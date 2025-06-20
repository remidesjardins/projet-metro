import logging
from typing import Dict, Tuple, Any
from pathlib import Path
from .gtfs_parser import parse_gtfs_to_graph
from .data_manager import DataManager

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_metro_file(file_path: str) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """
    Parse le fichier metro.txt et retourne les structures graph et stations.
    
    Args:
        file_path: Chemin vers le fichier metro.txt
        
    Returns:
        Tuple contenant (graph, stations)
    """
    graph = {}
    stations = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('-'):
                    continue
                if line.startswith('V'):
                    # V 0000 Abbesses ;12 ;False 0
                    # Séparer V et le reste
                    parts = line.split(' ', 2)
                    if len(parts) < 3:
                        continue
                    station_id = parts[1]
                    # Trouver le nom (avant le premier point-virgule)
                    rest = parts[2]
                    if ';' not in rest:
                        continue
                    name, after_name = rest.split(';', 1)
                    name = name.strip()
                    # Après le nom, il reste : numéro_ligne ;terminus branche
                    after_name = after_name.strip()
                    # On split sur ; pour ligne et terminus, puis sur espace pour branche
                    after_split = after_name.split(';')
                    if len(after_split) < 2:
                        continue
                    line_num = after_split[0].strip()
                    terminus_and_branche = after_split[1].strip().split()
                    if len(terminus_and_branche) < 2:
                        continue
                    terminus = terminus_and_branche[0].strip().lower() == 'true'
                    branche = int(terminus_and_branche[1].strip())
                    stations[station_id] = {
                        'name': name,
                        'line': line_num,
                        'terminus': terminus,
                        'branche': branche
                    }
                    graph[station_id] = {}
                elif line.startswith('E'):
                    # E 0 238 41
                    parts = line.split()
                    if len(parts) != 4:
                        continue
                    # Convertir les IDs en format 4 chiffres
                    station1 = parts[1].zfill(4)
                    station2 = parts[2].zfill(4)
                    time = int(parts[3])
                    if station1 in graph and station2 in graph:
                        graph[station1][station2] = time
                        graph[station2][station1] = time
    except FileNotFoundError:
        logger.error(f"Le fichier {file_path} n'a pas été trouvé")
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la lecture du fichier {file_path}: {str(e)}")
        raise
        
    return graph, stations

def parse_pospoints_file(file_path: str, stations: Dict[str, Dict]) -> Dict[str, Tuple[int, int]]:
    """
    Parse le fichier pospoints.txt et retourne un dictionnaire des positions des stations.
    Réutilise les positions pour les stations de correspondance.
    """
    positions = {}
    station_name_to_ids = {}
    
    # Créer un mapping nom de station -> liste d'IDs
    for station_id, station_data in stations.items():
        station_name = station_data['name']
        if station_name not in station_name_to_ids:
            station_name_to_ids[station_name] = []
        station_name_to_ids[station_name].append(station_id)
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                parts = line.split(';')
                if len(parts) != 3:
                    continue
                x, y, raw_name = parts
                try:
                    x = int(x)
                    y = int(y)
                except ValueError:
                    continue
                station_name = raw_name.replace('@', ' ')
                # On matche exactement le nom, mais on peut aussi essayer de matcher sans les virgules si besoin
                matched = False
                if station_name in station_name_to_ids:
                    for sid in station_name_to_ids[station_name]:
                        positions[sid] = (x, y)
                    matched = True
                else:
                    # Essayer de matcher en supprimant les virgules
                    alt_name = station_name.replace(',', '')
                    for name in station_name_to_ids:
                        if name.replace(',', '') == alt_name:
                            for sid in station_name_to_ids[name]:
                                positions[sid] = (x, y)
                            matched = True
                            break
                if not matched:
                    # On peut logger les noms non matchés si besoin
                    pass
    except FileNotFoundError:
        logging.error(f"Fichier {file_path} non trouvé")
        return {}
    except Exception as e:
        logging.error(f"Erreur lors de la lecture du fichier {file_path}: {str(e)}")
        return {}
    
    # Vérifier si toutes les stations ont une position
    stations_without_position = []
    for station_id in stations:
        if station_id not in positions:
            stations_without_position.append(f"{station_id}: {stations[station_id]['name']}")
    
    if stations_without_position:
        logging.warning(f"Nombre de stations différent entre metro.txt ({len(stations)}) et pospoints.txt ({len(positions)})")
        logging.warning("Stations sans position :")
        for station in stations_without_position:
            logging.warning(f"- {station}")
        
    return positions

def load_data() -> Tuple[Dict[str, Dict[str, int]], Dict[str, Tuple[int, int]], Dict[str, Dict[str, Any]]]:
    """
    Charge les données du métro en utilisant le DataManager pour optimiser les performances.
    Les données sont mises en cache et rechargées seulement si nécessaire.
    """
    return DataManager.get_data()

if __name__ == '__main__':
    # Test du chargement des données
    graph, positions, stations = load_data()
    
    # Affichage d'un exemple de station
    first_station_id = next(iter(stations))
    print(f"ID: {first_station_id}")
    print(f"Données: {stations[first_station_id]}")
    print(f"Position: {positions.get(first_station_id, 'Non trouvée')}")
    print(f"Voisins: {graph[first_station_id]}")
    
    # Statistiques générales
    print(f"Nombre total de stations : {len(stations)}")
    print(f"Nombre total de positions : {len(positions)}")
    print(f"Nombre total de connexions : {sum(len(neighbors) for neighbors in graph.values()) // 2}")
    print(f"Nombre de stations terminus : {sum(1 for station in stations.values() if station['terminus'])}")
    print(f"Nombre de stations avec branche : {sum(1 for station in stations.values() if station['branche'] > 0)}")
    
    # Vérification de cohérence
    print(f"Toutes les stations ont-elles une position ? : {all(station_id in positions for station_id in stations)}")
    print(f"Toutes les stations ont-elles des voisins ? : {all(len(neighbors) > 0 for neighbors in graph.values())}") 
    
    # Informations sur le cache
    cache_info = DataManager.get_cache_info()
    print(f"\nInformations sur le cache:")
    print(f"Cache chargé: {cache_info.get('cache_loaded', False)}")
    print(f"Données en mémoire: {cache_info.get('data_in_memory', False)}")
    print(f"Fichier de cache existe: {cache_info.get('cache_file_exists', False)}")
    if 'cache_size_mb' in cache_info:
        print(f"Taille du cache: {cache_info['cache_size_mb']:.2f} MB") 