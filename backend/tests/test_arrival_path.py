"""
MetroCity - Mastercamp 2025
Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
Fichier: test_arrival_path.py
Description: Tests unitaires pour les calculs de chemins avec heure d'arrivée souhaitée
"""

import pytest
import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
from services.temporal_path import TemporalPathService, TemporalPath, TemporalSegment
from services.graph_service import GraphService
from services.gtfs_temporal import GTFSemporalService
from utils.data_manager import DataManager

class TestArrivalPath(unittest.TestCase):
    """Tests pour la fonctionnalité d'itinéraire avec horaire d'arrivée"""
    
    @classmethod
    def setUpClass(cls):
        """Initialisation des services pour tous les tests"""
        try:
            # Charger les données
            graph, positions, stations = DataManager.get_data()
            
            # Initialiser les services
            cls.graph_service = GraphService(graph, stations)
            cls.gtfs_service = GTFSemporalService("data/gtfs")
            cls.temporal_service = TemporalPathService(cls.graph_service, cls.gtfs_service)
            
            print("✅ Services initialisés avec succès")
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation: {e}")
            raise
    
    def test_arrival_path_basic(self):
        """Test basique de la fonctionnalité d'itinéraire avec horaire d'arrivée"""
        start_station = "Châtelet"
        end_station = "Bastille"
        arrival_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Calculer l'itinéraire avec horaire d'arrivée
        path = self.temporal_service.find_optimal_temporal_path_with_arrival_time(
            start_station=start_station,
            end_station=end_station,
            arrival_time=arrival_time,
            max_structural_paths=3,
            max_wait_time=1800
        )
        
        # Vérifications de base
        if path is not None:
            self.assertIsInstance(path, TemporalPath)
            self.assertGreater(len(path.segments), 0)
            self.assertIsNotNone(path.departure_time)
            self.assertIsNotNone(path.arrival_time)
            self.assertGreaterEqual(path.total_duration, 0)
            
            # Vérifier que l'arrivée est proche de l'heure souhaitée
            arrival_diff = abs(int((path.arrival_time - arrival_time).total_seconds() / 60))
            self.assertLessEqual(arrival_diff, 30)  # Écart maximum de 30 minutes
            
            print(f"✅ Itinéraire trouvé: Départ {path.departure_time.strftime('%H:%M')}, Arrivée {path.arrival_time.strftime('%H:%M')}, Écart {arrival_diff} min")
        else:
            print("⚠️ Aucun itinéraire trouvé (peut être normal selon les horaires)")
    
    def test_arrival_path_vs_normal_path(self):
        """Compare l'itinéraire avec horaire d'arrivée vs l'itinéraire normal"""
        start_station = "Châtelet"
        end_station = "Bastille"
        target_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Itinéraire normal
        normal_path = self.temporal_service.find_optimal_temporal_path(
            start_station=start_station,
            end_station=end_station,
            departure_time=target_time,
            max_structural_paths=3,
            max_wait_time=1800
        )
        
        # Itinéraire avec horaire d'arrivée
        arrival_path = self.temporal_service.find_optimal_temporal_path_with_arrival_time(
            start_station=start_station,
            end_station=end_station,
            arrival_time=target_time,
            max_structural_paths=3,
            max_wait_time=1800
        )
        
        # Comparer les résultats si les deux itinéraires existent
        if normal_path and arrival_path:
            normal_diff = abs(int((normal_path.arrival_time - target_time).total_seconds() / 60))
            arrival_diff = abs(int((arrival_path.arrival_time - target_time).total_seconds() / 60))
            
            print(f"Normal: écart {normal_diff} min, Arrivée: écart {arrival_diff} min")
            
            # L'itinéraire avec horaire d'arrivée devrait être au moins aussi bon
            # (mais pas forcément meilleur car l'algorithme normal peut aussi être optimal)
            self.assertLessEqual(arrival_diff, normal_diff + 5)  # Tolérance de 5 minutes
    
    def test_arrival_path_different_stations(self):
        """Test avec différentes paires de stations"""
        test_cases = [
            ("Châtelet", "Bastille"),
            ("Gare du Nord", "Gare de Lyon"),
            ("Montparnasse", "Saint-Lazare"),
        ]
        
        arrival_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0)
        
        for start_station, end_station in test_cases:
            with self.subTest(start=start_station, end=end_station):
                path = self.temporal_service.find_optimal_temporal_path_with_arrival_time(
                    start_station=start_station,
                    end_station=end_station,
                    arrival_time=arrival_time,
                    max_structural_paths=3,
                    max_wait_time=1800
                )
                
                if path is not None:
                    # Vérifications de base - pour un chemin rétrograde, on vérifie l'arrivée
                    self.assertEqual(path.segments[-1].to_station, end_station)
                    
                    # Vérifier que l'arrivée est proche de l'heure souhaitée
                    arrival_diff = abs(int((path.arrival_time - arrival_time).total_seconds() / 60))
                    self.assertLessEqual(arrival_diff, 60)  # Écart maximum de 1 heure
                    
                    print(f"✅ {start_station} → {end_station}: écart {arrival_diff} min")
                else:
                    print(f"⚠️ Aucun itinéraire trouvé pour {start_station} → {end_station}")
    
    def test_arrival_path_edge_cases(self):
        """Test des cas limites"""
        start_station = "Châtelet"
        end_station = "Bastille"
        
        # Test avec une heure très tôt
        early_time = datetime.now().replace(hour=5, minute=0, second=0, microsecond=0)
        path_early = self.temporal_service.find_optimal_temporal_path_with_arrival_time(
            start_station=start_station,
            end_station=end_station,
            arrival_time=early_time,
            max_structural_paths=3,
            max_wait_time=1800
        )
        
        # Test avec une heure très tardive
        late_time = datetime.now().replace(hour=23, minute=0, second=0, microsecond=0)
        path_late = self.temporal_service.find_optimal_temporal_path_with_arrival_time(
            start_station=start_station,
            end_station=end_station,
            arrival_time=late_time,
            max_structural_paths=3,
            max_wait_time=1800
        )
        
        # Les deux peuvent retourner None si les horaires ne sont pas disponibles
        print(f"Tôt (5h): {'✅' if path_early else '❌'}")
        print(f"Tard (23h): {'✅' if path_late else '❌'}")
    
    def test_arrival_path_validation(self):
        """Test de validation des paramètres"""
        # Test avec des stations inexistantes
        path = self.temporal_service.find_optimal_temporal_path_with_arrival_time(
            start_station="Station Inexistante",
            end_station="Autre Station Inexistante",
            arrival_time=datetime.now(),
            max_structural_paths=3,
            max_wait_time=1800
        )
        
        # Devrait retourner None pour des stations inexistantes
        self.assertIsNone(path)
        print("✅ Validation des stations inexistantes OK")

if __name__ == '__main__':
    # Configuration des tests
    unittest.main(verbosity=2) 