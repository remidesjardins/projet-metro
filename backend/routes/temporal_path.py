"""
MetroCity - Mastercamp 2025
Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
Fichier: temporal_path.py
Description: Routes Flask pour les calculs de chemins temporels (version alternative)
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, date, timedelta
import logging

from services.temporal_path import TemporalPathService, TemporalPath, TemporalSegment
from services.graph_service import GraphService
from services.gtfs_temporal import GTFSemporalService
from utils.parser import load_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/temporal", tags=["temporal"])

class TemporalPathRequest(BaseModel):
    """Modèle de requête pour un chemin temporel"""
    start_station: str
    end_station: str
    departure_time: str  # Format "HH:MM"
    date: Optional[str] = None  # Format "YYYY-MM-DD"
    max_paths: Optional[int] = 3
    max_wait_time: Optional[int] = 1800  # 30 minutes en secondes

class TemporalSegmentResponse(BaseModel):
    """Modèle de réponse pour un segment temporel"""
    from_station: str
    to_station: str
    line: str
    departure_time: str
    arrival_time: str
    wait_time: int
    travel_time: int
    transfer_time: int

class TemporalPathResponse(BaseModel):
    """Modèle de réponse pour un chemin temporel"""
    segments: List[TemporalSegmentResponse]
    total_duration: int
    total_wait_time: int
    departure_time: str
    arrival_time: str

class AlternativePathsResponse(BaseModel):
    """Modèle de réponse pour plusieurs chemins alternatifs"""
    paths: List[TemporalPathResponse]
    request_info: dict

# Initialisation des services (à faire une seule fois)
_temporal_service = None
_graph_service = None
_gtfs_service = None

def get_services():
    """Initialise et retourne les services nécessaires"""
    global _temporal_service, _graph_service, _gtfs_service
    
    if _temporal_service is None:
        # Charger les données
        graph, positions, stations = load_data()
        
        # Initialiser les services
        _graph_service = GraphService(graph, stations)
        _gtfs_service = GTFSemporalService("data/gtfs")
        _temporal_service = TemporalPathService(_graph_service, _gtfs_service)
    
    return _temporal_service, _graph_service, _gtfs_service

@router.post("/path", response_model=TemporalPathResponse)
async def get_temporal_path(request: TemporalPathRequest):
    """
    Calcule le chemin temporel optimal entre deux stations
    
    Args:
        request: Paramètres de la requête
        
    Returns:
        Le chemin temporel optimal avec horaires précis
    """
    try:
        # Valider et parser les paramètres
        departure_time = parse_time_and_date(request.departure_time, request.date)
        
        # Obtenir les services
        temporal_service, _, _ = get_services()
        
        # Calculer le chemin optimal
        path = temporal_service.find_optimal_temporal_path(
            start_station=request.start_station,
            end_station=request.end_station,
            departure_time=departure_time,
            max_structural_paths=request.max_paths * 3,
            max_wait_time=request.max_wait_time
        )
        
        if not path:
            raise HTTPException(
                status_code=404,
                detail=f"Aucun chemin trouvé entre {request.start_station} et {request.end_station} pour l'heure {request.departure_time}"
            )
        
        # Convertir en format de réponse
        return convert_temporal_path_to_response(path)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur lors du calcul du chemin temporel: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@router.post("/alternatives", response_model=AlternativePathsResponse)
async def get_alternative_paths(request: TemporalPathRequest):
    """
    Calcule plusieurs chemins alternatifs entre deux stations
    
    Args:
        request: Paramètres de la requête
        
    Returns:
        Liste des chemins alternatifs triés par durée
    """
    try:
        # Valider et parser les paramètres
        departure_time = parse_time_and_date(request.departure_time, request.date)
        
        # Obtenir les services
        temporal_service, _, _ = get_services()
        
        # Calculer les chemins alternatifs
        paths = temporal_service.find_alternative_paths(
            start_station=request.start_station,
            end_station=request.end_station,
            departure_time=departure_time,
            max_paths=request.max_paths
        )
        
        if not paths:
            raise HTTPException(
                status_code=404,
                detail=f"Aucun chemin trouvé entre {request.start_station} et {request.end_station} pour l'heure {request.departure_time}"
            )
        
        # Convertir en format de réponse
        path_responses = [convert_temporal_path_to_response(path) for path in paths]
        
        return AlternativePathsResponse(
            paths=path_responses,
            request_info={
                "start_station": request.start_station,
                "end_station": request.end_station,
                "departure_time": request.departure_time,
                "date": request.date,
                "paths_count": len(path_responses)
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur lors du calcul des chemins alternatifs: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@router.get("/stations")
async def get_stations():
    """Retourne la liste de toutes les stations disponibles"""
    try:
        _, graph_service, _ = get_services()
        stations = graph_service.get_all_stations()
        return {"stations": sorted(stations)}
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des stations: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@router.get("/station/{station_name}/lines")
async def get_station_lines(station_name: str):
    """Retourne les lignes qui desservent une station"""
    try:
        _, _, gtfs_service = get_services()
        lines = gtfs_service.get_station_lines(station_name)
        return {"station": station_name, "lines": lines}
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des lignes: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

@router.get("/next-departure")
async def get_next_departure(
    station: str = Query(..., description="Nom de la station"),
    line: str = Query(..., description="Nom de la ligne"),
    after_time: str = Query(..., description="Heure après laquelle chercher (HH:MM)")
):
    """Trouve le prochain départ d'une ligne depuis une station"""
    try:
        # Parser l'heure
        after_datetime = parse_time_and_date(after_time)
        
        # Obtenir les services
        _, _, gtfs_service = get_services()
        
        # Trouver le prochain départ
        next_departure = gtfs_service.get_next_departure(station, line, after_datetime)
        
        if not next_departure:
            return {
                "station": station,
                "line": line,
                "after_time": after_time,
                "next_departure": None,
                "message": "Aucun départ trouvé"
            }
        
        return {
            "station": station,
            "line": line,
            "after_time": after_time,
            "next_departure": next_departure.strftime("%H:%M:%S"),
            "wait_time_minutes": int((next_departure - after_datetime).total_seconds() / 60)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erreur lors de la recherche du prochain départ: {e}")
        raise HTTPException(status_code=500, detail="Erreur interne du serveur")

def parse_time_and_date(time_str: str, date_str: Optional[str] = None) -> datetime:
    """Parse une heure et une date optionnelle"""
    try:
        # Parser l'heure
        hour, minute = map(int, time_str.split(':'))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("Heure invalide")
        
        # Utiliser la date fournie ou aujourd'hui
        if date_str:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            target_date = date.today()
        
        return datetime.combine(target_date, datetime.min.time()) + timedelta(hours=hour, minutes=minute)
        
    except (ValueError, TypeError) as e:
        raise ValueError(f"Format d'heure invalide: {time_str}. Utilisez le format HH:MM")

def convert_temporal_path_to_response(path: TemporalPath) -> TemporalPathResponse:
    """Convertit un TemporalPath en TemporalPathResponse"""
    segments = []
    for segment in path.segments:
        segments.append(TemporalSegmentResponse(
            from_station=segment.from_station,
            to_station=segment.to_station,
            line=segment.line,
            departure_time=segment.departure_time.strftime("%H:%M:%S"),
            arrival_time=segment.arrival_time.strftime("%H:%M:%S"),
            wait_time=segment.wait_time,
            travel_time=segment.travel_time,
            transfer_time=segment.transfer_time
        ))
    
    return TemporalPathResponse(
        segments=segments,
        total_duration=path.total_duration,
        total_wait_time=path.total_wait_time,
        departure_time=path.departure_time.strftime("%H:%M:%S"),
        arrival_time=path.arrival_time.strftime("%H:%M:%S")
    ) 