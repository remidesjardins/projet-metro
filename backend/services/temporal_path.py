import heapq
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging
import time

logger = logging.getLogger(__name__)

@dataclass
class TemporalSegment:
    """Segment d'un chemin temporel avec horaires précis"""
    from_station: str
    to_station: str
    line: str
    departure_time: datetime
    arrival_time: datetime
    wait_time: int  # secondes
    travel_time: int  # secondes
    transfer_time: int = 0  # secondes de correspondance

@dataclass
class TemporalPath:
    """Chemin temporel complet avec horaires"""
    segments: List[TemporalSegment]
    total_duration: int  # secondes
    total_wait_time: int  # secondes
    departure_time: datetime
    arrival_time: datetime
    structural_path: List[Dict] = None  # Chemin structurel original
    
    def __post_init__(self):
        if not self.segments:
            return
        self.departure_time = self.segments[0].departure_time
        self.arrival_time = self.segments[-1].arrival_time

@dataclass
class ServiceHours:
    """Informations sur les heures de service du métro"""
    first_departure: Optional[datetime]
    last_departure: Optional[datetime]
    is_service_available: bool
    suggested_departure: Optional[datetime] = None
    message: str = ""

class TemporalPathService:
    """Service pour calculer les chemins temporels optimaux"""
    
    def __init__(self, graph_service, gtfs_service):
        self.graph_service = graph_service
        self.gtfs_service = gtfs_service
        self.schedule_cache = {}
    
    def check_service_availability(
        self,
        start_station: str,
        departure_time: datetime
    ) -> ServiceHours:
        """
        Vérifie si le service métro est disponible à l'heure demandée
        et propose des alternatives si nécessaire
        """
        # Obtenir les lignes disponibles à la station de départ
        lines = self.gtfs_service.get_station_lines(start_station)
        if not lines:
            return ServiceHours(
                first_departure=None,
                last_departure=None,
                is_service_available=False,
                message=f"Aucune ligne de métro trouvée à la station {start_station}"
            )
        
        # Vérifier les horaires pour chaque ligne
        earliest_first = None
        latest_last = None
        
        for line in lines:
            schedules = self.gtfs_service.get_station_schedules(
                start_station, line, departure_time.date()
            )
            
            if schedules:
                first_departure = schedules[0]['departure_time']
                last_departure = schedules[-1]['departure_time']
                
                if earliest_first is None or first_departure < earliest_first:
                    earliest_first = first_departure
                if latest_last is None or last_departure > latest_last:
                    latest_last = last_departure
        
        if earliest_first is None:
            return ServiceHours(
                first_departure=None,
                last_departure=None,
                is_service_available=False,
                message=f"Aucun horaire trouvé pour la station {start_station}"
            )
        
        # Vérifier si l'heure demandée est dans les heures de service
        is_available = earliest_first <= departure_time <= latest_last
        
        # Proposer une alternative si nécessaire
        suggested_departure = None
        message = ""
        
        if not is_available:
            if departure_time < earliest_first:
                # Trop tôt : proposer le premier train
                suggested_departure = earliest_first
                message = f"Le métro ne circule pas encore à {departure_time.strftime('%H:%M')}. Premier train à {earliest_first.strftime('%H:%M')}."
            else:
                # Trop tard : proposer le premier train du lendemain
                next_day_schedules = self.gtfs_service.get_station_schedules(
                    start_station, lines[0], departure_time.date() + timedelta(days=1)
                )
                if next_day_schedules:
                    suggested_departure = next_day_schedules[0]['departure_time']
                    message = f"Le métro ne circule plus à {departure_time.strftime('%H:%M')}. Dernier train à {latest_last.strftime('%H:%M')}, premier train du lendemain à {suggested_departure.strftime('%H:%M')}."
                else:
                    message = f"Le métro ne circule plus à {departure_time.strftime('%H:%M')}. Dernier train à {latest_last.strftime('%H:%M')}."
        
        return ServiceHours(
            first_departure=earliest_first,
            last_departure=latest_last,
            is_service_available=is_available,
            suggested_departure=suggested_departure,
            message=message
        )
    
    def find_optimal_temporal_path(
        self, 
        start_station: str, 
        end_station: str, 
        departure_time: datetime,
        max_structural_paths: int = 10,
        max_wait_time: int = 1800  # 30 minutes max d'attente
    ) -> Optional[TemporalPath]:
        """
        Trouve le chemin temporel optimal en évaluant plusieurs chemins structurels
        
        Args:
            start_station: Station de départ
            end_station: Station d'arrivée
            departure_time: Heure de départ souhaitée
            max_structural_paths: Nombre max de chemins structurels à tester
            max_wait_time: Temps d'attente maximum autorisé (secondes)
        
        Returns:
            Le chemin temporel optimal ou None si impossible
        """
        start_time = time.time()
        
        # 1. Vérifier la disponibilité du service
        service_check_start = time.time()
        service_info = self.check_service_availability(start_station, departure_time)
        service_check_time = time.time() - service_check_start
        logger.info(f"[PERF] Vérification service: {service_check_time:.3f}s - {service_info.message}")
        
        # Si pas de service disponible, essayer avec l'heure suggérée
        effective_departure_time = departure_time
        if not service_info.is_service_available and service_info.suggested_departure:
            effective_departure_time = service_info.suggested_departure
            logger.info(f"[TEMPORAL] Utilisation de l'heure suggérée: {effective_departure_time.strftime('%H:%M')}")
        
        # 2. Trouver plusieurs chemins structurels
        structural_start = time.time()
        structural_paths = self.graph_service.find_multiple_paths(
            start_station, end_station, max_structural_paths
        )
        structural_time = time.time() - structural_start
        logger.info(f"[PERF] Recherche chemins structurels: {structural_time:.3f}s - {len(structural_paths)} chemins trouvés")
        
        if not structural_paths:
            return None
        
        # 3. Évaluer chaque chemin temporellement
        temporal_eval_start = time.time()
        temporal_paths = []
        cache_hits = 0
        cache_misses = 0
        
        for i, path in enumerate(structural_paths):
            segment_start = time.time()
            temporal_path = self._evaluate_temporal_path(
                path, effective_departure_time, max_wait_time
            )
            segment_time = time.time() - segment_start
            
            if temporal_path:
                # Ajuster le departure_time original si on a utilisé une heure suggérée
                if effective_departure_time != departure_time:
                    temporal_path.departure_time = departure_time
                    temporal_path.total_duration = int((temporal_path.arrival_time - departure_time).total_seconds())
                temporal_paths.append(temporal_path)
                logger.info(f"[PERF] Chemin {i+1} évalué en {segment_time:.3f}s")
            else:
                logger.info(f"[PERF] Chemin {i+1} impossible en {segment_time:.3f}s")
        
        temporal_eval_time = time.time() - temporal_eval_start
        logger.info(f"[PERF] Évaluation temporelle totale: {temporal_eval_time:.3f}s - {len(temporal_paths)} chemins valides")
        
        # 4. Retourner le plus rapide en tenant compte des transferts
        if not temporal_paths:
            return None
        
        # Calculer un score pondéré qui pénalise les changements de ligne
        def calculate_weighted_score(path: TemporalPath) -> int:
            # Durée de base
            base_duration = path.total_duration
            
            # Calculer la pénalité basée sur les temps de correspondance réels
            total_transfer_penalty = 0
            for segment in path.segments:
                if segment.transfer_time > 0:  # Si c'est un changement de ligne
                    # Pénalité = temps de marche + temps d'attente (ce qui est affiché à l'utilisateur)
                    transfer_penalty = segment.transfer_time + segment.wait_time
                    total_transfer_penalty += transfer_penalty
            
            # Pénalité pour le temps d'attente total (encourage les départs directs)
            wait_penalty = path.total_wait_time * 0.5  # Pénalité de 50% du temps d'attente
            
            return base_duration + total_transfer_penalty + int(wait_penalty)
        
        # Trier par score pondéré
        temporal_paths.sort(key=calculate_weighted_score)
        
        total_time = time.time() - start_time
        logger.info(f"[PERF] Recherche temporelle complète: {total_time:.3f}s (service: {service_check_time:.3f}s, structurel: {structural_time:.3f}s, temporel: {temporal_eval_time:.3f}s)")
        
        return temporal_paths[0]
    
    def _evaluate_temporal_path(
        self, 
        structural_path: List[Dict], 
        departure_time: datetime,
        max_wait_time: int
    ) -> Optional[TemporalPath]:
        """
        Évalue un chemin structurel avec les horaires réels (LOGIQUE AMÉLIORÉE)
        
        Args:
            structural_path: Liste des segments du chemin structurel
            departure_time: Heure de départ
            max_wait_time: Temps d'attente maximum autorisé
        
        Returns:
            Chemin temporel ou None si impossible
        """
        segments = []
        current_time = departure_time
        
        for i, segment in enumerate(structural_path):
            from_station = segment['from_station']
            to_station = segment['to_station']
            line = segment['line']
            # travel_time = segment['time']  # On va remplacer par le temps réel GTFS
            
            # Déterminer si changement de ligne
            is_line_change = False
            transfer_time = 0
            
            if i > 0:
                previous_line = segments[-1].line
                if line != previous_line:
                    is_line_change = True
                    # Calculer le temps de transfert entre lignes dans la même station
                    transfer_time = self.gtfs_service.get_transfer_time_between_lines(
                        from_station, previous_line, line
                    )
            
            # Trouver le prochain départ
            if is_line_change:
                # Heure d'arrivée après transfert (déplacement entre quais)
                arrival_after_transfer = segments[-1].arrival_time + timedelta(seconds=transfer_time)
                next_departure = self._get_next_departure(from_station, line, arrival_after_transfer)
            else:
                # Même ligne ou première ligne
                if i == 0:
                    # Premier segment : partir au plus tôt après l'heure de départ demandée
                    next_departure = self._get_next_departure(from_station, line, current_time)
                else:
                    # Segment suivant sur la même ligne : continuer directement
                    # Pas de temps d'attente, on reste dans la même rame
                    next_departure = segments[-1].arrival_time
            
            if not next_departure:
                return None  # Pas de départ possible
            
            # Calculer le temps d'attente
            if i == 0:
                # Premier segment : temps d'attente entre l'heure demandée et le premier départ
                wait_time = int((next_departure - current_time).total_seconds())
                if wait_time < 0:
                    wait_time = 0  # Pas d'attente négative
            elif is_line_change:
                # Changement de ligne : temps d'attente après le transfert
                arrival_after_transfer = segments[-1].arrival_time + timedelta(seconds=transfer_time)
                wait_time = int((next_departure - arrival_after_transfer).total_seconds())
            else:
                # Même ligne : pas de temps d'attente, on reste dans la rame
                wait_time = 0
            
            # Vérifier le temps d'attente maximum
            if wait_time > max_wait_time:
                return None
            
            # --- NOUVEAU : Calculer le temps réel GTFS entre from_station et to_station sur la ligne ---
            real_travel_time = None
            dep_a, arr_b = None, None
            
            # OPTIMISATION : Utiliser le cache des temps de trajet d'abord
            cached_travel_time = self.gtfs_service.get_travel_time(from_station, to_station, line)
            if cached_travel_time is not None:
                real_travel_time = cached_travel_time
                # Calculer les heures de départ et d'arrivée basées sur le temps de trajet
                arrival_time = next_departure + timedelta(seconds=real_travel_time)
            else:
                # Fallback : utiliser la méthode GTFS originale (plus lente)
                route_ids = self.gtfs_service.route_name_to_ids.get(line, [])
                trips = self.gtfs_service.trips_df[self.gtfs_service.trips_df['route_id'].isin(route_ids)]['trip_id'].tolist()
                stop_ids_a = self.gtfs_service.stop_name_to_ids.get(from_station, [])
                stop_ids_b = self.gtfs_service.stop_name_to_ids.get(to_station, [])
                best_dep = None
                best_arr = None
                
                # OPTIMISATION : Limiter le nombre de trips testés
                for trip_id in trips[:5]:  # Tester seulement les 5 premiers trips
                    stops = self.gtfs_service.stop_times_cache.get(trip_id, [])
                    indices = {s['stop_id']: i for i, s in enumerate(stops)}
                    for id_a in stop_ids_a:
                        for id_b in stop_ids_b:
                            if id_a in indices and id_b in indices and indices[id_a] < indices[id_b]:
                                stop_a = stops[indices[id_a]]
                                stop_b = stops[indices[id_b]]
                                dep_time = self.gtfs_service._parse_gtfs_time(stop_a['departure_time'], next_departure.date())
                                arr_time = self.gtfs_service._parse_gtfs_time(stop_b['arrival_time'], next_departure.date())
                                # On veut le premier trip qui part après next_departure
                                if dep_time >= next_departure:
                                    if best_dep is None or dep_time < best_dep:
                                        best_dep = dep_time
                                        best_arr = arr_time
                
                if best_dep and best_arr:
                    real_travel_time = int((best_arr - best_dep).total_seconds())
                    # On ajuste next_departure si besoin (pour coller au vrai départ)
                    next_departure = best_dep
                    arrival_time = best_arr
                else:
                    # fallback : on garde la logique précédente
                    real_travel_time = segment['time']
                    arrival_time = next_departure + timedelta(seconds=real_travel_time)
            # --- FIN NOUVEAU ---
            
            # Créer le segment temporel
            temporal_segment = TemporalSegment(
                from_station=from_station,
                to_station=to_station,
                line=line,
                departure_time=next_departure,
                arrival_time=arrival_time,
                wait_time=wait_time,
                travel_time=real_travel_time,
                transfer_time=transfer_time
            )
            
            segments.append(temporal_segment)
            current_time = arrival_time
        
        if not segments:
            return None
        
        # Calculer les totaux
        total_duration = int((segments[-1].arrival_time - departure_time).total_seconds())
        total_wait_time = sum(seg.wait_time for seg in segments)
        
        return TemporalPath(
            segments=segments,
            total_duration=total_duration,
            total_wait_time=total_wait_time,
            departure_time=departure_time,
            arrival_time=segments[-1].arrival_time,
            structural_path=structural_path
        )
    
    def _get_next_departure(
        self, 
        station: str, 
        line: str, 
        after_time: datetime
    ) -> Optional[datetime]:
        """
        Trouve le prochain départ d'une ligne depuis une station
        
        Args:
            station: Nom de la station
            line: Identifiant de la ligne
            after_time: Heure après laquelle chercher
        
        Returns:
            Heure du prochain départ ou None
        """
        # Utiliser le service GTFS pour récupérer les horaires
        schedules = self.gtfs_service.get_station_schedules(station, line, after_time.date())
        
        if not schedules:
            return None
        
        # Chercher le prochain départ
        for schedule in schedules:
            departure_time = schedule['departure_time']
            if departure_time > after_time:
                return departure_time
        
        return None
    
    def find_alternative_paths(
        self, 
        start_station: str, 
        end_station: str, 
        departure_time: datetime,
        max_paths: int = 3,
        max_wait_time: int = 1800  # 30 minutes max d'attente
    ) -> List[TemporalPath]:
        """
        Trouve plusieurs itinéraires alternatifs
        
        Args:
            start_station: Station de départ
            end_station: Station d'arrivée
            departure_time: Heure de départ
            max_paths: Nombre maximum d'itinéraires à retourner
            max_wait_time: Temps d'attente maximum autorisé (secondes)
        
        Returns:
            Liste des itinéraires alternatifs triés par durée
        """
        # Augmenter le nombre de chemins structurels pour avoir plus d'alternatives
        structural_paths = self.graph_service.find_multiple_paths(
            start_station, end_station, max_paths * 3
        )
        
        temporal_paths = []
        for path in structural_paths:
            temporal_path = self._evaluate_temporal_path(path, departure_time, max_wait_time)
            if temporal_path:
                temporal_paths.append(temporal_path)
        
        # Trier par durée et retourner les meilleurs
        temporal_paths.sort(key=lambda p: p.total_duration)
        return temporal_paths[:max_paths] 