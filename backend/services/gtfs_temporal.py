import os
import pandas as pd
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import pickle
import time
from .transfer_service import TransferService

logger = logging.getLogger(__name__)

class GTFSemporalService:
    """Service GTFS pour les fonctionnalités temporelles avec cache intelligent"""
    
    def __init__(self, gtfs_dir: str):
        self.gtfs_dir = gtfs_dir
        self.cache_dir = Path(gtfs_dir).parent / 'cache' / 'temporal'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache des horaires par station/ligne/date
        self.schedule_cache = {}
        self.transfer_cache = {}
        
        # Cache global des stop_times (NOUVEAU)
        self.stop_times_cache = {}
        self.stop_times_loaded = False
        
        # NOUVEAU : Cache des temps de trajet réels entre stations
        self.travel_time_cache = {}
        self.travel_time_cache_loaded = False
        
        # Service de transfert (NOUVEAU)
        self.transfer_service = TransferService(gtfs_dir)
        
        # Charger les données GTFS temporelles
        self._load_temporal_data()
    
    def _load_temporal_data(self):
        """Charge les données GTFS nécessaires pour les calculs temporels"""
        start_time = time.time()
        logger.info("Chargement des données GTFS temporelles...")
        
        # Charger les routes de métro
        routes_start = time.time()
        routes_df = pd.read_csv(
            os.path.join(self.gtfs_dir, 'routes.txt'),
            usecols=['route_id', 'route_short_name', 'route_type'],
            dtype={'route_id': 'string', 'route_short_name': 'string', 'route_type': 'int8'}
        )
        
        # Filtrer pour le métro parisien
        metro_routes = routes_df[
            (routes_df['route_type'] == 1) & 
            (routes_df['route_short_name'].isin([str(i) for i in range(1, 15)] + ['3B', '7B']))
        ]
        
        self.route_id_to_name = metro_routes.set_index('route_id')['route_short_name'].to_dict()
        self.route_name_to_id = metro_routes.set_index('route_short_name')['route_id'].to_dict()
        
        # CORRECTION: Créer un mapping inverse pour trouver tous les route_ids d'une ligne
        self.route_name_to_ids = {}
        for route_id, route_name in self.route_id_to_name.items():
            if route_name not in self.route_name_to_ids:
                self.route_name_to_ids[route_name] = []
            self.route_name_to_ids[route_name].append(route_id)
        
        routes_time = time.time() - routes_start
        logger.info(f"Routes chargées en {routes_time:.3f}s")
        
        # Charger les trips de métro
        trips_start = time.time()
        metro_route_ids = set(metro_routes['route_id'])
        trips_df = pd.read_csv(
            os.path.join(self.gtfs_dir, 'trips.txt'),
            usecols=['trip_id', 'route_id'],
            dtype={'trip_id': 'string', 'route_id': 'string'}
        )
        
        self.trips_df = trips_df[trips_df['route_id'].isin(metro_route_ids)]
        self.trip_to_route = self.trips_df.set_index('trip_id')['route_id'].to_dict()
        trips_time = time.time() - trips_start
        logger.info(f"Trips chargés en {trips_time:.3f}s")
        
        # Charger les stops
        stops_start = time.time()
        self.stops_df = pd.read_csv(
            os.path.join(self.gtfs_dir, 'stops.txt'),
            usecols=['stop_id', 'stop_name'],
            dtype={'stop_id': 'string', 'stop_name': 'string'}
        )
        
        # Créer les mappings station
        self.stop_id_to_name = self.stops_df.set_index('stop_id')['stop_name'].to_dict()
        self.stop_name_to_ids = self.stops_df.groupby('stop_name')['stop_id'].apply(list).to_dict()
        stops_time = time.time() - stops_start
        logger.info(f"Stops chargés en {stops_time:.3f}s")
        
        # Charger les transfers
        transfers_start = time.time()
        self._load_transfers()
        transfers_time = time.time() - transfers_start
        logger.info(f"Transfers chargés en {transfers_time:.3f}s")
        
        # Charger le cache global des stop_times (NOUVEAU)
        stop_times_start = time.time()
        self._load_stop_times_cache()
        stop_times_time = time.time() - stop_times_start
        logger.info(f"Stop_times cache chargé en {stop_times_time:.3f}s")
        
        # NOUVEAU : Charger le cache des temps de trajet
        travel_time_start = time.time()
        self._load_travel_time_cache()
        travel_time_time = time.time() - travel_time_start
        logger.info(f"Travel time cache chargé en {travel_time_time:.3f}s")
        
        total_time = time.time() - start_time
        logger.info(f"Données GTFS temporelles chargées en {total_time:.3f}s (routes: {routes_time:.3f}s, trips: {trips_time:.3f}s, stops: {stops_time:.3f}s, transfers: {transfers_time:.3f}s, stop_times: {stop_times_time:.3f}s, travel_times: {travel_time_time:.3f}s)")
    
    def _load_stop_times_cache(self):
        """Charge le cache global des stop_times pour éviter les relectures"""
        if self.stop_times_loaded:
            return
            
        cache_file = self.cache_dir / 'global_stop_times.pkl'
        
        # Essayer de charger depuis le cache
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    self.stop_times_cache = pickle.load(f)
                self.stop_times_loaded = True
                logger.info(f"[GTFS] Cache global stop_times chargé: {len(self.stop_times_cache)} entrées")
                return
            except Exception as e:
                logger.warning(f"[GTFS] Erreur lors du chargement du cache stop_times: {e}")
        
        # Charger depuis le fichier GTFS
        logger.info("[GTFS] Chargement du fichier stop_times.txt...")
        stop_times_df = pd.read_csv(
            os.path.join(self.gtfs_dir, 'stop_times.txt'),
            usecols=['trip_id', 'stop_id', 'departure_time', 'arrival_time'],
            dtype={
                'trip_id': 'string',
                'stop_id': 'string',
                'departure_time': 'string',
                'arrival_time': 'string'
            }
        )
        
        # Grouper par trip_id pour un accès rapide
        self.stop_times_cache = {}
        for trip_id, group in stop_times_df.groupby('trip_id'):
            self.stop_times_cache[trip_id] = group.to_dict('records')
        
        # Sauvegarder en cache
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(self.stop_times_cache, f)
            logger.info(f"[GTFS] Cache global stop_times sauvegardé: {len(self.stop_times_cache)} entrées")
        except Exception as e:
            logger.warning(f"[GTFS] Erreur lors de la sauvegarde du cache stop_times: {e}")
        
        self.stop_times_loaded = True
    
    def _load_transfers(self):
        """Charge les temps de correspondance"""
        transfers_file = os.path.join(self.gtfs_dir, 'transfers.txt')
        if os.path.exists(transfers_file):
            transfers_df = pd.read_csv(
                transfers_file,
                usecols=['from_stop_id', 'to_stop_id', 'min_transfer_time'],
                dtype={'from_stop_id': 'string', 'to_stop_id': 'string', 'min_transfer_time': 'int32'}
            )
            
            # Créer un dictionnaire des temps de correspondance
            self.transfers = {}
            for _, row in transfers_df.iterrows():
                from_name = self.stop_id_to_name.get(row['from_stop_id'])
                to_name = self.stop_id_to_name.get(row['to_stop_id'])
                if from_name and to_name:
                    key = (from_name, to_name)
                    self.transfers[key] = row['min_transfer_time']
        else:
            self.transfers = {}
            logger.warning("Fichier transfers.txt non trouvé")
    
    def _get_station_schedules_cache_key(self, station: str, line: str, target_date: date) -> str:
        """Génère une clé de cache pour les horaires d'une station"""
        return f"{station}_{line}_{target_date.isoformat()}"
    
    def get_station_schedules(
        self, 
        station: str, 
        line: str, 
        target_date: date
    ) -> List[Dict]:
        """
        Récupère les horaires d'une station pour une ligne et une date
        
        Args:
            station: Nom de la station
            line: Nom de la ligne (ex: "1", "2", etc.)
            target_date: Date cible
        
        Returns:
            Liste des horaires avec departure_time et arrival_time
        """
        start_time = time.time()
        cache_key = self._get_station_schedules_cache_key(station, line, target_date)
        
        # Vérifier le cache mémoire
        cache_memory_start = time.time()
        if cache_key in self.schedule_cache:
            cache_memory_time = time.time() - cache_memory_start
            logger.info(f"[GTFS] Horaires trouvés en cache mémoire en {cache_memory_time:.3f}s")
            return self.schedule_cache[cache_key]
        cache_memory_time = time.time() - cache_memory_start
        
        # Charger depuis le fichier de cache
        cache_file_start = time.time()
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                schedules = pickle.load(f)
                self.schedule_cache[cache_key] = schedules
                cache_file_time = time.time() - cache_file_start
                total_time = time.time() - start_time
                logger.info(f"[GTFS] Horaires chargés depuis le cache fichier en {cache_file_time:.3f}s (total: {total_time:.3f}s)")
                return schedules
        cache_file_time = time.time() - cache_file_start
        
        # Calculer les horaires
        calc_start = time.time()
        schedules = self._calculate_station_schedules(station, line, target_date)
        calc_time = time.time() - calc_start
        
        # Sauvegarder en cache
        save_start = time.time()
        self.schedule_cache[cache_key] = schedules
        with open(cache_file, 'wb') as f:
            pickle.dump(schedules, f)
        save_time = time.time() - save_start
        
        total_time = time.time() - start_time
        logger.info(f"[GTFS] Horaires calculés en {calc_time:.3f}s, sauvegardés en {save_time:.3f}s (total: {total_time:.3f}s)")
        
        return schedules
    
    def _calculate_station_schedules(
        self, 
        station: str, 
        line: str, 
        target_date: date
    ) -> List[Dict]:
        """Calcule les horaires d'une station pour une ligne et une date (OPTIMISÉ)"""
        start_time = time.time()
        
        # Obtenir les IDs de la station et de la ligne
        station_ids = self.stop_name_to_ids.get(station, [])
        route_ids = self.route_name_to_ids.get(line, [])  # CORRECTION: Utiliser tous les route_ids
        
        if not station_ids or not route_ids:
            logger.warning(f"[GTFS] Station {station} ou ligne {line} non trouvée")
            return []
        
        # Obtenir les trips de cette ligne (CORRECTION: Tous les route_ids)
        trips_start = time.time()
        line_trips = self.trips_df[self.trips_df['route_id'].isin(route_ids)]['trip_id'].tolist()
        trips_time = time.time() - trips_start
        
        if not line_trips:
            logger.warning(f"[GTFS] Aucun trip trouvé pour la ligne {line}")
            return []
        
        # Utiliser le cache global des stop_times (OPTIMISATION MAJEURE)
        stop_times_start = time.time()
        schedules = []
        
        # Parcourir les trips de la ligne
        for trip_id in line_trips:
            if trip_id in self.stop_times_cache:
                trip_stops = self.stop_times_cache[trip_id]
                
                # Filtrer pour les stations de la station demandée
                for stop_data in trip_stops:
                    if stop_data['stop_id'] in station_ids:
                        # Convertir les horaires en datetime
                        departure_time = self._parse_gtfs_time(stop_data['departure_time'], target_date)
                        arrival_time = self._parse_gtfs_time(stop_data['arrival_time'], target_date)
                        
                        schedules.append({
                            'departure_time': departure_time,
                            'arrival_time': arrival_time,
                            'trip_id': trip_id
                        })
        
        stop_times_time = time.time() - stop_times_start
        
        # Trier par heure de départ
        sort_start = time.time()
        schedules.sort(key=lambda x: x['departure_time'])
        sort_time = time.time() - sort_start
        
        total_time = time.time() - start_time
        logger.info(f"[GTFS] Calcul des horaires: trips={trips_time:.3f}s, stop_times={stop_times_time:.3f}s, sort={sort_time:.3f}s (total: {total_time:.3f}s)")
        
        return schedules
    
    def _parse_gtfs_time(self, time_str: str, target_date: date) -> datetime:
        """Parse un horaire GTFS et le convertit en datetime"""
        hours, minutes, seconds = map(int, time_str.split(':'))
        
        # Gérer les heures > 24 (jour suivant)
        if hours >= 24:
            hours -= 24
            target_date += timedelta(days=1)
        
        return datetime.combine(target_date, datetime.min.time()) + timedelta(
            hours=hours, minutes=minutes, seconds=seconds
        )
    
    def get_next_departure(
        self, 
        station: str, 
        line: str, 
        after_time: datetime
    ) -> Optional[datetime]:
        """
        Trouve le prochain départ d'une ligne depuis une station
        
        Args:
            station: Nom de la station
            line: Nom de la ligne
            after_time: Heure après laquelle chercher
        
        Returns:
            Heure du prochain départ ou None
        """
        start_time = time.time()
        
        schedules = self.get_station_schedules(station, line, after_time.date())
        
        # Chercher le prochain départ
        search_start = time.time()
        for schedule in schedules:
            if schedule['departure_time'] >= after_time:
                search_time = time.time() - search_start
                total_time = time.time() - start_time
                logger.info(f"[GTFS] Prochain départ trouvé en {search_time:.3f}s (total: {total_time:.3f}s)")
                return schedule['departure_time']
        
        # Si pas trouvé, essayer le jour suivant
        next_date_start = time.time()
        next_date = after_time.date() + timedelta(days=1)
        next_schedules = self.get_station_schedules(station, line, next_date)
        
        if next_schedules:
            next_date_time = time.time() - next_date_start
            total_time = time.time() - start_time
            logger.info(f"[GTFS] Prochain départ trouvé le jour suivant en {next_date_time:.3f}s (total: {total_time:.3f}s)")
            return next_schedules[0]['departure_time']
        
        search_time = time.time() - search_start
        total_time = time.time() - start_time
        logger.warning(f"[GTFS] Aucun départ trouvé en {search_time:.3f}s (total: {total_time:.3f}s)")
        
        return None
    
    def get_transfer_time(self, from_station: str, to_station: str) -> int:
        """
        Récupère le temps de correspondance entre deux stations
        
        Args:
            from_station: Station de départ
            to_station: Station d'arrivée
        
        Returns:
            Temps de correspondance en secondes (défaut: 300s)
        """
        start_time = time.time()
        
        # Vérifier le cache
        cache_key = (from_station, to_station)
        if cache_key in self.transfer_cache:
            cache_time = time.time() - start_time
            logger.info(f"[GTFS] Temps de correspondance trouvé en cache en {cache_time:.3f}s")
            return self.transfer_cache[cache_key]
        
        # Chercher dans les transfers
        transfer_time = self.transfers.get(cache_key, 300)  # 5 min par défaut
        
        # Mettre en cache
        self.transfer_cache[cache_key] = transfer_time
        
        total_time = time.time() - start_time
        logger.info(f"[GTFS] Temps de correspondance calculé en {total_time:.3f}s")
        
        return transfer_time
    
    def get_transfer_time_between_lines(self, station: str, from_line: str, to_line: str) -> int:
        """
        Calcule le temps de transfert entre deux lignes dans une même station
        
        Args:
            station: Nom de la station (ex: "Châtelet")
            from_line: Ligne de départ (ex: "1")
            to_line: Ligne d'arrivée (ex: "14")
            
        Returns:
            Temps de transfert en secondes
        """
        start_time = time.time()
        # Passer self à TransferService pour accès aux mappings
        transfer_time = self.transfer_service.get_transfer_time_between_lines(station, from_line, to_line, gtfs_service=self)
        total_time = time.time() - start_time
        logger.info(f"[GTFS] Transfert {station} {from_line}→{to_line}: {transfer_time}s (calculé en {total_time:.3f}s)")
        return transfer_time
    
    def get_station_lines(self, station: str) -> List[str]:
        """
        Récupère toutes les lignes qui desservent une station (OPTIMISÉ)
        
        Args:
            station: Nom de la station
        
        Returns:
            Liste des noms de lignes
        """
        start_time = time.time()
        
        station_ids = self.stop_name_to_ids.get(station, [])
        if not station_ids:
            return []
        
        # Utiliser le cache global des stop_times (OPTIMISATION)
        station_trips = set()
        
        # Parcourir le cache pour trouver les trips qui passent par cette station
        for trip_id, trip_stops in self.stop_times_cache.items():
            for stop_data in trip_stops:
                if stop_data['stop_id'] in station_ids:
                    station_trips.add(trip_id)
                    break  # Un seul arrêt suffit pour cette station
        
        # Obtenir les routes correspondantes
        station_routes = set()
        for trip_id in station_trips:
            route_id = self.trip_to_route.get(trip_id)
            if route_id:
                station_routes.add(route_id)
        
        # Convertir en noms de lignes
        lines = []
        for route_id in station_routes:
            line_name = self.route_id_to_name.get(route_id)
            if line_name:
                lines.append(line_name)
        
        total_time = time.time() - start_time
        logger.info(f"[GTFS] Lignes de la station trouvées en {total_time:.3f}s")
        
        return sorted(list(set(lines)))
    
    def clear_cache(self):
        """Vide le cache des horaires"""
        self.schedule_cache.clear()
        self.transfer_cache.clear()
        self.stop_times_cache.clear()
        self.stop_times_loaded = False
        
        # Supprimer les fichiers de cache
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()
        
        logger.info("Cache des horaires vidé")
    
    def _load_travel_time_cache(self):
        """Charge le cache des temps de trajet réels entre stations"""
        if self.travel_time_cache_loaded:
            return
            
        cache_file = self.cache_dir / 'travel_times_cache.pkl'
        
        # Essayer de charger depuis le cache
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    self.travel_time_cache = pickle.load(f)
                self.travel_time_cache_loaded = True
                logger.info(f"[GTFS] Cache des temps de trajet chargé: {len(self.travel_time_cache)} entrées")
                return
            except Exception as e:
                logger.warning(f"[GTFS] Erreur lors du chargement du cache des temps de trajet: {e}")
        
        # Pré-calculer les temps de trajet pour toutes les paires de stations sur chaque ligne
        logger.info("[GTFS] Pré-calcul des temps de trajet entre stations...")
        
        for line_name, route_ids in self.route_name_to_ids.items():
            logger.info(f"[GTFS] Calcul des temps pour la ligne {line_name}...")
            
            # Obtenir tous les trips de cette ligne
            trips = self.trips_df[self.trips_df['route_id'].isin(route_ids)]['trip_id'].tolist()
            
            for trip_id in trips[:10]:  # Limiter à 10 trips par ligne pour les performances
                stops = self.stop_times_cache.get(trip_id, [])
                if len(stops) < 2:
                    continue
                
                # Calculer les temps entre toutes les paires de stations de ce trip
                for i in range(len(stops)):
                    for j in range(i + 1, len(stops)):
                        stop_a = stops[i]
                        stop_b = stops[j]
                        
                        # Obtenir les noms des stations
                        station_a = self.stop_id_to_name.get(stop_a['stop_id'])
                        station_b = self.stop_id_to_name.get(stop_b['stop_id'])
                        
                        if not station_a or not station_b:
                            continue
                        
                        # Calculer le temps de trajet
                        dep_time = self._parse_gtfs_time(stop_a['departure_time'], date.today())
                        arr_time = self._parse_gtfs_time(stop_b['arrival_time'], date.today())
                        travel_time = int((arr_time - dep_time).total_seconds())
                        
                        # Stocker dans le cache
                        cache_key = (station_a, station_b, line_name)
                        if cache_key not in self.travel_time_cache:
                            self.travel_time_cache[cache_key] = []
                        self.travel_time_cache[cache_key].append(travel_time)
        
        # Prendre le temps médian pour chaque paire
        for key, times in self.travel_time_cache.items():
            if times:
                self.travel_time_cache[key] = sorted(times)[len(times)//2]  # Médiane
        
        # Sauvegarder en cache
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(self.travel_time_cache, f)
            logger.info(f"[GTFS] Cache des temps de trajet sauvegardé: {len(self.travel_time_cache)} entrées")
        except Exception as e:
            logger.warning(f"[GTFS] Erreur lors de la sauvegarde du cache des temps de trajet: {e}")
        
        self.travel_time_cache_loaded = True
    
    def get_travel_time(self, from_station: str, to_station: str, line: str) -> Optional[int]:
        """
        Récupère le temps de trajet entre deux stations sur une ligne donnée
        
        Args:
            from_station: Station de départ
            to_station: Station d'arrivée
            line: Ligne de métro
        
        Returns:
            Temps de trajet en secondes ou None si non trouvé
        """
        cache_key = (from_station, to_station, line)
        return self.travel_time_cache.get(cache_key) 