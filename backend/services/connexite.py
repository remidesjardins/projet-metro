from typing import Dict, Set, List, Tuple
from utils.parser import load_data
import logging

class ConnexiteChecker:
    def __init__(self):
        self.graph, self.positions, self.stations = load_data()
        self.visited: Set[str] = set()
        
    def dfs(self, start_station: str) -> None:
        """
        Implémentation de l'algorithme DFS (Depth-First Search)
        pour parcourir le graphe à partir d'une station donnée.
        
        Args:
            start_station: ID de la station de départ
        """
        # Marquer la station actuelle comme visitée
        self.visited.add(start_station)
        
        # Parcourir récursivement tous les voisins non visités
        for neighbor in self.graph[start_station]:
            if neighbor not in self.visited:
                self.dfs(neighbor)
    
    def is_connected(self) -> bool:
        """
        Vérifie si le graphe est connexe en utilisant DFS.
        
        Returns:
            bool: True si le graphe est connexe, False sinon
        """
        # Réinitialiser l'ensemble des stations visitées
        self.visited.clear()
        
        # Choisir une station de départ arbitraire (la première du graphe)
        start_station = next(iter(self.graph))
        
        # Lancer DFS à partir de cette station
        self.dfs(start_station)
        
        # Le graphe est connexe si toutes les stations ont été visitées
        return len(self.visited) == len(self.graph)
    
    def get_unreachable_stations(self) -> List[str]:
        """
        Retourne la liste des stations qui ne sont pas accessibles
        à partir de la station de départ.
        
        Returns:
            List[str]: Liste des IDs des stations non accessibles
        """
        if self.is_connected():
            return []
        
        # Trouver toutes les stations non visitées
        all_stations = set(self.graph.keys())
        return list(all_stations - self.visited)

    def check_connexity_from_station(self, station_name: str) -> Tuple[bool, List[Dict[str, str]]]:
        """
        Vérifie la connexité du graphe à partir d'une station spécifique.
        
        Args:
            station_name: Nom de la station de départ
            
        Returns:
            Tuple contenant:
            - bool: True si toutes les stations sont accessibles depuis la station de départ
            - List[Dict]: Liste des stations non accessibles avec leurs détails
        """
        # Réinitialiser l'ensemble des stations visitées
        self.visited.clear()
        
        # Trouver l'ID de la station de départ
        start_station_id = None
        for station_id, station_data in self.stations.items():
            if station_data['name'] == station_name:
                start_station_id = station_id
                break
        
        if start_station_id is None:
            raise ValueError(f"Station '{station_name}' non trouvée")
        
        # Lancer DFS à partir de la station spécifiée
        self.dfs(start_station_id)
        
        # Vérifier si toutes les stations sont accessibles
        is_fully_connected = len(self.visited) == len(self.graph)
        
        # Si non connexe, préparer la liste des stations non accessibles
        unreachable_stations = []
        if not is_fully_connected:
            all_stations = set(self.graph.keys())
            unreachable_ids = all_stations - self.visited
            for station_id in unreachable_ids:
                station_data = self.stations[station_id]
                unreachable_stations.append({
                    'id': station_id,
                    'name': station_data['name'],
                    'line': station_data['line']
                })
        
        return is_fully_connected, unreachable_stations

def test_connexite():
    """
    Fonction de test pour vérifier la connexité du graphe du métro.
    """
    checker = ConnexiteChecker()
    
    # Vérifier la connexité
    is_connected = checker.is_connected()
    
    return is_connected, checker.get_unreachable_stations()

if __name__ == "__main__":
    is_connected, unreachable = test_connexite()
    print(f"Le graphe est {'connexe' if is_connected else 'non connexe'}")
    if not is_connected:
        print(f"Stations non accessibles: {len(unreachable)}")
