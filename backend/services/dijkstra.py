from utils.parser import load_data
import heapq
from typing import Dict, List, Tuple, Any

def dijkstra(graph, start, end):
    heap = [(0, start, [start])]
    visited = set()
    while heap:
        dist, current, path = heapq.heappop(heap)
        if current == end:
            return dist, path
        if current in visited:
            continue
        visited.add(current)
        for neighbor, weight in graph[current].items():
            if neighbor not in visited:
                heapq.heappush(heap, (dist + weight, neighbor, path + [neighbor]))
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
    graph, positions, stations = load_data()
    # Exemple : plus court chemin entre Abbesses (0000) et Bastille (0016)
    start_id = '0000'  # Abbesses
    end_id = '0016'    # Bastille
    print(f"Calcul du plus court chemin entre {stations[start_id]['name']} et {stations[end_id]['name']}...")
    dist, path = dijkstra(graph, start_id, end_id)
    if path:
        print(f"\nChemin trouvé :\n{print_path(path, stations)}")
        print(f"Durée totale : {dist} secondes (soit {dist/60:.1f} minutes)")
    else:
        print("Aucun chemin trouvé.")

if __name__ == "__main__":
    main()
