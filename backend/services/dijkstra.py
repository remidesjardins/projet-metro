from utils.parser import load_data
import heapq
from typing import Dict, List, Tuple, Any

def extract_weight(weight_data):
    """
    Extrait le poids numérique depuis le nouveau format de graphe.
    Le nouveau format est [{'time': X, 'line': Y}] au lieu d'un simple entier.
    """
    if isinstance(weight_data, list) and len(weight_data) > 0:
        if isinstance(weight_data[0], dict):
            return weight_data[0]['time']
        else:
            return weight_data[0]
    elif isinstance(weight_data, dict):
        return weight_data.get('time', 0)
    else:
        return weight_data

def dijkstra(graph, start, end):
    # Compatibilité : transformer la liste de tuples en dict si besoin
    def get_neighbors(node):
        neighbors = graph[node]
        if isinstance(neighbors, dict):
            return neighbors.items()
        # Si c'est une liste de tuples (neighbor, weight)
        return neighbors

    heap = [(0, start, [start])]
    visited = set()
    while heap:
        dist, current, path = heapq.heappop(heap)
        if current == end:
            return dist, path
        if current in visited:
            continue
        visited.add(current)
        for neighbor, weight in get_neighbors(current):
            if neighbor not in visited:
                # Extraire le poids numérique du nouveau format
                numeric_weight = extract_weight(weight)
                heapq.heappush(heap, (dist + numeric_weight, neighbor, path + [neighbor]))
    return float('inf'), []

def print_path(path, stations):
    return ' -> '.join([stations[station]['name'] for station in path])

def create_name_to_ids_mapping(stations: Dict[str, Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Crée un mapping des noms de stations vers leurs IDs.
    
    Args:
        stations: Dictionnaire des stations avec leurs informations
        
    Returns:
        Dictionnaire {nom_station: [liste_des_ids]}
    """
    name_to_ids = {}
    for station_id, station_data in stations.items():
        name = station_data['name']
        if name not in name_to_ids:
            name_to_ids[name] = []
        name_to_ids[name].append(station_id)
    return name_to_ids

def shortest_path_by_name(start_name: str, end_name: str) -> Tuple[List[str], int, str, str]:
    """
    Trouve le plus court chemin entre deux stations en tenant compte des correspondances.
    
    Args:
        start_name: Nom de la station de départ
        end_name: Nom de la station d'arrivée
        
    Returns:
        Tuple contenant:
        - Liste des IDs des stations formant le chemin
        - Distance totale en secondes
        - ID de la station de départ utilisée
        - ID de la station d'arrivée utilisée
    """
    graph, positions, stations = load_data()
    name_to_ids = create_name_to_ids_mapping(stations)
    
    # Vérifier que les stations existent
    if start_name not in name_to_ids:
        raise ValueError(f"Station de départ '{start_name}' non trouvée")
    if end_name not in name_to_ids:
        raise ValueError(f"Station d'arrivée '{end_name}' non trouvée")
    
    # Trouver le meilleur chemin parmi toutes les combinaisons possibles
    best_distance = float('inf')
    best_path = []
    best_start_id = None
    best_end_id = None
    
    for start_id in name_to_ids[start_name]:
        for end_id in name_to_ids[end_name]:
            distance, path = dijkstra(graph, start_id, end_id)
            if distance < best_distance:
                best_distance = distance
                best_path = path
                best_start_id = start_id
                best_end_id = end_id
    
    if best_path:
        return best_path, best_distance, best_start_id, best_end_id
    else:
        raise ValueError(f"Aucun chemin trouvé entre '{start_name}' et '{end_name}'")

def main():
    # Test de l'algorithme de Dijkstra
    graph, positions, stations = load_data()
    
    # Test avec des stations existantes
    start_station = '0000'  # Abbesses
    end_station = '0016'    # Bastille
    
    if start_station in graph and end_station in graph:
        dist, path = dijkstra(graph, start_station, end_station)
        
        if path:
            # Affichage des résultats (supprimé pour la production)
            # print(f"Chemin trouvé : {print_path(path, stations)}")
            # print(f"Durée totale : {dist} secondes (soit {dist/60:.1f} minutes)")
            pass
        else:
            # print("Aucun chemin trouvé.")
            pass

if __name__ == "__main__":
    main()
