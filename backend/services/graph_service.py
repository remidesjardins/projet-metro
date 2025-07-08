"""
MetroCity - Mastercamp 2025
Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
Fichier: graph_service.py
Description: Service de gestion du graphe de métro avec algorithmes de recherche de chemins
"""

import heapq
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class GraphService:
    """Service pour la gestion du graphe et la recherche de chemins multiples"""
    
    def __init__(self, graph: Dict, stations: Dict):
        self.graph = graph
        self.stations = stations
        self.name_to_ids = self._create_name_to_ids_mapping()
    
    def _create_name_to_ids_mapping(self) -> Dict[str, List[str]]:
        """Crée un mapping des noms de stations vers leurs IDs"""
        name_to_ids = defaultdict(list)
        for station_id, station_data in self.stations.items():
            name = station_data['name']
            name_to_ids[name].append(station_id)
        return dict(name_to_ids)
    
    def find_multiple_paths(
        self, 
        start_station: str, 
        end_station: str, 
        max_paths: int = None,
        max_path_length: int = 50  # Nombre max de stations par chemin
    ) -> List[List[Dict]]:
        """
        Trouve tous les chemins structurels entre deux stations si max_paths=None, sinon limite à max_paths
        """
        # Obtenir les IDs des stations
        start_ids = self.name_to_ids.get(start_station, [])
        end_ids = self.name_to_ids.get(end_station, [])
        
        if not start_ids or not end_ids:
            logger.warning(f"Stations non trouvées: {start_station} ou {end_station}")
            return []
        
        # Trouver tous les chemins possibles
        all_paths = []
        
        for start_id in start_ids:
            for end_id in end_ids:
                paths = self._find_paths_between_ids(
                    start_id, end_id, max_paths if max_paths is not None else 999999, max_path_length
                )
                all_paths.extend(paths)
        
        # Trier par coût total (incluant les pénalités de changement de ligne)
        unique_paths = self._deduplicate_paths(all_paths)
        # Tri déterministe : coût puis tuple des noms de stations
        unique_paths.sort(key=lambda p: (self._calculate_path_cost(p), tuple(seg['from_station'] for seg in p)))
        
        if max_paths is not None:
            return unique_paths[:max_paths]
        return unique_paths
    
    def _calculate_path_cost(self, path: List[Dict]) -> int:
        """
        Calcule le coût total d'un chemin en incluant une pénalité linéaire forte pour les changements de ligne
        """
        if not path:
            return 0
        base_cost = sum(seg['time'] for seg in path)
        # Pénalité linéaire forte pour les changements de ligne
        line_changes = 0
        current_line = path[0]['line']
        penalty = 0
        for segment in path[1:]:
            if segment['line'] != current_line:
                line_changes += 1
                # Pénalité linéaire forte : 600s par changement
                penalty += 600
                current_line = segment['line']
        return base_cost + penalty
    
    def _find_paths_between_ids(
        self, 
        start_id: str, 
        end_id: str, 
        max_paths: int,
        max_path_length: int
    ) -> List[List[Dict]]:
        """
        Trouve plusieurs chemins entre deux IDs de stations
        Utilise une variante de l'algorithme de Yen pour les k-plus courts chemins
        """
        # Trouver le chemin le plus court
        shortest_path = self._dijkstra_shortest_path(start_id, end_id)
        if not shortest_path:
            return []
        
        # Convertir en format de segments
        shortest_segments = self._path_to_segments(shortest_path)
        paths = [shortest_segments]
        
        # Trouver des chemins alternatifs
        for k in range(1, max_paths):
            alternative_path = self._find_alternative_path(
                start_id, end_id, paths, max_path_length
            )
            if alternative_path:
                paths.append(alternative_path)
            else:
                break
        
        return paths
    
    def _dijkstra_shortest_path(self, start_id: str, end_id: str) -> Optional[List[str]]:
        """Implémentation de Dijkstra pour trouver le plus court chemin avec pénalités de changement de ligne"""
        heap = [(0, start_id, [start_id], None)]  # (coût, station, chemin, ligne_actuelle)
        visited = set()
        
        while heap:
            dist, current, path, current_line = heapq.heappop(heap)
            
            if current == end_id:
                return path
            
            if current in visited:
                continue
            
            visited.add(current)
            
            # Explorer les voisins
            neighbors = self.graph.get(current, {})
            if isinstance(neighbors, dict):
                neighbor_items = neighbors.items()
            else:
                # Si c'est une liste de tuples (neighbor, weight)
                neighbor_items = neighbors
            
            for neighbor, weight_data in neighbor_items:
                # Extraire le poids du nouveau format
                if isinstance(weight_data, list) and weight_data:
                    weight = weight_data[0]['time']  # Prendre le premier temps disponible
                elif isinstance(weight_data, int):
                    weight = weight_data
                else:
                    continue  # Ignorer les formats invalides
                if neighbor not in visited:
                    # Déterminer la ligne vers ce voisin
                    next_line = self._determine_line(current, neighbor)
                    if not next_line:
                        continue
                    
                    # Calculer le coût avec pénalité de changement de ligne
                    transfer_penalty = 0
                    if current_line is not None and next_line != current_line:
                        # Pénalité de 5 minutes pour changement de ligne
                        transfer_penalty = 300  # 5 minutes = 300 secondes
                    
                    new_cost = dist + weight + transfer_penalty
                    new_path = path + [neighbor]
                    heapq.heappush(heap, (new_cost, neighbor, new_path, next_line))
        
        return None
    
    def _path_to_segments(self, path: List[str]) -> List[Dict]:
        """Convertit un chemin (liste d'IDs) en segments avec informations (corrigé)"""
        segments = []
        for i in range(len(path) - 1):
            current_id = path[i]
            next_id = path[i + 1]
            neighbors = self.graph.get(current_id, {})
            if isinstance(neighbors, dict):
                weight_data = neighbors.get(next_id, 0)
                # Extraire le poids du nouveau format
                if isinstance(weight_data, list) and weight_data:
                    weight = weight_data[0]['time']
                elif isinstance(weight_data, int):
                    weight = weight_data
                else:
                    weight = 0
            else:
                weight_item = next((w for n, w in neighbors if n == next_id), 0)
                if isinstance(weight_item, list) and weight_item:
                    weight = weight_item[0]['time']
                elif isinstance(weight_item, int):
                    weight = weight_item
                else:
                    weight = 0
            line = self._determine_line(current_id, next_id)
            if not line:
                continue  # ignorer les segments sans ligne valide
            segments.append({
                'from_station': self.stations[current_id]['name'],
                'to_station': self.stations[next_id]['name'],
                'from_id': current_id,
                'to_id': next_id,
                'line': line,
                'time': weight
            })
        return segments
    
    def _determine_line(self, from_id: str, to_id: str) -> str:
        """Détermine la ligne entre deux stations (corrigé pour GTFS)"""
        from_station = self.stations[from_id]
        to_station = self.stations[to_id]
        # Supporter 'line' (str) ou 'lines' (list)
        from_lines = set()
        to_lines = set()
        if 'lines' in from_station:
            from_lines = set(from_station['lines'])
        elif 'line' in from_station:
            if isinstance(from_station['line'], list):
                from_lines = set(from_station['line'])
            else:
                from_lines = set([from_station['line']])
        if 'lines' in to_station:
            to_lines = set(to_station['lines'])
        elif 'line' in to_station:
            if isinstance(to_station['line'], list):
                to_lines = set(to_station['line'])
            else:
                to_lines = set([to_station['line']])
        common_lines = from_lines & to_lines
        if common_lines:
            return list(common_lines)[0]
        # Si aucune ligne commune, logguer un avertissement et retourner None
        logger.warning(f"[GRAPH] Aucune ligne commune entre {from_station.get('name')} ({from_id}) et {to_station.get('name')} ({to_id})")
        return None
    
    def _find_alternative_path(
        self, 
        start_id: str, 
        end_id: str, 
        existing_paths: List[List[Dict]],
        max_path_length: int
    ) -> Optional[List[Dict]]:
        """
        Trouve un chemin alternatif en évitant les segments des chemins existants
        Utilise une approche de déviation
        """
        # Essayer de trouver un chemin en évitant certains segments
        for existing_path in existing_paths:
            # Essayer de dévier à chaque station du chemin existant
            for i, segment in enumerate(existing_path):
                deviation_point = segment['from_id']
                
                # Créer un graphe temporaire sans certains segments
                temp_graph = self._create_deviation_graph(existing_paths, deviation_point)
                
                # Chercher un chemin alternatif
                alt_path = self._dijkstra_shortest_path_with_graph(
                    start_id, end_id, temp_graph, max_path_length
                )
                
                if alt_path and len(alt_path) <= max_path_length:
                    return self._path_to_segments(alt_path)
        
        return None
    
    def _create_deviation_graph(
        self, 
        existing_paths: List[List[Dict]], 
        deviation_point: str
    ) -> Dict:
        """Crée un graphe temporaire pour la déviation"""
        # Copier le graphe original
        temp_graph = {k: dict(v) if isinstance(v, dict) else list(v) 
                     for k, v in self.graph.items()}
        
        # Supprimer certains segments des chemins existants
        for path in existing_paths:
            for segment in path:
                if segment['from_id'] == deviation_point:
                    # Supprimer cette connexion
                    if isinstance(temp_graph[segment['from_id']], dict):
                        temp_graph[segment['from_id']].pop(segment['to_id'], None)
                    else:
                        # Si c'est une liste de tuples
                        temp_graph[segment['from_id']] = [
                            (n, w) for n, w in temp_graph[segment['from_id']] 
                            if n != segment['to_id']
                        ]
        
        return temp_graph
    
    def _dijkstra_shortest_path_with_graph(
        self, 
        start_id: str, 
        end_id: str, 
        graph: Dict, 
        max_length: int
    ) -> Optional[List[str]]:
        """Dijkstra avec un graphe spécifique et limite de longueur, avec pénalités de changement de ligne"""
        heap = [(0, start_id, [start_id], None)]  # (coût, station, chemin, ligne_actuelle)
        visited = set()
        
        while heap:
            dist, current, path, current_line = heapq.heappop(heap)
            
            if current == end_id:
                return path
            
            if current in visited or len(path) > max_length:
                continue
            
            visited.add(current)
            
            neighbors = graph.get(current, {})
            if isinstance(neighbors, dict):
                neighbor_items = neighbors.items()
            else:
                neighbor_items = neighbors
            
            for neighbor, weight_data in neighbor_items:
                if neighbor not in visited:
                    # Extraire le poids du nouveau format
                    if isinstance(weight_data, list) and weight_data:
                        weight = weight_data[0]['time']  # Prendre le premier temps disponible
                    elif isinstance(weight_data, int):
                        weight = weight_data
                    else:
                        continue  # Ignorer les formats invalides
                    
                    # Déterminer la ligne vers ce voisin
                    next_line = self._determine_line(current, neighbor)
                    if not next_line:
                        continue
                    
                    # Calculer le coût avec pénalité de changement de ligne
                    transfer_penalty = 0
                    if current_line is not None and next_line != current_line:
                        # Pénalité de 5 minutes pour changement de ligne
                        transfer_penalty = 300  # 5 minutes = 300 secondes
                    
                    new_cost = dist + weight + transfer_penalty
                    new_path = path + [neighbor]
                    heapq.heappush(heap, (new_cost, neighbor, new_path, next_line))
        
        return None
    
    def _deduplicate_paths(self, paths: List[List[Dict]]) -> List[List[Dict]]:
        """Supprime les chemins dupliqués et les trie de façon déterministe"""
        unique_paths = []
        seen_paths = set()
        for path in paths:
            # Clé unique déterministe : tuple trié des (from_station, to_station, line)
            path_key = tuple((seg['from_station'], seg['to_station'], seg['line']) for seg in path)
            if path_key not in seen_paths:
                seen_paths.add(path_key)
                unique_paths.append(path)
        # Tri déterministe par coût puis noms de stations
        unique_paths.sort(key=lambda p: (self._calculate_path_cost(p), tuple(seg['from_station'] for seg in p)))
        return unique_paths
    
    def get_station_info(self, station_name: str) -> Optional[Dict]:
        """Récupère les informations d'une station"""
        station_ids = self.name_to_ids.get(station_name, [])
        if station_ids:
            return self.stations[station_ids[0]]
        return None
    
    def get_all_stations(self) -> List[str]:
        """Retourne la liste de toutes les stations"""
        return list(self.name_to_ids.keys()) 