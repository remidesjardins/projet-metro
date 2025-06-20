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

# Lignes de métro parisien (y compris 3B et 7B)
PARIS_METRO_LINES = [str(i) for i in range(1, 15)] + ['3B', '7B']

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
        
        # Filtrer pour ne garder que le métro parisien
        self.routes_df = self.routes_df[
            (self.routes_df['route_type'] == 1) & 
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
        
        # Optimisation 5: Créer des index pour accélérer les recherches
        logger.info("Création des index...")
        
        # FUSIONNER LES STATIONS PAR NOM (stop_name)
        self.stop_name_to_ids = self.stops_df.groupby('stop_name')['stop_id'].apply(list).to_dict()
        self.stop_id_to_name = self.stops_df.set_index('stop_id')['stop_name'].to_dict()
        self.stop_name_to_coords = self.stops_df.groupby('stop_name').agg({
            'stop_lat': 'mean', 
            'stop_lon': 'mean'
        }).apply(tuple, axis=1).to_dict()
        
        # Créer des dictionnaires pour un accès plus rapide
        self.route_names = self.routes_df.set_index('route_id')['route_short_name'].to_dict()
        self.trip_routes = self.trips_df.set_index('trip_id')['route_id'].to_dict()
        
        # Optimisation 6: Créer un index pour stop_times pour accélérer les recherches
        self.stop_times_df.set_index('trip_id', inplace=True)
        
        load_time = time.time() - start_time
        logger.info(f"Données GTFS chargées en {load_time:.2f}s")

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
        
        for route_id in self.routes_df['route_id']:
            route_name = self.route_names[route_id]
            route_trips = self.trips_df[self.trips_df['route_id'] == route_id]['trip_id']
            
            for trip_id in route_trips:
                # Récupérer les arrêts de ce trip
                if trip_id in self.stop_times_df.index:
                    trip_stops = self.stop_times_df.loc[trip_id].sort_values('stop_sequence')
        
                    # Si c'est un DataFrame avec une seule ligne, le convertir en Series
                    if isinstance(trip_stops, pd.Series):
                        trip_stops = pd.DataFrame([trip_stops])
                    
            if len(trip_stops) < 2:  # Ignorer les trajets avec moins de 2 arrêts
                continue
                
                    # Traiter les connexions consécutives
            for i in range(len(trip_stops) - 1):
                current_stop = trip_stops.iloc[i]
                next_stop = trip_stops.iloc[i+1]
                
                a = self.stop_id_to_name[current_stop['stop_id']]
                b = self.stop_id_to_name[next_stop['stop_id']]
                
                if a != b:
                    # Convertir les horaires en secondes
                    current_time = self._time_to_seconds(current_stop['departure_time'])
                    next_time = self._time_to_seconds(next_stop['arrival_time'])
                    
                    # Calculer la durée en secondes
                    duration = next_time - current_time
                    if duration < 0:  # Gérer le cas où on passe minuit
                        duration += 24 * 3600
                    
                    # Ajouter la connexion dans les deux sens avec la durée réelle
                    graph[a].add((b, duration))
                    graph[b].add((a, duration))
                            
                    # Ajouter la ligne aux deux stations
                    lines[a].add(route_name)
                    lines[b].add(route_name)
            
            # Marquer les terminus
            if len(trip_stops) > 0:
                first_stop = self.stop_id_to_name[trip_stops.iloc[0]['stop_id']]
                last_stop = self.stop_id_to_name[trip_stops.iloc[-1]['stop_id']]
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
        
        return result

def parse_gtfs_to_graph(gtfs_dir: str) -> Tuple[Dict[str, List[Tuple[str, int]]], Dict[str, Tuple[float, float]], Dict[str, List[str]], Set[str], Dict[str, int]]:
    """Parse les données GTFS et retourne le graphe du métro."""
    parser = GTFSMetroParser(gtfs_dir)
    return parser.build_metro_graph() 