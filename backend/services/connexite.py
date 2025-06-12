from typing import Dict, Set, List
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

def test_connexite():
    """
    Fonction de test pour vérifier la connexité du graphe du métro.
    """
    checker = ConnexiteChecker()
    
    # Vérifier la connexité
    is_connected = checker.is_connected()
    
    # Afficher les résultats
    print("\n=== Test de connexité du graphe du métro ===")
    print(f"Le graphe est {'connexe' if is_connected else 'non connexe'}")
    
    if not is_connected:
        unreachable = checker.get_unreachable_stations()
        print(f"\nStations non accessibles ({len(unreachable)}):")
        for station_id in unreachable:
            station_name = checker.stations[station_id]['name']
            print(f"- {station_id}: {station_name}")
    
    # Statistiques
    print(f"\nStatistiques:")
    print(f"- Nombre total de stations: {len(checker.graph)}")
    print(f"- Nombre de stations visitées: {len(checker.visited)}")
    if not is_connected:
        print(f"- Nombre de stations non accessibles: {len(unreachable)}")

if __name__ == "__main__":
    test_connexite()
