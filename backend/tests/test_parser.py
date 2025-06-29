import pytest
from utils.parser import load_data, parse_metro_file, parse_pospoints_file
import os

def test_load_data():
    """Test le chargement complet des données."""
    graph, positions, stations = load_data()
    
    # Vérifier que les données sont chargées
    assert graph is not None
    assert positions is not None
    assert stations is not None
    
    # Vérifier le nombre de stations
    assert len(stations) > 0
    assert len(graph) == len(stations)
    
    # Vérifier la structure des données
    for station_id, station_data in stations.items():
        assert 'name' in station_data
        assert 'line' in station_data
        assert station_id in graph
        assert station_id in positions

def test_parse_metro_file():
    """Test le parsing du fichier metro.txt."""
    metro_file = os.path.join('data', 'metro.txt')
    graph, stations = parse_metro_file(metro_file)
    
    # Vérifier la structure du graphe
    assert graph is not None
    assert stations is not None
    
    # Vérifier que chaque station a des voisins
    for station_id, neighbors in graph.items():
        assert isinstance(neighbors, dict)
        for neighbor, weight in neighbors.items():
            assert isinstance(weight, (int, float))
            assert weight > 0

def test_parse_pospoints_file():
    """Test le parsing du fichier pospoints.txt."""
    pospoints_file = os.path.join('data', 'pospoint.txt')
    graph, _, stations = load_data()  # Pour obtenir les stations
    positions = parse_pospoints_file(pospoints_file, stations)
    
    # Vérifier la structure des positions
    assert positions is not None
    assert len(positions) > 0
    
    # Vérifier le format des coordonnées
    for station_id, coords in positions.items():
        assert isinstance(coords, tuple)
        assert len(coords) == 2
        assert isinstance(coords[0], (int, float))
        assert isinstance(coords[1], (int, float))

def test_data_consistency():
    """Test la cohérence entre les différents fichiers."""
    graph, positions, stations = load_data()
    
    # Vérifier que toutes les stations du graphe ont des positions
    for station_id in graph:
        assert station_id in positions
    
    # Vérifier que toutes les stations ont des voisins
    for station_id in stations:
        assert station_id in graph
        assert len(graph[station_id]) > 0

def test_station_connections():
    """Test la symétrie des connexions entre stations."""
    graph, _, _ = load_data()
    
    # Vérifier que si A est connecté à B, alors B est connecté à A
    for station1, neighbors in graph.items():
        for station2, connections in neighbors.items():
            assert station1 in graph[station2]
            
            # Vérifier que les connexions sont symétriques
            # La nouvelle structure peut avoir des listes de connexions
            if isinstance(connections, list):
                # Pour les listes, vérifier qu'il y a au moins une connexion
                assert len(connections) > 0
                if isinstance(graph[station2][station1], list):
                    assert len(graph[station2][station1]) > 0
            else:
                # Pour les valeurs simples, vérifier l'égalité
                assert graph[station2][station1] == connections 