"""
MetroCity - Mastercamp 2025
Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
Fichier: gtfs_parser.py
Description: Utilitaire de parsing des données GTFS pour construire le graphe du métro parisien
"""

import os
import pandas as pd
import logging
import json
import pickle
from typing import Dict, List, Tuple, Set, Any
from pathlib import Path
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import hashlib
import numpy as np
from functools import lru_cache
import sys
from tqdm import tqdm

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Lignes de métro parisien (y compris 3B, 7B et RER)
PARIS_METRO_LINES = [str(i) for i in range(1, 15)] + ['3B', '7B', 'A', 'B', 'C', 'D', 'E']

class GTFSMetroParser:
    def __init__(self, gtfs_dir: str):
        self.gtfs_dir = gtfs_dir
        self.cache_dir = Path(gtfs_dir).parent / 'cache'
        self.cache_dir.mkdir(exist_ok=True)
        
        # Chemins des fichiers de cache optimisés
        self.graph_cache = self.cache_dir / 'metro_graph.pkl'
        self.stats_cache = self.cache_dir / 'metro_stats.json'
        
        # Charger les données GTFS avec optimisations
        self._load_gtfs_data()
    
    def _load_gtfs_data(self):
        """Charge les données GTFS avec optimisations majeures."""
        start_time = time.time()
        
        # OPTIMISATION 1: Charger seulement les colonnes nécessaires avec des types optimisés
        logger.info("Chargement optimisé des routes...")
        self.routes_df = pd.read_csv(
            os.path.join(self.gtfs_dir, 'routes.txt'),
            usecols=['route_id', 'route_short_name', 'route_type'],
            dtype={
                'route_id': 'string',
                'route_short_name': 'string',
                'route_type': 'int8'
            },
            low_memory=False
        )
        
        # Filtrer pour ne garder que le métro parisien ET les RER
        self.routes_df = self.routes_df[
            ((self.routes_df['route_type'] == 1) | (self.routes_df['route_type'] == 2)) &
            (self.routes_df['route_short_name'].isin(PARIS_METRO_LINES))
        ]
        
        # Créer des index pour un accès plus rapide
        self.routes_df.set_index('route_id', inplace=True)
        
        logger.info(f"Routes filtrées: {len(self.routes_df)} lignes de métro")
        
        # OPTIMISATION 2: Charger les trips avec index
        logger.info("Chargement optimisé des trips...")
        self.trips_df = pd.read_csv(
            os.path.join(self.gtfs_dir, 'trips.txt'),
            usecols=['trip_id', 'route_id'],
            dtype={
                'trip_id': 'string',
                'route_id': 'string'
            },
            low_memory=False
        )
        
        # Filtrer les trips pour les routes de métro
        metro_route_ids = set(self.routes_df.index)
        self.trips_df = self.trips_df[self.trips_df['route_id'].isin(metro_route_ids)]
        self.trips_df.set_index('trip_id', inplace=True)
        
        logger.info(f"Trips filtrés: {len(self.trips_df)} trajets de métro")
        
        # OPTIMISATION 3: Charger stop_times par chunks optimisés
        logger.info("Chargement optimisé des stop_times...")
        metro_trip_ids = set(self.trips_df.index)
        
        # Lire stop_times par chunks pour économiser la mémoire
        chunk_size = 500000  # Augmenter la taille des chunks
        stop_times_chunks = []
        
        # Obtenir la taille totale du fichier pour estimer le nombre de chunks
        stop_times_file = os.path.join(self.gtfs_dir, 'stop_times.txt')
        with open(stop_times_file, 'r') as f:
            total_lines = sum(1 for _ in f) - 1  # -1 pour l'en-tête
        estimated_chunks = max(1, total_lines // chunk_size)
        
        chunk_reader = pd.read_csv(
            stop_times_file,
            usecols=['trip_id', 'stop_id', 'stop_sequence', 'departure_time', 'arrival_time'],
            dtype={
                'trip_id': 'string',
                'stop_id': 'string',
                'stop_sequence': 'int16',
                'departure_time': 'string',
                'arrival_time': 'string'
            },
            chunksize=chunk_size,
            low_memory=False,
            quoting=1
        )
        
        for chunk in tqdm(chunk_reader, total=estimated_chunks, desc='Chargement stop_times'):
            # Filtrer le chunk pour ne garder que les trips de métro
            filtered_chunk = chunk[chunk['trip_id'].isin(metro_trip_ids)]
            if not filtered_chunk.empty:
                stop_times_chunks.append(filtered_chunk)
        
        # Combiner tous les chunks
        self.stop_times_df = pd.concat(stop_times_chunks, ignore_index=True)
        del stop_times_chunks  # Libérer la mémoire
        
        # OPTIMISATION: Créer un index sur trip_id pour un accès plus rapide
        self.stop_times_df.set_index('trip_id', inplace=True)
        
        logger.info(f"Stop_times filtrés: {len(self.stop_times_df)} arrêts de métro")
        
        # OPTIMISATION 4: Charger seulement les stops utilisés
        logger.info("Chargement optimisé des stops...")
        used_stop_ids = set(self.stop_times_df['stop_id'].unique())
        
        self.stops_df = pd.read_csv(
            os.path.join(self.gtfs_dir, 'stops.txt'),
            usecols=['stop_id', 'stop_name', 'stop_lat', 'stop_lon'],
            dtype={
                'stop_id': 'string',
                'stop_name': 'string',
                'stop_lat': 'float32',
                'stop_lon': 'float32'
            },
            low_memory=False
        )
        self.stops_df = self.stops_df[self.stops_df['stop_id'].isin(used_stop_ids)]
        self.stops_df.set_index('stop_id', inplace=True)
        
        logger.info(f"Stops filtrés: {len(self.stops_df)} arrêts de métro")
        
        # OPTIMISATION 5: Créer des mappings optimisés
        self.route_names = self.routes_df['route_short_name'].to_dict()
        self.trip_routes = self.trips_df['route_id'].to_dict()
        
        # OPTIMISATION 6: Charger les transfers avec cache intelligent
        logger.info("Chargement optimisé des transfers...")
        self._load_transfers()
        
        # OPTIMISATION 7: Créer les groupes de stations avec algorithme optimisé
        self._create_station_groups()
        
        # OPTIMISATION 8: Créer les mappings finaux optimisés
        self._create_final_mappings()
        
        total_time = time.time() - start_time
        logger.info(f"Données GTFS chargées en {total_time:.3f}s")
    
    def _load_transfers(self):
        """Charge les transfers avec cache intelligent."""
        transfers_file = os.path.join(self.gtfs_dir, 'transfers.txt')
        transfers_cache = self.cache_dir / 'transfers_filtered.pkl'
        
        # Calculer un hash du fichier source pour l'invalider si modifié
        def file_hash(path):
            h = hashlib.sha256()
            with open(path, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    h.update(chunk)
            return h.hexdigest()
        
        hash_file = self.cache_dir / 'transfers_hash.txt'
        current_hash = file_hash(transfers_file) if os.path.exists(transfers_file) else None
        cache_valid = False
        
        if transfers_cache.exists() and hash_file.exists():
            with open(hash_file, 'r') as f:
                cached_hash = f.read().strip()
            if cached_hash == current_hash:
                cache_valid = True
        
        if cache_valid:
            with open(transfers_cache, 'rb') as f:
                self.transfers_df = pickle.load(f)
            logger.info(f"Transfers filtrés chargés depuis le cache ({len(self.transfers_df)} transferts)")
        else:
            self.transfers_df = pd.read_csv(
                transfers_file,
                usecols=['from_stop_id', 'to_stop_id', 'transfer_type'],
                dtype={
                    'from_stop_id': 'string',
                    'to_stop_id': 'string',
                    'transfer_type': 'int8'
                },
                low_memory=False
            )
            
            # OPTIMISATION: Filtrer seulement les transfers entre stops utilisés
            used_stop_ids = set(self.stops_df.index)
            self.transfers_df = self.transfers_df[
                (self.transfers_df['from_stop_id'].isin(used_stop_ids)) &
                (self.transfers_df['to_stop_id'].isin(used_stop_ids))
            ]
            
            with open(transfers_cache, 'wb') as f:
                pickle.dump(self.transfers_df, f)
            with open(hash_file, 'w') as f:
                f.write(current_hash or '')
            logger.info(f"Transfers filtrés sauvegardés dans le cache ({len(self.transfers_df)} transferts)")
    
    def _create_station_groups(self):
        """Crée des groupes de stations avec algorithme optimisé."""
        logger.info("Création optimisée des groupes de stations...")
        
        # OPTIMISATION: Pré-calculer les mappings stop_id → route_type et stop_id → name
        logger.info("Pré-calcul des mappings stop_id...")
        
        # Créer un mapping stop_id → route_types de manière vectorisée
        stop_times_subset = self.stop_times_df[['stop_id']].reset_index()
        trips_df_reset = self.trips_df.reset_index()
        
        # Typage strict pour éviter les erreurs de merge
        stop_times_subset['trip_id'] = stop_times_subset['trip_id'].astype(str)
        trips_df_reset['trip_id'] = trips_df_reset['trip_id'].astype(str)
        
        stop_trip_mapping = stop_times_subset.merge(
            trips_df_reset, 
            left_on='trip_id', 
            right_on='trip_id', 
            how='left'
        )
        
        # Obtenir les route_types pour chaque stop_id
        routes_df_reset = self.routes_df.reset_index()
        routes_df_reset['route_id'] = routes_df_reset['route_id'].astype(str)
        stop_trip_mapping['route_id'] = stop_trip_mapping['route_id'].astype(str)
        
        stop_route_mapping = stop_trip_mapping.merge(
            routes_df_reset,
            left_on='route_id',
            right_on='route_id',
            how='left'
        )
        
        # Grouper par stop_id et obtenir les types uniques
        stop_id_to_types = stop_route_mapping.groupby('stop_id')['route_type'].apply(set).to_dict()
        
        # Mapping stop_id → name
        stop_id_to_name = self.stops_df['stop_name'].to_dict()
        
        # OPTIMISATION: Filtrer les transfers de type 2 de manière vectorisée
        physical_transfers = self.transfers_df[self.transfers_df['transfer_type'] == 2].copy()
        
        # OPTIMISATION: Créer les groupes avec algorithme Union-Find optimisé
        logger.info("Création des groupes avec Union-Find...")
        
        # Initialiser Union-Find
        parent = {}
        rank = {}
        
        def find(x):
            if x not in parent:
                parent[x] = x
                rank[x] = 0
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y):
            px, py = find(x), find(y)
            if px == py:
                return
            if rank[px] < rank[py]:
                parent[px] = py
            elif rank[px] > rank[py]:
                parent[py] = px
            else:
                parent[py] = px
                rank[px] += 1
        
        # Traiter les transfers physiques
        for _, transfer in tqdm(physical_transfers.iterrows(), total=len(physical_transfers), desc='Traitement transfers physiques'):
            from_stop = transfer['from_stop_id']
            to_stop = transfer['to_stop_id']
            
            # Vérifier la compatibilité des types et noms
            types_from = stop_id_to_types.get(from_stop, {1})
            types_to = stop_id_to_types.get(to_stop, {1})
            name_from = stop_id_to_name.get(from_stop)
            name_to = stop_id_to_name.get(to_stop)
            
            if types_from.isdisjoint(types_to) or name_from != name_to:
                continue
            
            union(from_stop, to_stop)
        
        # OPTIMISATION: Créer les groupes finaux de manière vectorisée
        logger.info("Finalisation des groupes...")
        
        # Créer les groupes
        groups = defaultdict(set)
        for stop_id in set(stop_id_to_types.keys()) | set(stop_id_to_name.keys()):
            if stop_id in parent:
                root = find(stop_id)
                groups[root].add(stop_id)
        
        # Créer les mappings finaux
        self.station_groups = {}
        self.stop_id_to_main_station = {}
        
        for group_key, group_stops in groups.items():
            if len(group_stops) < 2:
                continue
                
            # Trouver le nom principal (le plus fréquent)
            station_names = []
            for stop_id in group_stops:
                if stop_id in stop_id_to_name:
                    station_names.append(stop_id_to_name[stop_id])
            
            if station_names:
                # Utiliser le mode (le plus fréquent)
                from collections import Counter
                name_counts = Counter(station_names)
                main_station_name = name_counts.most_common(1)[0][0]
                
                self.station_groups[group_key] = {
                    'main_name': main_station_name,
                    'stop_ids': list(group_stops),
                    'all_names': list(set(station_names))
                }
                
                for stop_id in group_stops:
                    self.stop_id_to_main_station[stop_id] = main_station_name
        
        logger.info(f"Créé {len(self.station_groups)} groupes de stations optimisés")
    
    def _create_final_mappings(self):
        """Crée les mappings finaux optimisés."""
        # Créer un mapping stop_id -> nom principal (en tenant compte des groupes)
        self.stop_id_to_name = {}
        for stop_id in self.stops_df.index:
            # Utiliser le nom principal si la station fait partie d'un groupe
            if stop_id in self.stop_id_to_main_station:
                self.stop_id_to_name[stop_id] = self.stop_id_to_main_station[stop_id]
            else:
                self.stop_id_to_name[stop_id] = self.stops_df.loc[stop_id, 'stop_name']
        
        # Créer un mapping nom principal -> liste de stop_ids
        self.stop_name_to_ids = defaultdict(list)
        for stop_id, name in self.stop_id_to_name.items():
            self.stop_name_to_ids[name].append(stop_id)
        
        # Créer un mapping nom principal -> coordonnées (prendre la première occurrence)
        self.stop_name_to_coords = {}
        for stop_id, name in self.stop_id_to_name.items():
            if name not in self.stop_name_to_coords:
                coords = (self.stops_df.loc[stop_id, 'stop_lon'], self.stops_df.loc[stop_id, 'stop_lat'])
                self.stop_name_to_coords[name] = coords
    
    def build_metro_graph(self, parallel=True) -> Tuple[Dict[str, List[Tuple[str, int]]], Dict[str, Tuple[float, float]], Dict[str, List[str]], Set[str], Dict[str, int]]:
        """Construit le graphe métro avec optimisations majeures - TRAITEMENT VECTORISÉ GLOBAL."""
        start_time = time.time()
        
        # Essayer de charger depuis le cache
        cached_graph = self._load_graph()
        if cached_graph is not None:
            logger.info("Graphe optimisé chargé depuis le cache")
            return cached_graph
        
        logger.info("Construction optimisée du graphe depuis les données GTFS...")
        
        # OPTIMISATION RÉVOLUTIONNAIRE: Traitement vectorisé global au lieu de route par route
        logger.info("Traitement vectorisé global des connexions...")
        
        # Initialiser les structures de données
        graph = {name: set() for name in self.stop_name_to_ids}
        positions = self.stop_name_to_coords.copy()
        lines = {name: set() for name in self.stop_name_to_ids}
        terminus = set()
        
        # OPTIMISATION RÉVOLUTIONNAIRE: Traitement global vectorisé
        # 1. Créer un DataFrame avec toutes les connexions
        logger.info("Création du DataFrame des connexions...")
        
        # Préparer les données pour le traitement vectorisé
        stop_times_with_routes = self.stop_times_df.reset_index()
        stop_times_with_routes['route_id'] = stop_times_with_routes['trip_id'].map(self.trip_routes)
        stop_times_with_routes['route_name'] = stop_times_with_routes['route_id'].map(self.route_names)
        
        # Grouper par trip_id et créer les connexions
        connections = []
        
        for trip_id, trip_data in tqdm(stop_times_with_routes.groupby('trip_id'), desc='Traitement vectorisé global'):
            if len(trip_data) < 2:
                continue
            
            # Trier par stop_sequence
            trip_data = trip_data.sort_values('stop_sequence')
            
            # Créer les connexions consécutives
            for i in range(len(trip_data) - 1):
                current_stop = trip_data.iloc[i]
                next_stop = trip_data.iloc[i + 1]
                
                # Obtenir les noms des stations
                current_station = self.stop_id_to_main_station.get(current_stop['stop_id'], self.stop_id_to_name[current_stop['stop_id']])
                next_station = self.stop_id_to_main_station.get(next_stop['stop_id'], self.stop_id_to_name[next_stop['stop_id']])
                
                if current_station != next_station:
                    # Calculer le temps de trajet
                    current_time = self._time_to_seconds_optimized(current_stop['departure_time'])
                    next_time = self._time_to_seconds_optimized(next_stop['arrival_time'])
                    duration = next_time - current_time
                    
                    if duration < 0:
                        duration += 24 * 3600
                    
                    connections.append({
                        'from_station': current_station,
                        'to_station': next_station,
                        'time': duration,
                        'route': current_stop['route_name']
                    })
            
            # Marquer les terminus
            if len(trip_data) > 0:
                first_station = self.stop_id_to_main_station.get(trip_data.iloc[0]['stop_id'], self.stop_id_to_name[trip_data.iloc[0]['stop_id']])
                last_station = self.stop_id_to_main_station.get(trip_data.iloc[-1]['stop_id'], self.stop_id_to_name[trip_data.iloc[-1]['stop_id']])
                terminus.add(first_station)
                terminus.add(last_station)
        
        # OPTIMISATION: Construire le graphe à partir des connexions
        logger.info("Construction du graphe à partir des connexions...")
        
        for connection in connections:
            from_station = connection['from_station']
            to_station = connection['to_station']
            time_val = connection['time']
            route = connection['route']
            
            # Ajouter la connexion
            graph[from_station].add((to_station, time_val))
            graph[to_station].add((from_station, time_val))
            
            # Ajouter les lignes
            lines[from_station].add(route)
            lines[to_station].add(route)
        
        # OPTIMISATION: Finalisation vectorisée
        logger.info("Finalisation optimisée du graphe...")
        graph = {k: sorted(list(v)) for k, v in graph.items()}
        lines = {k: sorted(list(v)) for k, v in lines.items()}
        branches = {k: 0 for k in graph}
        
        result = (graph, positions, lines, terminus, branches)
        self._save_graph(result)
        
        build_time = time.time() - start_time
        logger.info(f"Graphe optimisé construit en {build_time:.3f}s")
        logger.info(f"Nombre de sommets (stations) dans le graphe : {len(graph)}")
        
        return result
    
    @lru_cache(maxsize=10000)
    def _time_to_seconds_optimized(self, time_str: str) -> int:
        """Convertit une chaîne de temps GTFS en secondes avec cache optimisé."""
        hours, minutes, seconds = map(int, time_str.split(':'))
        return hours * 3600 + minutes * 60 + seconds
    
    def _save_graph(self, graph_data: Tuple):
        """Sauvegarde le graphe optimisé."""
        graph, positions, lines, terminus, branches = graph_data
        
        with open(self.graph_cache, 'wb') as f:
            pickle.dump(graph_data, f)
        
        stats = {
            'stations': len(graph),
            'connections': sum(len(v) for v in graph.values()) // 2,
            'terminus': len(terminus),
            'lines': len(set().union(*[set(l) for l in lines.values()]))
        }
        
        with open(self.stats_cache, 'w') as f:
            json.dump(stats, f, indent=2)
    
    def _load_graph(self) -> Tuple:
        """Charge le graphe optimisé depuis le cache."""
        if self.graph_cache.exists():
            with open(self.graph_cache, 'rb') as f:
                return pickle.load(f)
        return None

def parse_gtfs_to_graph(gtfs_dir: str, parallel=True) -> Tuple[Dict[str, List[Tuple[str, int]]], Dict[str, Tuple[float, float]], Dict[str, List[str]], Set[str], Dict[str, int]]:
    """Parse les données GTFS avec optimisations et retourne le graphe du métro."""
    parser = GTFSMetroParser(gtfs_dir)
    return parser.build_metro_graph(parallel=parallel)

# === DÉBUT : Ajout de la fonction worker au niveau module ===
def process_route_worker(args):
    import pandas as pd
    from collections import defaultdict
    route_id, route_names, trips_df, stop_times_df, stop_id_to_main_station, stop_id_to_name = args
    local_graph = defaultdict(set)
    local_lines = defaultdict(set)
    local_terminus = set()
    route_name = route_names[route_id]
    route_trips = trips_df[trips_df['route_id'] == route_id]['trip_id']
    for trip_id in route_trips:
        if trip_id in stop_times_df.index:
            trip_stops = stop_times_df.loc[trip_id].sort_values('stop_sequence')
            if isinstance(trip_stops, pd.Series):
                trip_stops = pd.DataFrame([trip_stops])
            if len(trip_stops) < 2:
                continue
            for i in range(len(trip_stops) - 1):
                current_stop = trip_stops.iloc[i]
                next_stop = trip_stops.iloc[i+1]
                a = stop_id_to_main_station.get(current_stop['stop_id'], stop_id_to_name[current_stop['stop_id']])
                b = stop_id_to_main_station.get(next_stop['stop_id'], stop_id_to_name[next_stop['stop_id']])
                if a != b:
                    current_time = int(current_stop['departure_time'][:2]) * 3600 + int(current_stop['departure_time'][3:5]) * 60 + int(current_stop['departure_time'][6:])
                    next_time = int(next_stop['arrival_time'][:2]) * 3600 + int(next_stop['arrival_time'][3:5]) * 60 + int(next_stop['arrival_time'][6:])
                    duration = next_time - current_time
                    if duration < 0:
                        duration += 24 * 3600
                    local_graph[a].add((b, duration))
                    local_graph[b].add((a, duration))
                    local_lines[a].add(route_name)
                    local_lines[b].add(route_name)
            if len(trip_stops) > 0:
                first_stop = stop_id_to_main_station.get(trip_stops.iloc[0]['stop_id'], stop_id_to_name[trip_stops.iloc[0]['stop_id']])
                last_stop = stop_id_to_main_station.get(trip_stops.iloc[-1]['stop_id'], stop_id_to_name[trip_stops.iloc[-1]['stop_id']])
                local_terminus.add(first_stop)
                local_terminus.add(last_stop)
    return local_graph, local_lines, local_terminus
# === FIN : Ajout de la fonction worker au niveau module === 