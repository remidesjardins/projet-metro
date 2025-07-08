"""
MetroCity - Mastercamp 2025
Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
Fichier: test_connexite_service.py
Description: Tests unitaires pour le service de vérification de connexité du réseau
"""

import unittest
import pytest
from services.connexite import ConnexiteChecker
from utils.parser import load_data

class TestConnexiteChecker:
    """Tests unitaires pour le service ConnexiteChecker."""
    
    def setup_method(self):
        """Initialisation avant chaque test."""
        self.checker = ConnexiteChecker()
        self.graph, self.positions, self.stations = load_data()
    
    def test_initialization(self):
        """Test de l'initialisation du checker."""
        assert self.checker.graph is not None
        assert self.checker.positions is not None
        assert self.checker.stations is not None
        assert isinstance(self.checker.visited, set)
        assert len(self.checker.visited) == 0
    
    def test_dfs_algorithm(self):
        """Test de l'algorithme DFS."""
        # Réinitialiser les stations visitées
        self.checker.visited.clear()
        
        # Choisir une station de départ
        start_station = next(iter(self.checker.graph))
        
        # Lancer DFS
        self.checker.dfs(start_station)
        
        # Vérifications
        assert start_station in self.checker.visited
        assert len(self.checker.visited) > 0
        assert len(self.checker.visited) <= len(self.checker.graph)
        
        # Vérifier que toutes les stations visitées existent dans le graphe
        for station in self.checker.visited:
            assert station in self.checker.graph
    
    def test_is_connected(self):
        """Test de la méthode is_connected."""
        is_connected = self.checker.is_connected()
        
        # Vérifications de base
        assert isinstance(is_connected, bool)
        
        # Si connexe, toutes les stations doivent être visitées
        if is_connected:
            assert len(self.checker.visited) == len(self.checker.graph)
        else:
            assert len(self.checker.visited) < len(self.checker.graph)
    
    def test_get_unreachable_stations(self):
        """Test de la méthode get_unreachable_stations."""
        # D'abord vérifier la connexité
        is_connected = self.checker.is_connected()
        unreachable = self.checker.get_unreachable_stations()
        
        # Vérifications
        assert isinstance(unreachable, list)
        
        if is_connected:
            assert len(unreachable) == 0
        else:
            assert len(unreachable) > 0
            # Vérifier que les stations inaccessibles ne sont pas dans visited
            for station in unreachable:
                assert station not in self.checker.visited
                assert station in self.checker.graph
    
    def test_check_connexity_from_station_valid(self):
        """Test de check_connexity_from_station avec une station valide."""
        # Trouver une station valide
        valid_station_name = None
        for station_id, station_data in self.checker.stations.items():
            valid_station_name = station_data['name']
            break
        
        assert valid_station_name is not None
        
        # Tester la connexité depuis cette station
        is_connected, unreachable_stations = self.checker.check_connexity_from_station(valid_station_name)
        
        # Vérifications
        assert isinstance(is_connected, bool)
        assert isinstance(unreachable_stations, list)
        
        # Vérifier la structure des stations inaccessibles
        for station in unreachable_stations:
            assert 'id' in station
            assert 'name' in station
            assert 'line' in station
            assert isinstance(station['id'], str)
            assert isinstance(station['name'], str)
            assert isinstance(station['line'], (str, list))
    
    def test_check_connexity_from_station_invalid(self):
        """Test de check_connexity_from_station avec une station invalide."""
        with pytest.raises(ValueError, match="Station 'StationInexistante' non trouvée"):
            self.checker.check_connexity_from_station("StationInexistante")
    
    def test_connexity_consistency(self):
        """Test de la cohérence entre les différentes méthodes."""
        # Test général
        is_connected_general = self.checker.is_connected()
        unreachable_general = self.checker.get_unreachable_stations()
        
        # Test depuis une station spécifique
        start_station_name = None
        for station_id, station_data in self.checker.stations.items():
            start_station_name = station_data['name']
            break
        
        is_connected_from_station, unreachable_from_station = self.checker.check_connexity_from_station(start_station_name)
        
        # Les résultats doivent être cohérents
        assert is_connected_general == is_connected_from_station
        
        # Le nombre de stations inaccessibles doit être le même
        assert len(unreachable_general) == len(unreachable_from_station)
    
    def test_visited_stations_consistency(self):
        """Test de la cohérence des stations visitées."""
        # Réinitialiser
        self.checker.visited.clear()
        
        # Vérifier la connexité
        is_connected = self.checker.is_connected()
        
        # Après is_connected(), visited doit contenir des stations
        assert len(self.checker.visited) > 0
        
        # Toutes les stations visitées doivent exister dans le graphe
        for station in self.checker.visited:
            assert station in self.checker.graph
        
        # Si connexe, toutes les stations doivent être visitées
        if is_connected:
            assert len(self.checker.visited) == len(self.checker.graph)
    
    def test_performance(self):
        """Test de performance de l'algorithme."""
        import time
        
        # Test de performance pour is_connected
        start_time = time.time()
        self.checker.is_connected()
        end_time = time.time()
        
        # L'algorithme doit être rapide (moins de 1 seconde)
        assert (end_time - start_time) < 1.0
        
        # Test de performance pour get_unreachable_stations
        start_time = time.time()
        self.checker.get_unreachable_stations()
        end_time = time.time()
        
        # L'algorithme doit être rapide (moins de 1 seconde)
        assert (end_time - start_time) < 1.0

def test_connexite_function():
    """Test de la fonction utilitaire test_connexite."""
    from services.connexite import test_connexite
    
    is_connected, unreachable = test_connexite()
    
    # Vérifications
    assert isinstance(is_connected, bool)
    assert isinstance(unreachable, list)
    
    # Si connexe, pas de stations inaccessibles
    if is_connected:
        assert len(unreachable) == 0
    else:
        assert len(unreachable) > 0 