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
        # Filtrer les chemins qui repassent par la station d'arrivée avant la fin
        filtered_structural_paths = []
        for path in structural_paths:
            stations = [seg['from_station'] for seg in path] + [path[-1]['to_station']]
            # Si la station d'arrivée apparaît ailleurs qu'à la fin, on rejette
            if stations.count(end_station) > 1 or (end_station in stations[:-1]):
                continue
            filtered_structural_paths.append(path)
        structural_paths = filtered_structural_paths
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
                # Même ligne
                if i == 0:
                    # Premier segment : partir au plus tôt après l'heure de départ demandée
                    next_departure = self._get_next_departure(from_station, line, current_time)
                else:
                    # Segment suivant sur la même ligne : vérifier si on peut continuer dans la même rame
                    # ou s'il faut attendre le prochain train
                    previous_arrival = segments[-1].arrival_time
                    
                    # Vérifier si on peut continuer dans la même rame
                    can_continue_same_train = self._can_continue_same_train(
                        from_station, to_station, line, previous_arrival
                    )
                    
                    if can_continue_same_train:
                        # On reste dans la même rame, pas d'attente
                        next_departure = previous_arrival
                    else:
                        # Il faut attendre le prochain train
                        next_departure = self._get_next_departure(from_station, line, previous_arrival)
            
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
                # Même ligne : vérifier s'il y a eu attente
                if next_departure > segments[-1].arrival_time:
                    wait_time = int((next_departure - segments[-1].arrival_time).total_seconds())
                else:
                    wait_time = 0  # Même rame, pas d'attente
            
            # Vérifier le temps d'attente maximum
            if wait_time > max_wait_time:
                return None
            
            # --- Calculer le temps réel GTFS entre from_station et to_station sur la ligne ---
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
        """
        # Augmenter le nombre de chemins structurels pour avoir plus d'alternatives
        structural_paths = self.graph_service.find_multiple_paths(
            start_station, end_station, max_paths * 10
        )
        logger.info(f"[ALTERNATIVES] {len(structural_paths)} chemins structurels générés pour {start_station} -> {end_station}")
        temporal_paths = []
        for path in structural_paths:
            temporal_path = self._evaluate_temporal_path(path, departure_time, max_wait_time)
            if temporal_path:
                temporal_paths.append(temporal_path)
        logger.info(f"[ALTERNATIVES] {len(temporal_paths)} chemins temporels valides générés pour {start_station} -> {end_station}")
        # Trier par durée et retourner les meilleurs
        temporal_paths.sort(key=lambda p: p.total_duration)
        return temporal_paths[:max_paths]

    def find_optimal_temporal_path_with_arrival_time(
        self, 
        start_station: str, 
        end_station: str, 
        arrival_time: datetime,
        max_structural_paths: int = 10,
        max_wait_time: int = 1800  # 30 minutes max d'attente
    ) -> Optional[TemporalPath]:
        """
        Trouve l'itinéraire optimal pour arriver à une heure donnée (logique rétrograde)
        
        Args:
            start_station: Station de départ
            end_station: Station d'arrivée
            arrival_time: Heure d'arrivée souhaitée
            max_structural_paths: Nombre maximum de chemins structurels à évaluer
            max_wait_time: Temps d'attente maximum autorisé
        
        Returns:
            Chemin temporel optimal ou None si impossible
        """
        logger.info(f"[ARRIVAL_PATH] Recherche d'itinéraire pour arriver à {end_station} à {arrival_time.strftime('%H:%M')}")
        
        # Vérifier la disponibilité du service
        service_info = self.check_service_availability(start_station, arrival_time)
        if not service_info.is_service_available:
            logger.warning(f"[ARRIVAL_PATH] Service non disponible: {service_info.message}")
            return None
        
        # Trouver les chemins structurels (même logique que l'algorithme normal)
        structural_paths = self.graph_service.find_multiple_paths(
            start_station, end_station, max_structural_paths
        )
        # Filtrer les chemins qui repassent par la station d'arrivée avant la fin
        filtered_structural_paths = []
        for path in structural_paths:
            stations = [seg['from_station'] for seg in path] + [path[-1]['to_station']]
            # Si la station d'arrivée apparaît ailleurs qu'à la fin, on rejette
            if stations.count(end_station) > 1 or (end_station in stations[:-1]):
                continue
            filtered_structural_paths.append(path)
        structural_paths = filtered_structural_paths
        
        if not structural_paths:
            logger.error(f"[ARRIVAL_PATH] Aucun chemin structurel trouvé entre {start_station} et {end_station}")
            return None
        
        logger.info(f"[PERF] Recherche chemins structurels: {len(structural_paths)} chemins trouvés")
        
        # Évaluer chaque chemin avec la nouvelle logique rétrograde
        temporal_paths = []
        
        for i, structural_path in enumerate(structural_paths):
            path_start_time = time.time()
            
            # NOUVELLE LOGIQUE : Construire le chemin en remontant depuis l'arrivée
            temporal_path = self._evaluate_temporal_path_reverse(
                structural_path, arrival_time, max_wait_time
            )
            
            if temporal_path is None:
                logger.warning(f"[ARRIVAL_PATH] Impossible de construire l'itinéraire rétrograde pour le chemin {i+1}")
                continue
            
            # Vérifier que l'arrivée est bien à l'heure demandée (ou légèrement avant)
            if temporal_path.arrival_time > arrival_time:
                logger.warning(f"[ARRIVAL_PATH] Arrivée trop tardive: {temporal_path.arrival_time.strftime('%H:%M:%S')} > {arrival_time.strftime('%H:%M:%S')}")
                continue
            
            temporal_paths.append(temporal_path)
            logger.info(f"[PERF] Chemin rétrograde {i+1} évalué en {time.time() - path_start_time:.3f}s")
        
        if not temporal_paths:
            logger.error(f"[ARRIVAL_PATH] Aucun itinéraire valide trouvé pour arriver à {end_station} à {arrival_time.strftime('%H:%M')}")
            return None
        
        # Calculer un score basé sur la ponctualité et la durée
        def calculate_arrival_score(path: TemporalPath) -> tuple:
            # On veut prioriser le départ le plus tardif, puis l'attente minimale, puis la durée
            # (on inverse l'heure de départ pour que le tri croissant donne le plus tardif)
            return (-int(path.departure_time.timestamp()), path.total_wait_time, path.total_duration)
        
        # Trier par score (départ le plus tardif, attente minimale, durée minimale)
        valid_paths = [p for p in temporal_paths if p.arrival_time <= arrival_time]
        if not valid_paths:
            return None
        valid_paths.sort(key=calculate_arrival_score)
        return valid_paths[0]

    def _evaluate_temporal_path_reverse(
        self, 
        structural_path: List[Dict], 
        target_arrival_time: datetime,
        max_wait_time: int
    ) -> Optional[TemporalPath]:
        """
        Évalue un chemin structurel en construisant le chemin temporel en remontant depuis l'arrivée
        """
        logger.info(f"[REVERSE_PATH] Construction du chemin rétrograde pour arriver à {target_arrival_time.strftime('%H:%M:%S')}")
        
        segments = []
        current_time = target_arrival_time
        previous_departure = None
        previous_arrival = None
        previous_transfer = 0
        
        # Remonter le chemin depuis la fin
        for i in range(len(structural_path) - 1, -1, -1):
            segment = structural_path[i]
            from_station = segment['from_station']
            to_station = segment['to_station']
            line = segment['line']
            
            transfer_time = 0
            if i < len(structural_path) - 1:
                next_line = structural_path[i + 1]['line']
                if line != next_line:
                    transfer_time = self.gtfs_service.get_transfer_time_between_lines(
                        to_station, line, next_line
                    )
            
            real_travel_time = self.gtfs_service.get_travel_time(from_station, to_station, line)
            if real_travel_time is None:
                real_travel_time = segment['time']
            
            # Heure d'arrivée à la station de départ
            arrival_at_from = current_time - timedelta(seconds=real_travel_time)
            if transfer_time > 0:
                arrival_at_from = arrival_at_from - timedelta(seconds=transfer_time)
            
            departure_info = self._find_last_departure_for_arrival(from_station, line, arrival_at_from)
            if departure_info is None:
                logger.error(f"[REVERSE_PATH] ❌ Aucun départ trouvé pour {from_station} (ligne {line})")
                return None
            departure_time, actual_arrival_time = departure_info
            
            # Correction : le segment suivant doit commencer à l'arrivée de ce segment (plus transfert)
            if previous_departure is not None:
                # Calculer l'attente réelle entre l'arrivée de ce segment et le départ du suivant
                expected_next_departure = actual_arrival_time
                if previous_transfer > 0:
                    expected_next_departure += timedelta(seconds=previous_transfer)
                wait_time = int((previous_departure - expected_next_departure).total_seconds())
                if wait_time < 0:
                    wait_time = 0
            else:
                wait_time = 0
            
            # Créer le segment temporel (dans l'ordre inverse)
            temporal_segment = TemporalSegment(
                from_station=from_station,
                to_station=to_station,
                line=line,
                departure_time=departure_time,
                arrival_time=actual_arrival_time,
                wait_time=wait_time,
                travel_time=int((actual_arrival_time - departure_time).total_seconds()),
                transfer_time=transfer_time
            )
            segments.append(temporal_segment)
            current_time = departure_time
            previous_departure = departure_time
            previous_arrival = actual_arrival_time
            previous_transfer = transfer_time
        
        segments.reverse()
        # Correction : recalculer les temps d'attente pour le sens chronologique
        for i in range(1, len(segments)):
            prev = segments[i-1]
            curr = segments[i]
            expected_departure = prev.arrival_time
            if curr.transfer_time > 0:
                expected_departure += timedelta(seconds=curr.transfer_time)
            wait_time = int((curr.departure_time - expected_departure).total_seconds())
            if wait_time < 0:
                wait_time = 0
            curr.wait_time = wait_time
        
        total_duration = int((segments[-1].arrival_time - segments[0].departure_time).total_seconds())
        total_wait_time = sum(seg.wait_time for seg in segments)
        
        temporal_path = TemporalPath(
            segments=segments,
            total_duration=total_duration,
            total_wait_time=total_wait_time,
            departure_time=segments[0].departure_time,
            arrival_time=segments[-1].arrival_time,
            structural_path=structural_path
        )
        logger.info(f"[REVERSE_PATH] ✓ Chemin rétrograde construit: Départ {temporal_path.departure_time.strftime('%H:%M:%S')}, Arrivée {temporal_path.arrival_time.strftime('%H:%M:%S')}, Durée {total_duration//60}min")
        return temporal_path

    def _find_last_departure_for_arrival(
        self, 
        station: str, 
        line: str, 
        target_arrival_time: datetime
    ) -> Optional[tuple[datetime, datetime]]:
        """
        Trouve le dernier départ d'une ligne qui permet d'arriver avant une heure donnée
        
        Args:
            station: Nom de la station
            line: Identifiant de la ligne
            target_arrival_time: Heure d'arrivée souhaitée
        
        Returns:
            Tuple (heure_départ, heure_arrivée_réelle) ou None
        """
        # Utiliser le service GTFS pour récupérer les horaires
        schedules = self.gtfs_service.get_station_schedules(station, line, target_arrival_time.date())
        
        if not schedules:
            return None
        
        # Obtenir les route_ids pour cette ligne
        route_ids = self.gtfs_service.route_name_to_ids.get(line, [])
        if not route_ids:
            return None
        
        # Obtenir les stop_ids pour cette station
        stop_ids = self.gtfs_service.stop_name_to_ids.get(station, [])
        if not stop_ids:
            return None
        
        last_valid_departure = None
        last_valid_arrival = None
        
        # Chercher dans les trips de cette ligne
        trips = self.gtfs_service.trips_df[self.gtfs_service.trips_df['route_id'].isin(route_ids)]['trip_id'].tolist()
        
        for trip_id in trips:
            stops = self.gtfs_service.stop_times_cache.get(trip_id, [])
            if not stops:
                continue
            
            # Trouver l'index de cette station dans le trip
            for i, stop in enumerate(stops):
                if stop['stop_id'] in stop_ids:
                    # Calculer l'heure de départ à cette station
                    dep_time = self.gtfs_service._parse_gtfs_time(stop['departure_time'], target_arrival_time.date())
                    
                    # Calculer l'heure d'arrivée réelle en trouvant la station suivante dans le trip
                    if i + 1 < len(stops):
                        next_stop = stops[i + 1]
                        arr_time = self.gtfs_service._parse_gtfs_time(next_stop['arrival_time'], target_arrival_time.date())
                        
                        # Si l'arrivée est avant ou égale à l'heure demandée, c'est un candidat
                        if arr_time <= target_arrival_time:
                            if last_valid_departure is None or dep_time > last_valid_departure:
                                last_valid_departure = dep_time
                                last_valid_arrival = arr_time
        
        if last_valid_departure is None:
            return None
        
        return (last_valid_departure, last_valid_arrival)

    def find_optimal_temporal_path_with_arrival_time_all(
        self, 
        start_station: str, 
        end_station: str, 
        arrival_time: datetime,
        max_structural_paths: int = 10,
        max_wait_time: int = 1800  # 30 minutes max d'attente
    ) -> List[TemporalPath]:
        """
        Retourne tous les chemins rétrogrades valides pour analyse et debug
        """
        logger.info(f"[ARRIVAL_PATH_ALL] Recherche de tous les itinéraires pour arriver à {end_station} à {arrival_time.strftime('%H:%M')}")
        
        service_info = self.check_service_availability(start_station, arrival_time)
        if not service_info.is_service_available:
            logger.warning(f"[ARRIVAL_PATH_ALL] Service non disponible: {service_info.message}")
            return []
        
        structural_paths = self.graph_service.find_multiple_paths(
            start_station, end_station, max_structural_paths
        )
        
        if not structural_paths:
            logger.error(f"[ARRIVAL_PATH_ALL] Aucun chemin structurel trouvé entre {start_station} et {end_station}")
            return []
        
        temporal_paths = []
        
        for i, structural_path in enumerate(structural_paths):
            # Utiliser la nouvelle logique rétrograde
            temporal_path = self._evaluate_temporal_path_reverse(
                structural_path, arrival_time, max_wait_time
            )
            
            if temporal_path is None:
                continue
            
            if temporal_path.arrival_time > arrival_time:
                continue
            
            temporal_paths.append(temporal_path)
        
        def calculate_arrival_score(path: TemporalPath) -> tuple:
            return (-int(path.departure_time.timestamp()), path.total_wait_time, path.total_duration)

        valid_paths = [p for p in temporal_paths if p.arrival_time <= arrival_time]
        valid_paths.sort(key=calculate_arrival_score)
        return valid_paths 

    def _can_continue_same_train(
        self, 
        from_station: str, 
        to_station: str, 
        line: str, 
        previous_arrival_time: datetime
    ) -> bool:
        """
        Vérifie si on peut continuer dans la même rame après un arrêt
        
        Args:
            from_station: Station de départ
            to_station: Station d'arrivée
            line: Ligne de métro
            previous_arrival_time: Heure d'arrivée du segment précédent
        
        Returns:
            True si on peut continuer dans la même rame, False sinon
        """
        # Vérifier si il existe un trip qui passe par les deux stations consécutivement
        # avec un temps de trajet réaliste (pas de changement de train)
        
        route_ids = self.gtfs_service.route_name_to_ids.get(line, [])
        if not route_ids:
            return False
            
        trips = self.gtfs_service.trips_df[self.gtfs_service.trips_df['route_id'].isin(route_ids)]['trip_id'].tolist()
        stop_ids_a = self.gtfs_service.stop_name_to_ids.get(from_station, [])
        stop_ids_b = self.gtfs_service.stop_name_to_ids.get(to_station, [])
        
        # Chercher un trip qui passe par les deux stations dans l'ordre
        for trip_id in trips[:10]:  # Limiter pour les performances
            stops = self.gtfs_service.stop_times_cache.get(trip_id, [])
            if not stops:
                continue
                
            indices = {s['stop_id']: i for i, s in enumerate(stops)}
            
            for id_a in stop_ids_a:
                for id_b in stop_ids_b:
                    if id_a in indices and id_b in indices and indices[id_a] < indices[id_b]:
                        # Vérifier si ce trip peut être utilisé après l'arrivée précédente
                        stop_a = stops[indices[id_a]]
                        stop_b = stops[indices[id_b]]
                        
                        dep_time = self.gtfs_service._parse_gtfs_time(stop_a['departure_time'], previous_arrival_time.date())
                        arr_time = self.gtfs_service._parse_gtfs_time(stop_b['arrival_time'], previous_arrival_time.date())
                        
                        # Le départ doit être proche de l'arrivée précédente (même rame)
                        # Tolérance de 2 minutes pour les arrêts en station
                        time_diff = abs((dep_time - previous_arrival_time).total_seconds())
                        if time_diff <= 120:  # 2 minutes de tolérance
                            return True
        
        return False 

    def find_optimal_temporal_path_from_structural(
        self,
        structural_paths,
        start_station,
        end_station,
        departure_time,
        max_wait_time=1800
    ):
        """
        Évalue une liste de chemins structurels déjà filtrés (ex: sans RER) et retourne le meilleur chemin temporel.
        """
        if not structural_paths:
            return None
        temporal_paths = []
        for path in structural_paths:
            temporal_path = self._evaluate_temporal_path(path, departure_time, max_wait_time)
            if temporal_path:
                temporal_paths.append(temporal_path)
        if not temporal_paths:
            return None
        # Trier par durée totale (ou score pondéré si besoin)
        temporal_paths.sort(key=lambda p: p.total_duration)
        return temporal_paths[0] 