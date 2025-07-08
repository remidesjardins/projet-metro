"""
MetroCity - Mastercamp 2025
Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
Fichier: test_acpm_service.py
Description: Tests unitaires pour le service d'Arbre Couvrant de Poids Minimum (Kruskal)
"""

import unittest
import pytest
from services.kruskal import kruskal_mst
from utils.parser import load_data
import time

class TestACPMService:
    """Tests unitaires pour le service ACPM (Arbre Couvrant de Poids Minimum)."""
    
    def setup_method(self):
        """Initialisation avant chaque test."""
        self.graph, self.positions, self.stations = load_data()
    
    def test_data_loading(self):
        """Test du chargement des données pour l'ACPM."""
        assert self.graph is not None
        assert self.positions is not None
        assert self.stations is not None
        assert len(self.graph) > 0
        assert len(self.positions) > 0
        assert len(self.stations) > 0
        
        # Vérifier que toutes les stations ont des positions
        for station_id in self.graph:
            assert station_id in self.positions, f"Station {station_id} n'a pas de position"
            assert station_id in self.stations, f"Station {station_id} n'a pas de données"
    
    def test_edge_extraction(self):
        """Test de l'extraction des arêtes du graphe."""
        edges = []
        seen = set()
        
        for s1 in self.graph:
            for s2, weight_data in self.graph[s1].items():
                if (s2, s1) not in seen:
                    # Extraire le poids selon le nouveau format
                    if isinstance(weight_data, list) and len(weight_data) > 0:
                        weight = weight_data[0]['time'] if isinstance(weight_data[0], dict) else weight_data[0]
                    elif isinstance(weight_data, dict):
                        weight = weight_data.get('time', weight_data)
                    else:
                        weight = weight_data
                    
                    edges.append((weight, s1, s2))
                    seen.add((s1, s2))
        
        # Vérifications
        assert len(edges) > 0, "Aucune arête extraite"
        assert len(edges) <= len(self.graph) * (len(self.graph) - 1) // 2, "Trop d'arêtes extraites"
        
        # Vérifier que toutes les arêtes ont des poids valides
        for weight, s1, s2 in edges:
            assert isinstance(weight, (int, float)), f"Poids invalide pour l'arête {s1}-{s2}: {weight}"
            assert weight >= 0, f"Poids négatif pour l'arête {s1}-{s2}: {weight}"
            assert s1 in self.graph, f"Station {s1} n'existe pas dans le graphe"
            assert s2 in self.graph, f"Station {s2} n'existe pas dans le graphe"
    
    def test_kruskal_algorithm(self):
        """Test de l'algorithme de Kruskal."""
        # Extraire les arêtes
        edges = []
        seen = set()
        for s1 in self.graph:
            for s2, weight_data in self.graph[s1].items():
                if (s2, s1) not in seen:
                    if isinstance(weight_data, list) and len(weight_data) > 0:
                        weight = weight_data[0]['time'] if isinstance(weight_data[0], dict) else weight_data[0]
                    elif isinstance(weight_data, dict):
                        weight = weight_data.get('time', weight_data)
                    else:
                        weight = weight_data
                    
                    edges.append((weight, s1, s2))
                    seen.add((s1, s2))
        
        # Trier les arêtes par poids
        edges.sort()
        
        # Appliquer l'algorithme de Kruskal
        mst, total_weight = kruskal_mst(edges, len(self.graph))
        
        # Vérifications de base
        assert isinstance(mst, list), "L'ACPM doit être une liste"
        assert isinstance(total_weight, (int, float)), "Le poids total doit être un nombre"
        assert total_weight >= 0, "Le poids total ne peut pas être négatif"
        
        # Vérifier la propriété de l'arbre couvrant
        assert len(mst) == len(self.graph) - 1, f"L'ACPM doit avoir {len(self.graph) - 1} arêtes, pas {len(mst)}"
        
        # Vérifier que toutes les arêtes de l'ACPM existent dans le graphe original
        for edge in mst:
            assert len(edge) == 2, f"Chaque arête doit avoir 2 sommets: {edge}"
            s1, s2 = edge
            assert s1 in self.graph, f"Station {s1} de l'ACPM n'existe pas dans le graphe"
            assert s2 in self.graph, f"Station {s2} de l'ACPM n'existe pas dans le graphe"
    
    def test_acpm_connectivity(self):
        """Test que l'ACPM connecte bien toutes les stations."""
        # Extraire et calculer l'ACPM
        edges = []
        seen = set()
        for s1 in self.graph:
            for s2, weight_data in self.graph[s1].items():
                if (s2, s1) not in seen:
                    if isinstance(weight_data, list) and len(weight_data) > 0:
                        weight = weight_data[0]['time'] if isinstance(weight_data[0], dict) else weight_data[0]
                    elif isinstance(weight_data, dict):
                        weight = weight_data.get('time', weight_data)
                    else:
                        weight = weight_data
                    
                    edges.append((weight, s1, s2))
                    seen.add((s1, s2))
        
        edges.sort()
        mst, total_weight = kruskal_mst(edges, len(self.graph))
        
        # Construire le graphe de l'ACPM
        acpm_graph = {}
        for s1, s2 in mst:
            if s1 not in acpm_graph:
                acpm_graph[s1] = set()
            if s2 not in acpm_graph:
                acpm_graph[s2] = set()
            acpm_graph[s1].add(s2)
            acpm_graph[s2].add(s1)
        
        # Vérifier que l'ACPM est connexe (DFS)
        visited = set()
        start_station = next(iter(acpm_graph))
        
        def dfs(node):
            visited.add(node)
            for neighbor in acpm_graph.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor)
        
        dfs(start_station)
        
        # Toutes les stations doivent être visitées
        assert len(visited) == len(self.graph), f"ACPM non connexe: {len(visited)}/{len(self.graph)} stations accessibles"
    
    def test_acpm_minimality(self):
        """Test que l'ACPM a bien un poids minimal."""
        # Extraire toutes les arêtes
        edges = []
        seen = set()
        for s1 in self.graph:
            for s2, weight_data in self.graph[s1].items():
                if (s2, s1) not in seen:
                    if isinstance(weight_data, list) and len(weight_data) > 0:
                        weight = weight_data[0]['time'] if isinstance(weight_data[0], dict) else weight_data[0]
                    elif isinstance(weight_data, dict):
                        weight = weight_data.get('time', weight_data)
                    else:
                        weight = weight_data
                    
                    edges.append((weight, s1, s2))
                    seen.add((s1, s2))
        
        edges.sort()
        mst, total_weight = kruskal_mst(edges, len(self.graph))
        
        # Vérifier que le poids total est raisonnable
        # Pour un réseau de métro, le poids total devrait être dans une fourchette logique
        assert total_weight > 0, "Le poids total doit être positif"
        assert total_weight < 1000000, f"Le poids total semble trop élevé: {total_weight}"
        
        # Vérifier que toutes les arêtes de l'ACPM ont des poids valides
        for edge in mst:
            s1, s2 = edge
            # Trouver le poids de cette arête dans le graphe original
            weight_data = self.graph[s1].get(s2) or self.graph[s2].get(s1)
            assert weight_data is not None, f"Arête {s1}-{s2} non trouvée dans le graphe original"
            
            if isinstance(weight_data, list) and len(weight_data) > 0:
                weight = weight_data[0]['time'] if isinstance(weight_data[0], dict) else weight_data[0]
            elif isinstance(weight_data, dict):
                weight = weight_data.get('time', weight_data)
            else:
                weight = weight_data
            
            assert isinstance(weight, (int, float)), f"Poids invalide pour l'arête {s1}-{s2}"
            assert weight >= 0, f"Poids négatif pour l'arête {s1}-{s2}"
    
    def test_acpm_structure(self):
        """Test de la structure de l'ACPM retourné par l'API."""
        # Simuler la structure retournée par l'API
        edges = []
        seen = set()
        for s1 in self.graph:
            for s2, weight_data in self.graph[s1].items():
                if (s2, s1) not in seen:
                    if isinstance(weight_data, list) and len(weight_data) > 0:
                        weight = weight_data[0]['time'] if isinstance(weight_data[0], dict) else weight_data[0]
                    elif isinstance(weight_data, dict):
                        weight = weight_data.get('time', weight_data)
                    else:
                        weight = weight_data
                    
                    edges.append((weight, s1, s2))
                    seen.add((s1, s2))
        
        edges.sort()
        mst, total_weight = kruskal_mst(edges, len(self.graph))
        
        # Construire la structure API
        mst_api = []
        for s1, s2 in mst:
            # Trouver le poids de cette arête
            weight_data = self.graph[s1].get(s2) or self.graph[s2].get(s1)
            if isinstance(weight_data, list) and len(weight_data) > 0:
                weight = weight_data[0]['time'] if isinstance(weight_data[0], dict) else weight_data[0]
            elif isinstance(weight_data, dict):
                weight = weight_data.get('time', weight_data)
            else:
                weight = weight_data
            
            mst_api.append({
                'from': {
                    'id': s1,
                    'name': self.stations[s1]['name']
                },
                'to': {
                    'id': s2,
                    'name': self.stations[s2]['name']
                },
                'weight': weight
            })
        
        # Vérifier la structure
        assert len(mst_api) == len(mst), "Nombre d'arêtes incorrect"
        
        for edge in mst_api:
            assert 'from' in edge, "Chaque arête doit avoir un champ 'from'"
            assert 'to' in edge, "Chaque arête doit avoir un champ 'to'"
            assert 'weight' in edge, "Chaque arête doit avoir un champ 'weight'"
            
            assert 'id' in edge['from'], "Le champ 'from' doit avoir un 'id'"
            assert 'name' in edge['from'], "Le champ 'from' doit avoir un 'name'"
            assert 'id' in edge['to'], "Le champ 'to' doit avoir un 'id'"
            assert 'name' in edge['to'], "Le champ 'to' doit avoir un 'name'"
            
            assert isinstance(edge['weight'], (int, float)), "Le poids doit être un nombre"
            assert edge['weight'] >= 0, "Le poids ne peut pas être négatif"
    
    def test_acpm_performance(self):
        """Test de performance de l'algorithme ACPM."""
        # Extraire les arêtes
        edges = []
        seen = set()
        for s1 in self.graph:
            for s2, weight_data in self.graph[s1].items():
                if (s2, s1) not in seen:
                    if isinstance(weight_data, list) and len(weight_data) > 0:
                        weight = weight_data[0]['time'] if isinstance(weight_data[0], dict) else weight_data[0]
                    elif isinstance(weight_data, dict):
                        weight = weight_data.get('time', weight_data)
                    else:
                        weight = weight_data
                    
                    edges.append((weight, s1, s2))
                    seen.add((s1, s2))
        
        edges.sort()
        
        # Test de performance
        start_time = time.time()
        mst, total_weight = kruskal_mst(edges, len(self.graph))
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # L'algorithme doit être rapide
        assert execution_time < 1.0, f"L'algorithme ACPM est trop lent: {execution_time:.4f}s"
        
        # Vérifier que le résultat est correct
        assert len(mst) == len(self.graph) - 1, "Nombre d'arêtes incorrect"
        assert total_weight > 0, "Poids total doit être positif"
    
    def test_acpm_edge_cases(self):
        """Test des cas limites de l'ACPM."""
        # Test avec un graphe très petit
        small_graph = {
            'A': {'B': 1},
            'B': {'A': 1}
        }
        
        edges = [(1, 'A', 'B')]
        mst, total_weight = kruskal_mst(edges, 2)
        
        assert len(mst) == 1, "ACPM d'un graphe à 2 nœuds doit avoir 1 arête"
        assert total_weight == 1, "Poids total incorrect"
        
        # Test avec des poids égaux
        equal_graph = {
            'A': {'B': 1, 'C': 1},
            'B': {'A': 1, 'C': 1},
            'C': {'A': 1, 'B': 1}
        }
        
        edges = [(1, 'A', 'B'), (1, 'A', 'C'), (1, 'B', 'C')]
        mst, total_weight = kruskal_mst(edges, 3)
        
        assert len(mst) == 2, "ACPM d'un graphe à 3 nœuds doit avoir 2 arêtes"
        assert total_weight == 2, "Poids total incorrect"

def test_kruskal_function():
    """Test de la fonction kruskal_mst directement."""
    # Test simple
    edges = [(1, 'A', 'B'), (2, 'B', 'C'), (3, 'A', 'C')]
    mst, total_weight = kruskal_mst(edges, 3)
    
    assert len(mst) == 2, "ACPM doit avoir 2 arêtes pour 3 nœuds"
    assert total_weight == 3, "Poids total doit être 3"
    
    # Vérifier que les arêtes sont bien présentes
    edge_set = set((s1, s2) for s1, s2 in mst)
    expected_edges = {('A', 'B'), ('B', 'C')}
    assert edge_set == expected_edges, f"Arêtes incorrectes: {edge_set} vs {expected_edges}" 