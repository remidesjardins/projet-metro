import os
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple
import pickle

logger = logging.getLogger(__name__)

class TransferService:
    """Service pour gérer les temps de transfert entre lignes de métro"""
    
    def __init__(self, gtfs_dir: str):
        self.gtfs_dir = gtfs_dir
        self.transfers = {}
        self.station_transfers = {}
        self.transfer_line_cache = {}
        self._load_transfers()
        self._load_transfer_line_cache()
    
    def _load_transfers(self):
        """Charge les données de transfert depuis transfers.txt"""
        logger.info("Chargement des données de transfert...")
        
        # Charger les stops pour avoir les mappings ID -> nom
        stops_file = os.path.join(self.gtfs_dir, 'stops.txt')
        if os.path.exists(stops_file):
            stops_df = pd.read_csv(
                stops_file,
                usecols=['stop_id', 'stop_name'],
                dtype={'stop_id': 'string', 'stop_name': 'string'}
            )
            stop_id_to_name = stops_df.set_index('stop_id')['stop_name'].to_dict()
        else:
            logger.warning("Fichier stops.txt non trouvé")
            return
        
        # Charger les transfers
        transfers_file = os.path.join(self.gtfs_dir, 'transfers.txt')
        if os.path.exists(transfers_file):
            transfers_df = pd.read_csv(
                transfers_file,
                usecols=['from_stop_id', 'to_stop_id', 'min_transfer_time'],
                dtype={'from_stop_id': 'string', 'to_stop_id': 'string', 'min_transfer_time': 'int32'}
            )
            
            # Créer les mappings de transfert
            for _, row in transfers_df.iterrows():
                from_name = stop_id_to_name.get(row['from_stop_id'])
                to_name = stop_id_to_name.get(row['to_stop_id'])
                
                if from_name and to_name:
                    # Mapping direct entre stations
                    self.transfers[(from_name, to_name)] = row['min_transfer_time']
                    
                    # Mapping par station pour les transferts entre lignes
                    if from_name not in self.station_transfers:
                        self.station_transfers[from_name] = {}
                    self.station_transfers[from_name][to_name] = row['min_transfer_time']
            
            logger.info(f"Transfers chargés: {len(self.transfers)} correspondances")
        else:
            logger.warning("Fichier transfers.txt non trouvé")
    
    def get_transfer_time(self, from_station: str, to_station: str) -> int:
        """
        Récupère le temps de transfert entre deux stations
        
        Args:
            from_station: Nom de la station de départ
            to_station: Nom de la station d'arrivée
        
        Returns:
            Temps de transfert en secondes, ou 0 si pas de transfert défini
        """
        return self.transfers.get((from_station, to_station), 0)
    
    def get_station_transfer_info(self, station: str) -> Dict:
        """
        Récupère toutes les informations de transfert pour une station
        
        Args:
            station: Nom de la station
        
        Returns:
            Dictionnaire avec les transferts possibles
        """
        return self.station_transfers.get(station, {})
    
    def _load_transfer_line_cache(self):
        """Charge ou génère le cache disque des temps de transfert entre lignes."""
        import hashlib
        import os
        cache_file = os.path.join(self.gtfs_dir, '..', 'cache', 'temporal', 'transfer_line_cache.pkl')
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        # Générer une clé de hash sur les fichiers GTFS pour l'invalidation
        hash_key = 'v1'
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                    if data.get('hash') == hash_key:
                        self.transfer_line_cache = data['cache']
                        logger.info(f"[TRANSFER] Cache des temps de transfert entre lignes chargé: {len(self.transfer_line_cache)} entrées")
                        return
            except Exception as e:
                logger.warning(f"[TRANSFER] Erreur chargement cache transfert lignes: {e}")
        # Sinon, générer le cache à partir des stops/lines connus
        logger.info("[TRANSFER] Génération du cache des temps de transfert entre lignes...")
        self.transfer_line_cache = {}
        # Nécessite gtfs_service pour les mappings, donc on ne pré-remplit que les cas simples ici
        # Le cache sera enrichi dynamiquement lors des appels
        with open(cache_file, 'wb') as f:
            pickle.dump({'hash': hash_key, 'cache': self.transfer_line_cache}, f)

    def save_transfer_line_cache(self):
        """Sauvegarde le cache disque."""
        import os
        cache_file = os.path.join(self.gtfs_dir, '..', 'cache', 'temporal', 'transfer_line_cache.pkl')
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, 'wb') as f:
            pickle.dump({'hash': 'v1', 'cache': self.transfer_line_cache}, f)

    def get_transfer_time_between_lines(self, station: str, from_line: str, to_line: str, gtfs_service=None) -> int:
        """
        Calcule le temps de transfert réel entre deux lignes dans une station à partir de transfers.txt
        Utilise un cache disque pour accélérer les appels répétés.
        """
        if from_line == to_line:
            return 0
        cache_key = (station, from_line, to_line)
        if cache_key in self.transfer_line_cache:
            return self.transfer_line_cache[cache_key]
        if gtfs_service is None:
            return 300
        
        # Obtenir tous les stop_ids de la station pour chaque ligne
        stop_ids_from = []
        stop_ids_to = []
        
        # Obtenir les route_ids
        route_id_from = gtfs_service.route_name_to_id.get(from_line)
        route_id_to = gtfs_service.route_name_to_id.get(to_line)
        
        if not route_id_from or not route_id_to:
            self.transfer_line_cache[cache_key] = 300
            self.save_transfer_line_cache()
            return 300
        
        # Obtenir les trips pour chaque ligne
        trips_from = gtfs_service.trips_df[gtfs_service.trips_df['route_id'] == route_id_from]
        trips_to = gtfs_service.trips_df[gtfs_service.trips_df['route_id'] == route_id_to]
        
        # Pour chaque stop_id de la station, vérifier s'il appartient à chaque ligne
        for stop_id in gtfs_service.stop_name_to_ids.get(station, []):
            # Vérifier ligne de départ
            for trip_id in trips_from['trip_id']:
                if trip_id in gtfs_service.stop_times_cache:
                    trip_stops = [s['stop_id'] for s in gtfs_service.stop_times_cache[trip_id]]
                    if stop_id in trip_stops:
                        stop_ids_from.append(stop_id)
                        break
            
            # Vérifier ligne d'arrivée
            for trip_id in trips_to['trip_id']:
                if trip_id in gtfs_service.stop_times_cache:
                    trip_stops = [s['stop_id'] for s in gtfs_service.stop_times_cache[trip_id]]
                    if stop_id in trip_stops:
                        stop_ids_to.append(stop_id)
                        break
        
        # Charger directement transfers.txt pour chercher les transferts
        transfers_file = os.path.join(self.gtfs_dir, 'transfers.txt')
        if not os.path.exists(transfers_file):
            self.transfer_line_cache[cache_key] = 300
            self.save_transfer_line_cache()
            return 300
        
        transfers_df = pd.read_csv(
            transfers_file,
            usecols=['from_stop_id', 'to_stop_id', 'min_transfer_time'],
            dtype={'from_stop_id': 'string', 'to_stop_id': 'string', 'min_transfer_time': 'int32'}
        )
        
        # Chercher le min_transfer_time entre les stop_ids des deux lignes
        transfer_times = []
        for from_id in stop_ids_from:
            for to_id in stop_ids_to:
                # Chercher dans transfers.txt
                matching_transfers = transfers_df[
                    (transfers_df['from_stop_id'] == from_id) & 
                    (transfers_df['to_stop_id'] == to_id)
                ]
                
                if not matching_transfers.empty:
                    transfer_time = int(matching_transfers.iloc[0]['min_transfer_time'])
                    transfer_times.append(transfer_time)
        
        if transfer_times:
            # Prendre le temps maximum entre les quais
            max_time = max(transfer_times)
            
            # Minimum de 3 minutes (180s) pour être réaliste
            realistic_time = max(max_time, 180)
            self.transfer_line_cache[cache_key] = realistic_time
            self.save_transfer_line_cache()
            return realistic_time
        
        self.transfer_line_cache[cache_key] = 300
        self.save_transfer_line_cache()
        return 300 