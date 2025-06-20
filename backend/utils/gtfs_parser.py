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
        """Charge les données GTFS depuis les fichiers source."""
        start_time = time.time()
        
        # Charger les routes et filtrer pour ne garder que le métro parisien
        self.routes_df = pd.read_csv(
            os.path.join(self.gtfs_dir, 'routes.txt'),
            usecols=['route_id', 'route_short_name', 'route_type'],
            low_memory=False
        )
        self.routes_df = self.routes_df[(self.routes_df['route_type'] == 1) & (self.routes_df['route_short_name'].isin(PARIS_METRO_LINES))]
        
        # Charger les trips pour les routes de métro
        self.trips_df = pd.read_csv(
            os.path.join(self.gtfs_dir, 'trips.txt'),
            usecols=['trip_id', 'route_id'],
            low_memory=False
        )
        self.trips_df = self.trips_df[self.trips_df['route_id'].isin(self.routes_df['route_id'])]
        
        # Charger les stop_times pour les trips de métro
        self.stop_times_df = pd.read_csv(
            os.path.join(self.gtfs_dir, 'stop_times.txt'),
            usecols=['trip_id', 'stop_id', 'stop_sequence', 'departure_time', 'arrival_time'],
            low_memory=False,
            quoting=1  # QUOTE_ALL pour gérer les virgules dans les en-têtes
        )
        self.stop_times_df = self.stop_times_df[self.stop_times_df['trip_id'].isin(self.trips_df['trip_id'])]
        
        # Charger les stops pour les arrêts utilisés
        used_stop_ids = set(self.stop_times_df['stop_id'].unique())
        self.stops_df = pd.read_csv(
            os.path.join(self.gtfs_dir, 'stops.txt'),
            usecols=['stop_id', 'stop_name', 'stop_lat', 'stop_lon'],
            low_memory=False
        )
        self.stops_df = self.stops_df[self.stops_df['stop_id'].isin(used_stop_ids)]
        
        # FUSIONNER LES STATIONS PAR NOM (stop_name)
        self.stop_name_to_ids = self.stops_df.groupby('stop_name')['stop_id'].apply(list).to_dict()
        self.stop_id_to_name = self.stops_df.set_index('stop_id')['stop_name'].to_dict()
        self.stop_name_to_coords = self.stops_df.groupby('stop_name').agg({'stop_lat': 'mean', 'stop_lon': 'mean'}).apply(tuple, axis=1).to_dict()
        
        # Créer des dictionnaires pour un accès plus rapide
        self.route_names = self.routes_df.set_index('route_id')['route_short_name'].to_dict()
        self.trip_routes = self.trips_df.set_index('trip_id')['route_id'].to_dict()

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
        """Construit le graphe du métro à partir des données GTFS."""
        start_time = time.time()
        
        # Essayer de charger depuis le cache
        cached_graph = self._load_graph()
        if cached_graph is not None:
            return cached_graph
        
        # Initialiser les structures de données
        graph = {name: set() for name in self.stop_name_to_ids}
        positions = self.stop_name_to_coords.copy()
        lines = {name: set() for name in self.stop_name_to_ids}
        terminus = set()
        
        # Pré-calculer les connexions par trip pour éviter les recalculs
        trip_connections = {}
        total_trips = len(self.trips_df['trip_id'].unique())
        
        for i, trip_id in enumerate(self.trips_df['trip_id'].unique()):
            trip_stops = self.stop_times_df[self.stop_times_df['trip_id'] == trip_id].sort_values('stop_sequence')
            if len(trip_stops) < 2:  # Ignorer les trajets avec moins de 2 arrêts
                continue
                
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
                    lines[a].add(self.route_names[self.trip_routes[trip_id]])
                    lines[b].add(self.route_names[self.trip_routes[trip_id]])
            
            # Marquer les terminus
            if len(trip_stops) > 0:
                first_stop = self.stop_id_to_name[trip_stops.iloc[0]['stop_id']]
                last_stop = self.stop_id_to_name[trip_stops.iloc[-1]['stop_id']]
                terminus.add(first_stop)
                terminus.add(last_stop)
        
        # Construire le graphe en utilisant les connexions pré-calculées
        for i, (trip_id, stop_names) in enumerate(trip_connections.items()):
            route_id = self.trip_routes[trip_id]
            route_name = self.route_names[route_id]
            
            # Ajouter les connexions entre stations consécutives
            trip_stops = self.stop_times_df[self.stop_times_df['trip_id'] == trip_id].sort_values('stop_sequence')
            if len(trip_stops) < 2:  # Ignorer les trajets avec moins de 2 arrêts
                continue
                
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
        graph = {k: sorted(list(v)) for k, v in graph.items()}
        lines = {k: sorted(list(v)) for k, v in lines.items()}
        
        # Branches : à recalculer si besoin, sinon 0 partout
        branches = {k: 0 for k in graph}
        
        # Sauvegarder le graphe
        result = (graph, positions, lines, terminus, branches)
        self._save_graph(result)
        
        return result

def parse_gtfs_to_graph(gtfs_dir: str) -> Tuple[Dict[str, List[Tuple[str, int]]], Dict[str, Tuple[float, float]], Dict[str, List[str]], Set[str], Dict[str, int]]:
    """Parse les données GTFS et retourne le graphe du métro."""
    parser = GTFSMetroParser(gtfs_dir)
    return parser.build_metro_graph() 