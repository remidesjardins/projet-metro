from flask import Blueprint, request, jsonify
from datetime import datetime, date, timedelta
import logging
import json
import pandas as pd
import os

from services.service_registry import get_temporal_service, get_graph_service, get_gtfs_service
from utils.co2 import calculate_emissions_from_segments
from config import Config
from services.temporal_path import TemporalPath
from utils.data_manager import DataManager

logger = logging.getLogger(__name__)

temporal_bp = Blueprint('temporal', __name__, url_prefix='/temporal')

@temporal_bp.route('/path', methods=['POST'])
def get_temporal_path():
    """
    Calcule le chemin temporel optimal entre deux stations
    
    Body JSON:
    {
        "start_station": "Châtelet",
        "end_station": "Bastille", 
        "departure_time": "08:30",
        "date": "2024-01-15",  // optionnel
        "max_paths": 3,        // optionnel
        "max_wait_time": 1800,  // optionnel (30 min en secondes)
        "include_rer": true  // optionnel (true ou false)
    }
    """
    try:
        data = request.get_json()
        logger.info(f"[TEMPORAL_PATH] Requête reçue: {data}")
        
        if not data:
            logger.warning("[TEMPORAL_PATH] Données JSON manquantes")
            return jsonify({"error": "Données JSON requises"}), 400
        
        # Validation des paramètres requis
        required_fields = ['start_station', 'end_station', 'departure_time']
        for field in required_fields:
            if field not in data:
                logger.warning(f"[TEMPORAL_PATH] Champ requis manquant: {field}")
                return jsonify({"error": f"Champ requis manquant: {field}"}), 400
        
        # Parser les paramètres
        departure_time = parse_time_and_date(
            data['departure_time'], 
            data.get('date')
        )
        logger.info(f"[TEMPORAL_PATH] Paramètres: start={data['start_station']}, end={data['end_station']}, departure_time={departure_time}")
        
        max_paths = data.get('max_paths', Config.TEMPORAL_DEFAULT_MAX_PATHS)
        max_wait_time = data.get('max_wait_time', Config.TEMPORAL_DEFAULT_MAX_WAIT_TIME)
        include_rer = data.get('include_rer', True)
        
        # Obtenir les services
        temporal_service, graph_service, _ = get_services()
        
        # Log les chemins structurels trouvés
        structural_paths = graph_service.find_multiple_paths(
            data['start_station'], data['end_station'], Config.TEMPORAL_MAX_STRUCTURAL_PATHS
        )
        # Filtrer les chemins structurels si RER désactivé
        if not include_rer:
            rer_lines = {'A', 'B', 'C', 'D', 'E'}
            def path_has_rer(path):
                for seg in path:
                    if seg['line'] in rer_lines:
                        return True
                return False
            structural_paths = [p for p in structural_paths if not path_has_rer(p)]
        logger.info(f"[TEMPORAL_PATH] Nombre de chemins structurels trouvés: {len(structural_paths)}")
        if len(structural_paths) == 0:
            logger.warning(f"[TEMPORAL_PATH] Aucun chemin structurel trouvé entre {data['start_station']} et {data['end_station']}")
        
        # Calculer le chemin optimal
        path = temporal_service.find_optimal_temporal_path_from_structural(
            structural_paths,
            data['start_station'],
            data['end_station'],
            departure_time=departure_time,
            max_wait_time=max_wait_time
        )
        
        if not path:
            # Vérifier si c'est un problème de disponibilité du service
            service_info = temporal_service.check_service_availability(
                data['start_station'], departure_time
            )
            
            error_response = {
                "error": f"Aucun chemin trouvé entre {data['start_station']} et {data['end_station']} pour l'heure {data['departure_time']}",
                "service_info": {
                    "is_service_available": service_info.is_service_available,
                    "message": service_info.message,
                    "first_departure": service_info.first_departure.strftime("%H:%M") if service_info.first_departure else None,
                    "last_departure": service_info.last_departure.strftime("%H:%M") if service_info.last_departure else None,
                    "suggested_departure": service_info.suggested_departure.strftime("%H:%M") if service_info.suggested_departure else None
                }
            }
            
            logger.warning(f"[TEMPORAL_PATH] {error_response['error']} - {service_info.message}")
            return jsonify(error_response), 404
        
        # Convertir en format de réponse
        response = convert_temporal_path_to_dict(path)
        
        # Log détaillé du chemin optimal envoyé au frontend
        segments_info = [(s['from_station'], s['to_station'], s['line']) for s in response['segments']]
        logger.info(f"[TEMPORAL_PATH] Chemin optimal envoyé au frontend: {segments_info}")
        logger.info(f"[TEMPORAL_PATH] Durée totale: {response['total_duration']}s, Temps d'attente: {response['total_wait_time']}s")
        
        return jsonify(response)
        
    except ValueError as e:
        logger.error(f"[TEMPORAL_PATH] Erreur de valeur: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"[TEMPORAL_PATH] Erreur lors du calcul du chemin temporel: {e}")
        return jsonify({"error": "Erreur interne du serveur"}), 500

@temporal_bp.route('/path-arrival', methods=['POST'])
def get_temporal_path_with_arrival():
    """
    Calcule le chemin temporel optimal entre deux stations en partant de l'heure d'arrivée souhaitée
    
    Body JSON:
    {
        "start_station": "Châtelet",
        "end_station": "Bastille", 
        "arrival_time": "09:00",
        "date": "2024-01-15",  // optionnel
        "max_paths": 3,        // optionnel
        "max_wait_time": 1800  // optionnel (30 min en secondes)
    }
    """
    try:
        data = request.get_json()
        logger.info(f"[TEMPORAL_PATH_ARRIVAL] Requête reçue: {data}")
        
        if not data:
            logger.warning("[TEMPORAL_PATH_ARRIVAL] Données JSON manquantes")
            return jsonify({"error": "Données JSON requises"}), 400
        
        # Validation des paramètres requis
        required_fields = ['start_station', 'end_station', 'arrival_time']
        for field in required_fields:
            if field not in data:
                logger.warning(f"[TEMPORAL_PATH_ARRIVAL] Champ requis manquant: {field}")
                return jsonify({"error": f"Champ requis manquant: {field}"}), 400
        
        # Parser les paramètres
        arrival_time = parse_time_and_date(
            data['arrival_time'], 
            data.get('date')
        )
        logger.info(f"[TEMPORAL_PATH_ARRIVAL] Paramètres: start={data['start_station']}, end={data['end_station']}, arrival_time={arrival_time}")
        
        max_paths = data.get('max_paths', Config.TEMPORAL_DEFAULT_MAX_PATHS)
        max_wait_time = data.get('max_wait_time', Config.TEMPORAL_DEFAULT_MAX_WAIT_TIME)
        
        # Obtenir les services
        temporal_service, graph_service, _ = get_services()
        
        # Log les chemins structurels trouvés
        structural_paths = graph_service.find_multiple_paths(
            data['start_station'], data['end_station'], Config.TEMPORAL_MAX_STRUCTURAL_PATHS
        )
        logger.info(f"[TEMPORAL_PATH_ARRIVAL] Nombre de chemins structurels trouvés: {len(structural_paths)}")
        if len(structural_paths) == 0:
            logger.warning(f"[TEMPORAL_PATH_ARRIVAL] Aucun chemin structurel trouvé entre {data['start_station']} et {data['end_station']}")
        
        # Calculer le chemin optimal avec logique rétrograde
        path = temporal_service.find_optimal_temporal_path_with_arrival_time(
            start_station=data['start_station'],
            end_station=data['end_station'],
            arrival_time=arrival_time,
            max_structural_paths=Config.TEMPORAL_MAX_STRUCTURAL_PATHS,
            max_wait_time=max_wait_time
        )
        
        if not path:
            # Vérifier si c'est un problème de disponibilité du service
            service_info = temporal_service.check_service_availability(
                data['end_station'], arrival_time
            )
            
            error_response = {
                "error": f"Aucun chemin trouvé entre {data['start_station']} et {data['end_station']} pour arriver à {data['arrival_time']}",
                "service_info": {
                    "is_service_available": service_info.is_service_available,
                    "message": service_info.message,
                    "first_departure": service_info.first_departure.strftime("%H:%M") if service_info.first_departure else None,
                    "last_departure": service_info.last_departure.strftime("%H:%M") if service_info.last_departure else None,
                    "suggested_departure": service_info.suggested_departure.strftime("%H:%M") if service_info.suggested_departure else None
                }
            }
            
            logger.warning(f"[TEMPORAL_PATH_ARRIVAL] {error_response['error']} - {service_info.message}")
            return jsonify(error_response), 404
        
        # Convertir en format de réponse
        response = convert_temporal_path_to_dict(path)
        
        # Log détaillé du chemin optimal envoyé au frontend
        segments_info = [(s['from_station'], s['to_station'], s['line']) for s in response['segments']]
        logger.info(f"[TEMPORAL_PATH_ARRIVAL] Chemin optimal envoyé au frontend: {segments_info}")
        logger.info(f"[TEMPORAL_PATH_ARRIVAL] Départ: {path.departure_time.strftime('%H:%M')}, Arrivée: {path.arrival_time.strftime('%H:%M')}, Durée: {response['total_duration']}s")
        
        return jsonify(response)
        
    except ValueError as e:
        logger.error(f"[TEMPORAL_PATH_ARRIVAL] Erreur de valeur: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"[TEMPORAL_PATH_ARRIVAL] Erreur lors du calcul du chemin temporel avec arrivée: {e}")
        return jsonify({"error": "Erreur interne du serveur"}), 500

@temporal_bp.route('/alternatives', methods=['POST'])
def get_alternative_paths():
    """
    Calcule plusieurs chemins alternatifs entre deux stations
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Données JSON requises"}), 400
        required_fields = ['start_station', 'end_station', 'departure_time']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Champ requis manquant: {field}"}), 400
        departure_time = parse_time_and_date(
            data['departure_time'], 
            data.get('date')
        )
        max_paths = data.get('max_paths', Config.TEMPORAL_DEFAULT_MAX_PATHS)
        sort_by = data.get('sort_by', 'duration')  # 'duration' ou 'emissions'
        
        # Valider le paramètre de tri
        if sort_by not in ['duration', 'emissions']:
            sort_by = 'duration'
        
        temporal_service, _, _ = get_services()
        paths = temporal_service.find_alternative_paths(
            start_station=data['start_station'],
            end_station=data['end_station'],
            departure_time=departure_time,
            max_paths=max_paths,
            sort_by=sort_by
        )
        if not paths:
            return jsonify({
                "error": f"Aucun chemin trouvé entre {data['start_station']} et {data['end_station']} pour l'heure {data['departure_time']}"
            }), 404
        path_responses = [convert_temporal_path_to_dict(path) for path in paths]
        response = {
            "paths": path_responses,
            "request_info": {
                "start_station": data['start_station'],
                "end_station": data['end_station'],
                "departure_time": data['departure_time'],
                "date": data.get('date'),
                "paths_count": len(path_responses),
                "sort_by": sort_by
            }
        }
        return jsonify(response)
    except ValueError as e:
        print(f"[ALTERNATIVES][ValueError] {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        import traceback
        print(f"[ALTERNATIVES][Exception] {e}")
        print(traceback.format_exc())
        return jsonify({"error": "Erreur interne du serveur", "details": str(e)}), 500

@temporal_bp.route('/stations', methods=['GET'])
def get_stations():
    """Retourne la liste de toutes les stations disponibles"""
    try:
        include_rer = request.args.get('include_rer', 'true').lower() == 'true'
        _, graph_service, _ = get_services()
        stations = graph_service.get_all_stations()
        if not include_rer:
            # Filtrer les stations qui n'ont aucune ligne RER
            rer_lines = {'A', 'B', 'C', 'D', 'E'}
            filtered = []
            for name in stations:
                lines = graph_service.get_station_info(name).get('line', [])
                if isinstance(lines, str):
                    lines = [lines]
                if not any(l in rer_lines for l in lines):
                    filtered.append(name)
            stations = filtered
        return jsonify({"stations": sorted(stations)})
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des stations: {e}")
        return jsonify({"error": "Erreur interne du serveur"}), 500

@temporal_bp.route('/station/<station_name>/lines', methods=['GET'])
def get_station_lines(station_name):
    """Retourne les lignes qui desservent une station"""
    try:
        _, _, gtfs_service = get_services()
        lines = gtfs_service.get_station_lines(station_name)
        return jsonify({"station": station_name, "lines": lines})
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des lignes: {e}")
        return jsonify({"error": "Erreur interne du serveur"}), 500

@temporal_bp.route('/next-departure', methods=['GET'])
def get_next_departure():
    """Trouve le prochain départ d'une ligne depuis une station"""
    try:
        # Récupérer les paramètres de requête
        station = request.args.get('station')
        line = request.args.get('line')
        after_time = request.args.get('after_time')
        
        if not all([station, line, after_time]):
            return jsonify({
                "error": "Paramètres requis: station, line, after_time"
            }), 400
        
        # Parser l'heure
        after_datetime = parse_time_and_date(after_time)
        
        # Obtenir les services
        _, _, gtfs_service = get_services()
        
        # Trouver le prochain départ
        next_departure = gtfs_service.get_next_departure(station, line, after_datetime)
        
        if not next_departure:
            return jsonify({
                "station": station,
                "line": line,
                "after_time": after_time,
                "next_departure": None,
                "message": "Aucun départ trouvé"
            })
        
        return jsonify({
            "station": station,
            "line": line,
            "after_time": after_time,
            "next_departure": next_departure.strftime("%H:%M:%S"),
            "wait_time_minutes": int((next_departure - after_datetime).total_seconds() / 60)
        })
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Erreur lors de la recherche du prochain départ: {e}")
        return jsonify({"error": "Erreur interne du serveur"}), 500

def get_gtfs_valid_period(gtfs_dir="data/gtfs"):
    calendar_path = os.path.join(gtfs_dir, "calendar.txt")
    if not os.path.exists(calendar_path):
        return None, None
    df = pd.read_csv(calendar_path, dtype=str)
    min_date = df['start_date'].min()
    max_date = df['end_date'].max()
    min_date = pd.to_datetime(min_date, format="%Y%m%d").date()
    max_date = pd.to_datetime(max_date, format="%Y%m%d").date()
    return min_date, max_date

def parse_time_and_date(time_str: str, date_str: str = None) -> datetime:
    """Parse une heure et une date optionnelle, gère les heures après minuit (ex: 24:30, 01:15)"""
    try:
        hour, minute = map(int, time_str.split(':'))
        if not (0 <= minute <= 59):
            raise ValueError("Minutes invalides (0-59)")
        min_gtfs, max_gtfs = get_gtfs_valid_period()
        if min_gtfs is None or max_gtfs is None:
            min_gtfs = datetime(2024, 3, 1).date()
            max_gtfs = datetime(2024, 3, 31).date()
        if date_str:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        else:
            target_date = date.today()
        if target_date < min_gtfs:
            logger.warning(f"[TEMPORAL] Date {target_date} avant la période GTFS ({min_gtfs} - {max_gtfs}), utilisation de {min_gtfs}")
            target_date = min_gtfs
        elif target_date > max_gtfs:
            logger.warning(f"[TEMPORAL] Date {target_date} après la période GTFS ({min_gtfs} - {max_gtfs}), utilisation de {max_gtfs}")
            target_date = max_gtfs
        if hour >= 24:
            hour_adjusted = hour - 24
            target_date += timedelta(days=1)
            if target_date > max_gtfs:
                target_date = max_gtfs
            logger.info(f"[TEMPORAL] Heure après minuit détectée: {hour}:{minute:02d} -> {hour_adjusted}:{minute:02d} du {target_date}")
        else:
            hour_adjusted = hour
        if not (0 <= hour_adjusted <= 23):
            raise ValueError(f"Heure invalide après ajustement: {hour_adjusted}")
        result = datetime.combine(target_date, datetime.min.time()) + timedelta(hours=hour_adjusted, minutes=minute)
        logger.info(f"[TEMPORAL] Heure parsée: {time_str} -> {result}")
        return result
    except (ValueError, TypeError) as e:
        raise ValueError(f"Format d'heure invalide: {time_str}. Utilisez le format HH:MM (ex: 08:30, 24:30 pour 00:30 du lendemain)")

def convert_temporal_path_to_dict(path: TemporalPath) -> dict:
    """Convertit un TemporalPath en dictionnaire JSON avec regroupement par ligne"""
    # Créer les segments individuels d'abord
    raw_segments = []
    for segment in path.segments:
        raw_segments.append({
            "from_station": segment.from_station,
            "to_station": segment.to_station,
            "line": segment.line,
            "departure_time": segment.departure_time.strftime("%H:%M:%S"),
            "arrival_time": segment.arrival_time.strftime("%H:%M:%S"),
            "wait_time": segment.wait_time,
            "travel_time": segment.travel_time,
            "transfer_time": segment.transfer_time
        })
    
    # Regrouper les segments par ligne
    grouped_segments = group_segments_by_line(raw_segments)
    
    response = {
        "segments": grouped_segments,
        "total_duration": path.total_duration,
        "total_wait_time": path.total_wait_time,
        "departure_time": path.departure_time.strftime("%H:%M:%S"),
        "arrival_time": path.arrival_time.strftime("%H:%M:%S")
    }
    # Ajouter le chemin structurel si disponible
    if path.structural_path:
        response["structural_path"] = path.structural_path
    # Ajout du calcul CO2
    graph, positions, stations = DataManager.get_data()
    response["emissions"] = calculate_emissions_from_segments(grouped_segments, stations, positions)
    return response

def group_segments_by_line(segments: list) -> list:
    """Regroupe les segments consécutifs de la même ligne"""
    if not segments:
        return []
    
    grouped = []
    current_group = [segments[0]]
    current_line = segments[0]['line']
    
    for i in range(1, len(segments)):
        segment = segments[i]
        
        # Si même ligne et pas de transfert, regrouper
        if segment['line'] == current_line and segment['transfer_time'] == 0:
            current_group.append(segment)
        else:
            # Finaliser le groupe actuel
            if len(current_group) > 1:
                # Créer un segment regroupé
                grouped_segment = {
                    "from_station": current_group[0]['from_station'],
                    "to_station": current_group[-1]['to_station'],
                    "line": current_line,
                    "departure_time": current_group[0]['departure_time'],
                    "arrival_time": current_group[-1]['arrival_time'],
                    "wait_time": current_group[0]['wait_time'],
                    "travel_time": sum(s['travel_time'] for s in current_group),
                    "transfer_time": current_group[0]['transfer_time']
                }
                grouped.append(grouped_segment)
            else:
                # Garder le segment seul
                grouped.append(current_group[0])
            
            # Commencer un nouveau groupe
            current_group = [segment]
            current_line = segment['line']
    
    # Finaliser le dernier groupe
    if len(current_group) > 1:
        grouped_segment = {
            "from_station": current_group[0]['from_station'],
            "to_station": current_group[-1]['to_station'],
            "line": current_line,
            "departure_time": current_group[0]['departure_time'],
            "arrival_time": current_group[-1]['arrival_time'],
            "wait_time": current_group[0]['wait_time'],
            "travel_time": sum(s['travel_time'] for s in current_group),
            "transfer_time": current_group[0]['transfer_time']
        }
        grouped.append(grouped_segment)
    else:
        grouped.append(current_group[0])
    
    return grouped

@temporal_bp.route('/transfer-test', methods=['POST'])
def test_transfer():
    """
    Test de la logique de transfert entre lignes
    
    Body JSON:
    {
        "station": "Châtelet",
        "from_line": "1",
        "to_line": "14"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Données JSON requises'}), 400
        
        station = data.get('station')
        from_line = data.get('from_line')
        to_line = data.get('to_line')
        
        if not all([station, from_line, to_line]):
            return jsonify({'error': 'station, from_line et to_line requis'}), 400
        
        # Obtenir les services
        _, _, gtfs_service = get_services()
        
        # Calculer le temps de transfert
        transfer_time = gtfs_service.get_transfer_time_between_lines(station, from_line, to_line)
        
        # Obtenir les informations de transfert pour la station
        transfer_info = gtfs_service.transfer_service.get_station_transfer_info(station)
        
        response = {
            'station': station,
            'from_line': from_line,
            'to_line': to_line,
            'transfer_time_seconds': transfer_time,
            'transfer_time_minutes': round(transfer_time / 60, 1),
            'station_transfer_info': transfer_info,
            'is_same_line': from_line == to_line,
            'has_transfer': transfer_time > 0
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Erreur lors du test de transfert: {e}")
        return jsonify({'error': str(e)}), 500

@temporal_bp.route('/alternatives-arrival', methods=['POST'])
def get_alternative_paths_arrival():
    """
    Calcule plusieurs chemins alternatifs entre deux stations pour une heure d'arrivée souhaitée
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Données JSON requises"}), 400
        required_fields = ['start_station', 'end_station', 'arrival_time']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Champ requis manquant: {field}"}), 400
        arrival_time = parse_time_and_date(
            data['arrival_time'],
            data.get('date')
        )
        max_paths = data.get('max_paths', Config.TEMPORAL_DEFAULT_MAX_PATHS)
        sort_by = data.get('sort_by', 'duration')  # 'duration' ou 'emissions'
        
        # Valider le paramètre de tri
        if sort_by not in ['duration', 'emissions']:
            sort_by = 'duration'
        
        temporal_service, _, _ = get_services()
        paths = temporal_service.find_optimal_temporal_path_with_arrival_time_all(
            start_station=data['start_station'],
            end_station=data['end_station'],
            arrival_time=arrival_time,
            max_structural_paths=max_paths * 10,
            max_wait_time=data.get('max_wait_time', Config.TEMPORAL_DEFAULT_MAX_WAIT_TIME)
        )
        if not paths:
            return jsonify({
                "error": f"Aucun chemin trouvé entre {data['start_station']} et {data['end_station']} pour arriver à {data['arrival_time']}"
            }), 404
        
        # Trier selon le critère choisi
        if sort_by == 'emissions':
            # Calculer les émissions pour chaque chemin et trier
            paths_with_emissions = []
            for path in paths:
                emissions = temporal_service._calculate_path_emissions(path)
                paths_with_emissions.append((path, emissions))
            
            # Trier par émissions croissantes
            paths_with_emissions.sort(key=lambda x: (x[1], x[0].total_duration))
            paths = [path for path, _ in paths_with_emissions]
        
        # Limiter au nombre de chemins demandés
        paths = paths[:max_paths]
        path_responses = [convert_temporal_path_to_dict(path) for path in paths]
        response = {
            "paths": path_responses,
            "request_info": {
                "start_station": data['start_station'],
                "end_station": data['end_station'],
                "arrival_time": data['arrival_time'],
                "date": data.get('date'),
                "paths_count": len(path_responses),
                "sort_by": sort_by
            }
        }
        return jsonify(response)
    except ValueError as e:
        print(f"[ALTERNATIVES_ARRIVAL][ValueError] {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        import traceback
        print(f"[ALTERNATIVES_ARRIVAL][Exception] {e}")
        print(traceback.format_exc())
        return jsonify({"error": "Erreur interne du serveur", "details": str(e)}), 500

def get_services():
    """Retourne les singletons des services nécessaires"""
    return get_temporal_service(), get_graph_service(), get_gtfs_service()

 