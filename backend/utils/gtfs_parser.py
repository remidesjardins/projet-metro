import os
import pandas as pd
import logging
import json
import pickle
from typing import Dict, List, Tuple, Set, Any
from pathlib import Path
import time

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
        
        # Chemins des fichiers de cache
        self.graph_cache = self.cache_dir / 'metro_graph.pkl'
        self.stats_cache = self.cache_dir / 'metro_stats.json'
        
        # Charger les données GTFS
        self._load_gtfs_data()
    
    def _load_gtfs_data(self):
        """Charge les données GTFS depuis les fichiers source avec optimisations."""
        start_time = time.time()
        
        # Optimisation 1: Charger seulement les colonnes nécessaires avec des types optimisés
        logger.info("Chargement des routes...")
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
        
        logger.info(f"Routes filtrées: {len(self.routes_df)} lignes de métro")
        
        # Optimisation 2: Charger les trips avec des types optimisés
        logger.info("Chargement des trips...")
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
        metro_route_ids = set(self.routes_df['route_id'])
        self.trips_df = self.trips_df[self.trips_df['route_id'].isin(metro_route_ids)]
        
        logger.info(f"Trips filtrés: {len(self.trips_df)} trajets de métro")
        
        # Optimisation 3: Charger stop_times par chunks pour économiser la mémoire
        logger.info("Chargement des stop_times...")
        metro_trip_ids = set(self.trips_df['trip_id'])
        
        # Lire stop_times par chunks pour économiser la mémoire
        chunk_size = 100000  # 100k lignes par chunk
        stop_times_chunks = []
        
        for chunk in pd.read_csv(
            os.path.join(self.gtfs_dir, 'stop_times.txt'),
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
        ):
            # Filtrer le chunk pour ne garder que les trips de métro
            filtered_chunk = chunk[chunk['trip_id'].isin(metro_trip_ids)]
            if not filtered_chunk.empty:
                stop_times_chunks.append(filtered_chunk)
        
        # Combiner tous les chunks
        self.stop_times_df = pd.concat(stop_times_chunks, ignore_index=True)
        del stop_times_chunks  # Libérer la mémoire
        
        logger.info(f"Stop_times filtrés: {len(self.stop_times_df)} arrêts de métro")
        
        # Optimisation 4: Charger seulement les stops utilisés
        logger.info("Chargement des stops...")
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
        
        logger.info(f"Stops filtrés: {len(self.stops_df)} arrêts de métro")
        
        # Créer des dictionnaires pour un accès plus rapide
        self.route_names = self.routes_df.set_index('route_id')['route_short_name'].to_dict()
        self.trip_routes = self.trips_df.set_index('trip_id')['route_id'].to_dict()
        
        # Charger les transfers pour identifier les stations physiquement identiques
        logger.info("Chargement des transfers...")
        self.transfers_df = pd.read_csv(
            os.path.join(self.gtfs_dir, 'transfers.txt'),
            usecols=['from_stop_id', 'to_stop_id', 'transfer_type'],
            dtype={
                'from_stop_id': 'string',
                'to_stop_id': 'string',
                'transfer_type': 'int8'
            },
            low_memory=False
        )
        
        # Filtrer seulement les transfers entre stops utilisés
        used_stop_ids = set(self.stops_df['stop_id'].unique())
        self.transfers_df = self.transfers_df[
            (self.transfers_df['from_stop_id'].isin(used_stop_ids)) &
            (self.transfers_df['to_stop_id'].isin(used_stop_ids))
        ]
        
        logger.info(f"Transfers filtrés: {len(self.transfers_df)} transfers entre stations utilisées")
        
        # Créer un mapping des stations physiquement identiques
        self._create_station_groups()
        
        # FUSIONNER LES STATIONS PAR NOM ET PAR GROUPE PHYSIQUE
        # Créer un mapping stop_id -> nom principal (en tenant compte des groupes)
        self.stop_id_to_name = {}
        for _, row in self.stops_df.iterrows():
            stop_id = row['stop_id']
            # Utiliser le nom principal si la station fait partie d'un groupe
            if stop_id in self.stop_id_to_main_station:
                self.stop_id_to_name[stop_id] = self.stop_id_to_main_station[stop_id]
            else:
                self.stop_id_to_name[stop_id] = row['stop_name']
        
        # Créer un mapping nom principal -> liste de stop_ids
        self.stop_name_to_ids = {}
        for stop_id, main_name in self.stop_id_to_name.items():
            if main_name not in self.stop_name_to_ids:
                self.stop_name_to_ids[main_name] = []
            self.stop_name_to_ids[main_name].append(stop_id)
        
        # Créer un mapping nom principal -> coordonnées moyennes
        self.stop_name_to_coords = {}
        for main_name, stop_ids in self.stop_name_to_ids.items():
            coords_list = []
            for stop_id in stop_ids:
                if stop_id in self.stops_df['stop_id'].values:
                    row = self.stops_df[self.stops_df['stop_id'] == stop_id].iloc[0]
                    coords_list.append((row['stop_lat'], row['stop_lon']))
            
            if coords_list:
                # Calculer les coordonnées moyennes
                avg_lat = sum(coord[0] for coord in coords_list) / len(coords_list)
                avg_lon = sum(coord[1] for coord in coords_list) / len(coords_list)
                self.stop_name_to_coords[main_name] = (avg_lat, avg_lon)
        
        # Optimisation 6: Créer un index pour stop_times pour accélérer les recherches
        self.stop_times_df.set_index('trip_id', inplace=True)
        
        load_time = time.time() - start_time
        logger.info(f"Données GTFS chargées en {load_time:.2f}s")

    def _create_station_groups(self):
        """Crée des groupes de stations physiquement identiques basés sur les transfers, mais uniquement si même type de ligne ET même nom exact."""
        logger.info("Création des groupes de stations physiquement identiques...")
        
        transfer_groups = {}
        group_id = 0
        
        # Pour chaque stop_id, déterminer le type de ligne (métro, RER, bus) et le nom
        stop_id_to_types = {}
        stop_id_to_name = {}
        for stop_id in self.stops_df['stop_id'].values:
            # On cherche tous les trips qui passent par ce stop
            trip_ids = self.stop_times_df[self.stop_times_df['stop_id'] == stop_id].index.unique()
            route_types = set()
            for trip_id in trip_ids:
                if trip_id in self.trip_routes:
                    route_id = self.trip_routes[trip_id]
                    if route_id in self.routes_df['route_id'].values:
                        route_type = self.routes_df[self.routes_df['route_id'] == route_id]['route_type'].iloc[0]
                        route_types.add(route_type)
            stop_id_to_types[stop_id] = route_types if route_types else {1}  # défaut métro
            # Nom de la station
            row = self.stops_df[self.stops_df['stop_id'] == stop_id]
            stop_id_to_name[stop_id] = row.iloc[0]['stop_name'] if not row.empty else None
        
        # Filtrer les transfers de type 2 (stations physiquement identiques)
        physical_transfers = self.transfers_df[self.transfers_df['transfer_type'] == 2]
        
        # Créer des groupes de stations connectées
        for _, transfer in physical_transfers.iterrows():
            from_stop = transfer['from_stop_id']
            to_stop = transfer['to_stop_id']
            
            # Empêcher la fusion si les stops sont de types de lignes incompatibles ou de noms différents
            types_from = stop_id_to_types.get(from_stop, {1})
            types_to = stop_id_to_types.get(to_stop, {1})
            name_from = stop_id_to_name.get(from_stop)
            name_to = stop_id_to_name.get(to_stop)
            if types_from.isdisjoint(types_to):
                continue
            if name_from != name_to:
                continue
            
            # Trouver les groupes existants
            from_group = None
            to_group = None
            for group_key, group_stops in transfer_groups.items():
                if from_stop in group_stops:
                    from_group = group_key
                if to_stop in group_stops:
                    to_group = group_key
            if from_group is None and to_group is None:
                new_group = f"group_{group_id}"
                transfer_groups[new_group] = {from_stop, to_stop}
                group_id += 1
            elif from_group is None:
                transfer_groups[to_group].add(from_stop)
            elif to_group is None:
                transfer_groups[from_group].add(to_stop)
            elif from_group != to_group:
                merged_group = transfer_groups[from_group] | transfer_groups[to_group]
                transfer_groups[from_group] = merged_group
                del transfer_groups[to_group]
        
        # Créer un mapping stop_id -> nom de station principal
        self.station_groups = {}
        self.stop_id_to_main_station = {}
        for group_key, group_stops in transfer_groups.items():
            station_names = {}
            for stop_id in group_stops:
                if stop_id in self.stops_df['stop_id'].values:
                    station_name = self.stops_df[self.stops_df['stop_id'] == stop_id]['stop_name'].iloc[0]
                    station_names[station_name] = station_names.get(station_name, 0) + 1
            if station_names:
                main_station_name = max(station_names.items(), key=lambda x: x[1])[0]
                self.station_groups[group_key] = {
                    'main_name': main_station_name,
                    'stop_ids': list(group_stops),
                    'all_names': list(station_names.keys())
                }
                for stop_id in group_stops:
                    self.stop_id_to_main_station[stop_id] = main_station_name
        logger.info(f"Créé {len(self.station_groups)} groupes de stations physiquement identiques")
        example_groups = list(self.station_groups.items())[:5]
        for group_key, group_info in example_groups:
            logger.info(f"Groupe {group_key}: {group_info['main_name']} (contient {len(group_info['stop_ids'])} stops)")

    def _save_graph(self, graph_data: Tuple):
        """Sauvegarde le graphe et les statistiques dans des fichiers de cache."""
        graph, positions, lines, terminus, branches = graph_data
        
        # Sauvegarder le graphe complet
        with open(self.graph_cache, 'wb') as f:
            pickle.dump(graph_data, f)
        
        # Sauvegarder les statistiques
        stats = {
            'stations': len(graph),
            'connections': sum(len(v) for v in graph.values()) // 2,
            'terminus': len(terminus),
            'lines': len(set().union(*[set(l) for l in lines.values()]))
        }
        with open(self.stats_cache, 'w') as f:
            json.dump(stats, f, indent=2)

    def _load_graph(self) -> Tuple:
        """Charge le graphe depuis le cache s'il existe."""
        if self.graph_cache.exists():
            with open(self.graph_cache, 'rb') as f:
                return pickle.load(f)
        return None

    def _time_to_seconds(self, time_str: str) -> int:
        """Convertit une chaîne de temps GTFS (HH:MM:SS) en secondes."""
        hours, minutes, seconds = map(int, time_str.split(':'))
        return hours * 3600 + minutes * 60 + seconds

    def build_metro_graph(self) -> Tuple[Dict[str, List[Tuple[str, int]]], Dict[str, Tuple[float, float]], Dict[str, List[str]], Set[str], Dict[str, int]]:
        """Construit le graphe du métro à partir des données GTFS avec optimisations."""
        start_time = time.time()
        
        # Essayer de charger depuis le cache
        cached_graph = self._load_graph()
        if cached_graph is not None:
            logger.info("Graphe chargé depuis le cache")
            return cached_graph
        
        logger.info("Construction du graphe depuis les données GTFS...")
        
        # Initialiser les structures de données
        graph = {name: set() for name in self.stop_name_to_ids}
        positions = self.stop_name_to_coords.copy()
        lines = {name: set() for name in self.stop_name_to_ids}
        terminus = set()
        
        # Optimisation 7: Traiter les trips par route pour réduire les calculs
        logger.info("Traitement des connexions par route...")
        
        total_routes = len(self.routes_df['route_id'])
        total_trips = len(self.trips_df)
        route_idx = 0
        trips_done = 0
        connexions_done = 0
        for route_id in self.routes_df['route_id']:
            route_idx += 1
            if route_idx % 2 == 0 or route_idx == total_routes:
                logger.info(f"Route {route_idx}/{total_routes} traitée...")
            route_name = self.route_names[route_id]
            route_trips = self.trips_df[self.trips_df['route_id'] == route_id]['trip_id']
            for trip_id in route_trips:
                trips_done += 1
                if trips_done % 500 == 0 or trips_done == total_trips:
                    logger.info(f"{trips_done}/{total_trips} trips traités...")
                # Récupérer les arrêts de ce trip
                if trip_id in self.stop_times_df.index:
                    trip_stops = self.stop_times_df.loc[trip_id].sort_values('stop_sequence')
                    if isinstance(trip_stops, pd.Series):
                        trip_stops = pd.DataFrame([trip_stops])
                    if len(trip_stops) < 2:
                        continue
                    for i in range(len(trip_stops) - 1):
                        current_stop = trip_stops.iloc[i]
                        next_stop = trip_stops.iloc[i+1]
                        
                        # Utiliser le nom principal de station si disponible
                        a = self.stop_id_to_main_station.get(current_stop['stop_id'], self.stop_id_to_name[current_stop['stop_id']])
                        b = self.stop_id_to_main_station.get(next_stop['stop_id'], self.stop_id_to_name[next_stop['stop_id']])
                        
                        if a != b:
                            current_time = self._time_to_seconds(current_stop['departure_time'])
                            next_time = self._time_to_seconds(next_stop['arrival_time'])
                            duration = next_time - current_time
                            if duration < 0:
                                duration += 24 * 3600
                            graph[a].add((b, duration))
                            graph[b].add((a, duration))
                            lines[a].add(route_name)
                            lines[b].add(route_name)
                            connexions_done += 1
                            if connexions_done % 10000 == 0:
                                logger.info(f"{connexions_done} connexions ajoutées...")
            if len(trip_stops) > 0:
                first_stop = self.stop_id_to_main_station.get(trip_stops.iloc[0]['stop_id'], self.stop_id_to_name[trip_stops.iloc[0]['stop_id']])
                last_stop = self.stop_id_to_main_station.get(trip_stops.iloc[-1]['stop_id'], self.stop_id_to_name[trip_stops.iloc[-1]['stop_id']])
                terminus.add(first_stop)
                terminus.add(last_stop)
        
        # Convertir les sets en listes et lignes en listes triées
        logger.info("Finalisation du graphe...")
        graph = {k: sorted(list(v)) for k, v in graph.items()}
        lines = {k: sorted(list(v)) for k, v in lines.items()}
        
        # Branches : à recalculer si besoin, sinon 0 partout
        branches = {k: 0 for k in graph}
        
        # Sauvegarder le graphe
        result = (graph, positions, lines, terminus, branches)
        self._save_graph(result)
        
        build_time = time.time() - start_time
        logger.info(f"Graphe construit en {build_time:.2f}s")
        
        logger.info(f"Nombre de sommets (stations) dans le graphe : {len(graph)}")
        
        return result

def parse_gtfs_to_graph(gtfs_dir: str) -> Tuple[Dict[str, List[Tuple[str, int]]], Dict[str, Tuple[float, float]], Dict[str, List[str]], Set[str], Dict[str, int]]:
    """Parse les données GTFS et retourne le graphe du métro."""
    parser = GTFSMetroParser(gtfs_dir)
    return parser.build_metro_graph() 