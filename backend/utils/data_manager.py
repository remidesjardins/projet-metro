import logging
import time
import pickle
import gzip
from pathlib import Path
from typing import Dict, Tuple, Any, Optional
from .gtfs_parser import parse_gtfs_to_graph

logger = logging.getLogger(__name__)

class DataManager:
    """
    Singleton pour gérer le cache global des données du métro.
    Charge les données une seule fois et les met en cache pour un accès rapide.
    """
    _instance = None
    _data = None
    _cache_file = None
    _last_load_time = None
    _cache_loaded = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialise le gestionnaire de données."""
        self._cache_file = Path(__file__).parent.parent / 'data' / 'cache' / 'global_data.pkl.gz'
        self._cache_file.parent.mkdir(exist_ok=True)
    
    @classmethod
    def get_data(cls) -> Tuple[Dict[str, Dict[str, int]], Dict[str, Tuple[int, int]], Dict[str, Dict[str, Any]]]:
        """
        Retourne les données du métro (graph, positions, stations).
        Charge depuis le cache si disponible, sinon depuis les données GTFS.
        """
        instance = cls()
        
        # Si les données sont déjà en mémoire, les retourner
        if instance._data is not None:
            return instance._data
        
        # Essayer de charger depuis le cache
        if instance._load_from_cache():
            logger.info(f"Données chargées depuis le cache en {time.time() - instance._last_load_time:.3f}s")
            return instance._data
        
        # Charger depuis les données GTFS et mettre en cache
        logger.info("Chargement des données depuis les fichiers GTFS...")
        start_time = time.time()
        
        instance._data = instance._load_from_gtfs()
        instance._save_to_cache()
        instance._cache_loaded = True
        
        load_time = time.time() - start_time
        logger.info(f"Données GTFS chargées et mises en cache en {load_time:.3f}s")
        
        return instance._data
    
    def _load_from_gtfs(self) -> Tuple[Dict[str, Dict[str, int]], Dict[str, Tuple[int, int]], Dict[str, Dict[str, Any]]]:
        """
        Charge les données depuis les fichiers GTFS et les convertit au format attendu.
        """
        data_dir = Path(__file__).parent.parent / 'data' / 'gtfs'
        
        # Charger le graphe, les positions, les lignes, les terminus et les branches depuis les données GTFS
        gtfs_graph, gtfs_positions, gtfs_lines, gtfs_terminus, gtfs_branches = parse_gtfs_to_graph(str(data_dir), parallel=True)
        
        # Convertir le graphe GTFS dans le format attendu
        graph = {}
        stations = {}
        positions = {}
        
        # Créer un ID unique pour chaque station
        station_id_counter = 0
        station_name_to_id = {}
        
        # Parcourir le graphe GTFS pour créer les structures de données
        for station_name, neighbors in gtfs_graph.items():
            # Créer un ID unique pour la station si elle n'existe pas déjà
            if station_name not in station_name_to_id:
                station_id = str(station_id_counter).zfill(4)
                station_id_counter += 1
                station_name_to_id[station_name] = station_id
                
                # Créer l'entrée dans stations
                stations[station_id] = {
                    'name': station_name,
                    'line': gtfs_lines.get(station_name, '1'),
                    'types': ['metro'],  # Par défaut, toutes les stations sont de type métro
                    'terminus': station_name in gtfs_terminus,
                    'branche': gtfs_branches.get(station_name, 0)
                }
                
                # Créer l'entrée dans le graphe
                graph[station_id] = {}
                
                # Utiliser les coordonnées GTFS (longitude, latitude)
                if station_name in gtfs_positions:
                    lon, lat = gtfs_positions[station_name]
                    # Convertir en float Python standard pour la sérialisation JSON
                    positions[station_id] = (float(lon), float(lat))
                else:
                    positions[station_id] = (0.0, 0.0)
            
            station_id = station_name_to_id[station_name]
            
            # Ajouter les connexions au graphe
            for neighbor_name, weight in neighbors:
                if neighbor_name not in station_name_to_id:
                    neighbor_id = str(station_id_counter).zfill(4)
                    station_id_counter += 1
                    station_name_to_id[neighbor_name] = neighbor_id
                    
                    stations[neighbor_id] = {
                        'name': neighbor_name,
                        'line': gtfs_lines.get(neighbor_name, '1'),
                        'types': ['metro'],  # Par défaut, toutes les stations sont de type métro
                        'terminus': neighbor_name in gtfs_terminus,
                        'branche': gtfs_branches.get(neighbor_name, 0)
                    }
                    graph[neighbor_id] = {}
                    
                    # Utiliser les coordonnées GTFS (longitude, latitude)
                    if neighbor_name in gtfs_positions:
                        lon, lat = gtfs_positions[neighbor_name]
                        # Convertir en float Python standard pour la sérialisation JSON
                        positions[neighbor_id] = (float(lon), float(lat))
                    else:
                        positions[neighbor_id] = (0.0, 0.0)
                
                neighbor_id = station_name_to_id[neighbor_name]
                
                # Préserver les informations de ligne dans le graphe
                line = gtfs_lines.get(station_name, '1')
                if neighbor_id not in graph[station_id]:
                    graph[station_id][neighbor_id] = []
                
                # Ajouter la connexion avec les informations de ligne
                connection = {
                    'time': weight,
                    'line': line
                }
                graph[station_id][neighbor_id].append(connection)
        
        # Correction manuelle de la topologie de la 7B (relations exactes)
        def find_station_id(nom, ligne):
            for sid, s in stations.items():
                lines = s['line'] if isinstance(s['line'], list) else [s['line']]
                if s['name'] == nom and ligne in lines:
                    return sid
            return None
        id_place = find_station_id('Place des Fêtes', '7B')
        id_pre = find_station_id('Pré-Saint-Gervais', '7B')
        id_botz = find_station_id('Botzaris', '7B')
        id_danube = find_station_id('Danube', '7B')
        # Supprimer tous les liens existants entre ces stations (pour éviter les doublons ou cycles)
        for a, b in [(id_place, id_pre), (id_place, id_danube), (id_botz, id_pre), (id_botz, id_danube), (id_place, id_botz), (id_pre, id_danube)]:
            if a and b and b in graph[a]:
                del graph[a][b]
            if a and b and a in graph[b]:
                del graph[b][a]
        # Ajouter Botzaris <-> Place des Fêtes <-> Pré-Saint-Gervais
        if id_botz and id_place:
            if id_place not in graph[id_botz]:
                graph[id_botz][id_place] = []
            if id_botz not in graph[id_place]:
                graph[id_place][id_botz] = []
            graph[id_botz][id_place].append({'time': 60, 'line': '7B'})
            graph[id_place][id_botz].append({'time': 60, 'line': '7B'})
        if id_place and id_pre:
            if id_pre not in graph[id_place]:
                graph[id_place][id_pre] = []
            if id_place not in graph[id_pre]:
                graph[id_pre][id_place] = []
            graph[id_place][id_pre].append({'time': 60, 'line': '7B'})
            graph[id_pre][id_place].append({'time': 60, 'line': '7B'})
        # Ajouter Pré-Saint-Gervais <-> Danube <-> Botzaris
        if id_pre and id_danube:
            if id_danube not in graph[id_pre]:
                graph[id_pre][id_danube] = []
            if id_pre not in graph[id_danube]:
                graph[id_danube][id_pre] = []
            graph[id_pre][id_danube].append({'time': 60, 'line': '7B'})
            graph[id_danube][id_pre].append({'time': 60, 'line': '7B'})
        # FORCER le lien Danube <-> Botzaris à la toute fin
        if id_danube and id_botz:
            if id_botz not in graph[id_danube]:
                graph[id_danube][id_botz] = []
            if id_danube not in graph[id_botz]:
                graph[id_botz][id_danube] = []
            graph[id_danube][id_botz].append({'time': 60, 'line': '7B'})
            graph[id_botz][id_danube].append({'time': 60, 'line': '7B'})
        
        return graph, positions, stations
    
    def _save_to_cache(self):
        """Sauvegarde les données en cache compressé."""
        try:
            with gzip.open(self._cache_file, 'wb') as f:
                pickle.dump(self._data, f)
            logger.info(f"Données sauvegardées en cache: {self._cache_file}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du cache: {e}")
    
    def _load_from_cache(self) -> bool:
        """
        Charge les données depuis le cache.
        Retourne True si le chargement a réussi, False sinon.
        """
        try:
            if not self._cache_file.exists():
                logger.info("Fichier de cache non trouvé")
                return False
            
            start_time = time.time()
            with gzip.open(self._cache_file, 'rb') as f:
                self._data = pickle.load(f)
            
            self._last_load_time = start_time
            self._cache_loaded = True
            
            # Vérifier que les données sont valides
            if not isinstance(self._data, tuple) or len(self._data) != 3:
                logger.warning("Format de cache invalide")
                return False
            
            graph, positions, stations = self._data
            logger.info(f"Cache chargé: {len(stations)} stations, {sum(len(v) for v in graph.values()) // 2} connexions")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement du cache: {e}")
            return False
    
    @classmethod
    def clear_cache(cls):
        """Efface le cache et force un rechargement des données."""
        instance = cls()
        instance._data = None
        instance._cache_loaded = False
        if instance._cache_file and instance._cache_file.exists():
            instance._cache_file.unlink()
            logger.info("Cache effacé")
    
    @classmethod
    def get_cache_info(cls) -> Dict[str, Any]:
        """Retourne des informations sur l'état du cache."""
        instance = cls()
        info = {
            'cache_loaded': instance._cache_loaded,
            'data_in_memory': instance._data is not None,
            'cache_file_exists': instance._cache_file.exists() if instance._cache_file else False
        }
        
        if instance._cache_file and instance._cache_file.exists():
            info['cache_size_mb'] = instance._cache_file.stat().st_size / (1024 * 1024)
        
        if instance._data is not None:
            graph, positions, stations = instance._data
            info['stations_count'] = len(stations)
            info['connections_count'] = sum(len(v) for v in graph.values()) // 2
        
        return info 