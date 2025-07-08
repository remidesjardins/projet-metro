#!/usr/bin/env python3
"""
MetroCity - Audit de Performance et Impact Écologique RÉALISTE
Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
Fichier: audit_performance.py
Description: Script d'audit complet pour analyser les performances et l'impact écologique
             avec simulation d'usage réel (centaines d'itinéraires, horaires variés)
"""

import os
import sys
import time
import psutil
import cProfile
import pstats
import io
import json
import tracemalloc
import gc
import threading
import subprocess
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Tuple
from contextlib import contextmanager
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import tempfile
import random
from collections import defaultdict

# Ajout du dossier parent au sys.path pour les imports backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

# Imports des services de l'application
from utils.parser import load_data
from utils.gtfs_parser import parse_gtfs_to_graph
from services.dijkstra import dijkstra, shortest_path_by_name
from services.kruskal import kruskal_mst
from services.connexite import ConnexiteChecker, test_connexite
from services.graph_service import GraphService
from services.gtfs_temporal import GTFSemporalService
from services.temporal_path import TemporalPathService
from services.service_registry import get_graph_service, get_gtfs_service, get_temporal_service

@dataclass
class PerformanceMetrics:
    """Métriques de performance pour une opération"""
    operation_name: str
    execution_time: float
    memory_peak: float
    memory_current: float
    cpu_percent: float
    complexity_order: str
    carbon_footprint: float  # grammes CO2
    energy_consumption: float  # joules
    network_calls: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    route_length: int = 0  # nombre de stations
    time_category: str = ""  # matin, midi, soir, weekend
    success_rate: float = 1.0

@dataclass
class AuditResults:
    """Résultats complets de l'audit"""
    timestamp: str
    system_info: Dict[str, Any]
    station_loading: PerformanceMetrics
    classical_routing: List[PerformanceMetrics]
    temporal_routing: List[PerformanceMetrics]
    concurrent_routing: Dict[str, Any]
    acpm_calculation: PerformanceMetrics
    connectivity_analysis: PerformanceMetrics
    overall_performance: Dict[str, Any]
    environmental_impact: Dict[str, Any]
    recommendations: List[str]
    statistical_analysis: Dict[str, Any]

class EnergyMonitor:
    """Moniteur de consommation énergétique"""
    
    def __init__(self):
        self.start_time = None
        self.start_cpu_percent = None
        self.start_memory = None
        self.readings = []
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Démarre le monitoring énergétique"""
        self.start_time = time.time()
        self.start_cpu_percent = psutil.cpu_percent(interval=0.1)
        self.start_memory = psutil.virtual_memory().used
        self.readings = []
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Arrête le monitoring et retourne les métriques"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        
        end_time = time.time()
        duration = end_time - self.start_time
        
        # Si pas de lectures ou durée très courte, utiliser des valeurs par défaut
        if not self.readings or duration < 0.01:
            # Valeurs par défaut pour éviter les zéros
            default_cpu = 5.0  # 5% CPU minimum
            default_memory = psutil.virtual_memory().used
            default_duration = max(duration, 0.001)  # Minimum 1ms
            
            # Calcul avec valeurs par défaut
            cpu_power_watts = 65 * (default_cpu / 100)
            memory_power_watts = 3 * (default_memory / (8 * 1024**3))
            total_power_watts = cpu_power_watts + memory_power_watts
            energy_joules = total_power_watts * default_duration
            
            # Facteur d'émission carbone France : ~57g CO2/kWh
            carbon_grams = energy_joules * (57 / 3600000)  # conversion J->kWh->gCO2
            
            return {
                'energy_joules': energy_joules,
                'carbon_grams': carbon_grams,
                'peak_cpu': default_cpu,
                'peak_memory': default_memory
            }
        
        # Calcul de la consommation énergétique basée sur CPU et mémoire
        avg_cpu = np.mean([r['cpu'] for r in self.readings])
        peak_cpu = max([r['cpu'] for r in self.readings])
        peak_memory = max([r['memory'] for r in self.readings])
        
        # S'assurer que les valeurs ne sont pas trop faibles
        avg_cpu = max(avg_cpu, 1.0)  # Minimum 1% CPU
        peak_cpu = max(peak_cpu, 2.0)  # Minimum 2% CPU peak
        
        # Estimation énergétique (valeurs approximatives)
        # CPU moderne : ~65W TDP, proportionnel à l'utilisation
        cpu_power_watts = 65 * (avg_cpu / 100)
        # RAM DDR4 : ~3W par 8GB
        memory_power_watts = 3 * (peak_memory / (8 * 1024**3))
        
        total_power_watts = cpu_power_watts + memory_power_watts
        energy_joules = total_power_watts * duration
        
        # Facteur d'émission carbone France : ~57g CO2/kWh
        carbon_grams = energy_joules * (57 / 3600000)  # conversion J->kWh->gCO2
        
        return {
            'energy_joules': energy_joules,
            'carbon_grams': carbon_grams,
            'peak_cpu': peak_cpu,
            'peak_memory': peak_memory
        }
    
    def _monitor_loop(self):
        """Boucle de monitoring en arrière-plan"""
        while self.monitoring:
            try:
                cpu_percent = psutil.cpu_percent(interval=0.05)  # Plus fréquent
                memory_usage = psutil.virtual_memory().used
                self.readings.append({
                    'timestamp': time.time(),
                    'cpu': cpu_percent,
                    'memory': memory_usage
                })
                time.sleep(0.05)  # Plus fréquent pour capturer les opérations courtes
            except Exception:
                # En cas d'erreur, continuer le monitoring
                time.sleep(0.05)

@contextmanager
def performance_monitor(operation_name: str):
    """Context manager pour mesurer les performances d'une opération"""
    # Démarrage du monitoring
    energy_monitor = EnergyMonitor()
    energy_monitor.start_monitoring()
    
    tracemalloc.start()
    process = psutil.Process()
    
    start_time = time.time()
    start_memory = process.memory_info().rss
    start_cpu = process.cpu_percent()
    
    gc.collect()  # Nettoyage avant mesure
    
    try:
        yield
    finally:
        # Arrêt du monitoring
        end_time = time.time()
        execution_time = end_time - start_time
        
        current_memory = process.memory_info().rss
        memory_peak = tracemalloc.get_traced_memory()[1]
        cpu_percent = process.cpu_percent()
        
        energy_metrics = energy_monitor.stop_monitoring()
        tracemalloc.stop()
        
        # Stockage des métriques (à implémenter selon vos besoins)
        print(f"[PERF] {operation_name}: {execution_time:.3f}s, "
              f"Memory: {memory_peak/1024/1024:.1f}MB, "
              f"Energy: {energy_metrics['energy_joules']:.2f}J")

class RealisticPerformanceAuditor:
    """Auditeur principal de performance avec simulation réaliste"""
    
    def __init__(self):
        self.results = []
        self.base_url = "http://localhost:5050"
        
        # Configuration des tests réalistes
        self.test_routes_count = 200  # Grand nombre d'itinéraires à tester
        self.temporal_routes_count = 100  # Tests temporels
        self.concurrent_users = [10, 25, 50, 100]  # Simulation d'utilisateurs concurrents
        
        # Heures de test variées (simulation réelle)
        self.test_times = {
            "heure_pointe_matin": (8, 30),    # 8h30 - heure de pointe
            "heure_pointe_soir": (18, 0),     # 18h00 - heure de pointe
            "heure_creuse_midi": (14, 0),     # 14h00 - heure creuse
            "heure_creuse_soir": (22, 0),     # 22h00 - heure creuse
            "weekend_matin": (10, 0),         # 10h00 weekend
            "weekend_soir": (20, 0)           # 20h00 weekend
        }
        
        # Jours de test
        self.test_days = {
            "lundi": 0, "mardi": 1, "mercredi": 2, "jeudi": 3, 
            "vendredi": 4, "samedi": 5, "dimanche": 6
        }
        
        self.all_stations = []
        self.station_categories = {
            "courtes_distances": [],    # < 5 stations
            "moyennes_distances": [],   # 5-10 stations  
            "longues_distances": []     # > 10 stations
        }
        
    def check_backend_available(self, max_wait=30):
        """Vérifie que le backend est bien lancé avant de démarrer l'audit."""
        import requests
        import time
        start = time.time()
        while time.time() - start < max_wait:
            try:
                response = requests.get(f"{self.base_url}/health", timeout=2)
                if response.status_code == 200:
                    print("✅ Backend disponible sur /health.")
                    return True
            except Exception:
                pass
            print("⏳ Attente du démarrage du backend sur http://localhost:5050...")
            time.sleep(2)
        print("❌ Le backend n'est pas accessible sur http://localhost:5050 après 30s. Veuillez le démarrer avant de relancer l'audit.")
        raise RuntimeError("Backend non disponible")
    
    def run_full_realistic_audit(self) -> AuditResults:
        self.check_backend_available()
        """Lance l'audit complet de performance réaliste"""
        print("🔍 Démarrage de l'audit de performance RÉALISTE...")
        print("📊 Tests prévus:")
        print(f"   • {self.test_routes_count} itinéraires classiques")
        print(f"   • {self.temporal_routes_count} itinéraires temporels")
        print(f"   • Tests de charge jusqu'à {max(self.concurrent_users)} utilisateurs simultanés")
        print(f"   • {len(self.test_times)} créneaux horaires différents")
        print("=" * 80)
        
        # Chargement des stations pour les tests
        self._load_station_data()
        
        # Tests séquentiels
        system_info = self._get_system_info()
        station_loading = self._audit_station_loading()
        
        # Tests d'itinéraires classiques (grande échelle)
        print("\n🚇 Tests d'itinéraires classiques (simulation réaliste)...")
        classical_routing = self._audit_realistic_classical_routing()
        
        # Tests d'itinéraires temporels (grande échelle)
        print("\n🕘 Tests d'itinéraires temporels (simulation réaliste)...")
        temporal_routing = self._audit_realistic_temporal_routing()
        
        # Tests de charge concurrente
        print("\n🚀 Tests de charge et utilisateurs concurrents...")
        concurrent_routing = self._audit_concurrent_routing()
        
        # Tests algorithmes
        acpm_calculation = self._audit_acpm_calculation()
        connectivity_analysis = self._audit_connectivity_analysis()
        overall_performance = self._analyze_overall_performance()
        
        # Analyses finales
        environmental_impact = self._calculate_environmental_impact()
        statistical_analysis = self._generate_statistical_analysis(classical_routing, temporal_routing)
        recommendations = self._generate_enhanced_recommendations(statistical_analysis)
        
        results = AuditResults(
            timestamp=datetime.now().isoformat(),
            system_info=system_info,
            station_loading=station_loading,
            classical_routing=classical_routing,
            temporal_routing=temporal_routing,
            concurrent_routing=concurrent_routing,
            acpm_calculation=acpm_calculation,
            connectivity_analysis=connectivity_analysis,
            overall_performance=overall_performance,
            environmental_impact=environmental_impact,
            recommendations=recommendations,
            statistical_analysis=statistical_analysis
        )
        
        # Remplir self.results pour l'impact environnemental
        self.results = []
        if isinstance(station_loading, PerformanceMetrics):
            self.results.append(station_loading)
        self.results.extend(classical_routing)
        self.results.extend(temporal_routing)
        if isinstance(acpm_calculation, PerformanceMetrics):
            self.results.append(acpm_calculation)
        if isinstance(connectivity_analysis, PerformanceMetrics):
            self.results.append(connectivity_analysis)
        # On peut ajouter d'autres métriques si besoin
        print("\n📊 Génération du rapport détaillé...")
        self._generate_enhanced_markdown_report(results)
        return results
    
    def _load_station_data(self):
        """Charge et prépare les données des stations pour les tests"""
        print("📊 Chargement et analyse des stations...")
        
        graph, positions, stations = load_data()
        self.all_stations = list(stations.keys())
        print(f"   • {len(self.all_stations)} stations chargées")
        
        # Analyse des distances entre stations pour catégoriser
        sample_routes = []
        for _ in range(100):  # Échantillon pour catégoriser
            start, end = random.sample(self.all_stations, 2)
            try:
                start_name = stations[start]['name']
                end_name = stations[end]['name']
                path, distance, _, _ = shortest_path_by_name(start_name, end_name)
                sample_routes.append((start, end, len(path)))
            except:
                continue
        
        # Catégorisation par distance
        for start, end, length in sample_routes:
            if length < 5:
                self.station_categories["courtes_distances"].append((start, end))
            elif length < 10:
                self.station_categories["moyennes_distances"].append((start, end))
            else:
                self.station_categories["longues_distances"].append((start, end))
        
        print(f"   • Routes courtes: {len(self.station_categories['courtes_distances'])}")
        print(f"   • Routes moyennes: {len(self.station_categories['moyennes_distances'])}")
        print(f"   • Routes longues: {len(self.station_categories['longues_distances'])}")

    def _generate_realistic_routes(self, count: int) -> List[Tuple[str, str, str, str, str]]:
        """Génère une liste d'itinéraires réalistes avec catégorie et IDs"""
        routes = []
        graph, positions, stations = load_data()
        # Répartition réaliste : 40% courts, 50% moyens, 10% longs
        short_count = int(count * 0.4)
        medium_count = int(count * 0.5) 
        long_count = count - short_count - medium_count
        # Routes courtes (1-4 stations)
        for _ in range(short_count):
            start, end = random.sample(self.all_stations, 2)
            try:
                start_name = stations[start]['name']
                end_name = stations[end]['name']
                path, _, _, _ = shortest_path_by_name(start_name, end_name)
                if len(path) <= 4:
                    routes.append((start, end, start_name, end_name, "courte"))
            except:
                pass
        # Routes moyennes (5-8 stations)
        for _ in range(medium_count):
            start, end = random.sample(self.all_stations, 2)
            try:
                start_name = stations[start]['name']
                end_name = stations[end]['name']
                path, _, _, _ = shortest_path_by_name(start_name, end_name)
                if 5 <= len(path) <= 8:
                    routes.append((start, end, start_name, end_name, "moyenne"))
            except:
                pass
        # Routes longues (9+ stations)
        for _ in range(long_count):
            start, end = random.sample(self.all_stations, 2)
            try:
                start_name = stations[start]['name']
                end_name = stations[end]['name']
                path, _, _, _ = shortest_path_by_name(start_name, end_name)
                if len(path) >= 9:
                    routes.append((start, end, start_name, end_name, "longue"))
            except:
                pass
        return routes

    def _get_system_info(self) -> Dict[str, Any]:
        """Collecte les informations système"""
        return {
            'platform': os.uname(),
            'python_version': sys.version,
            'cpu_count': psutil.cpu_count(),
            'memory_total': psutil.virtual_memory().total,
            'disk_usage': psutil.disk_usage('/').total,
            'python_executable': sys.executable
        }
    
    def _audit_station_loading(self) -> PerformanceMetrics:
        """Audit du chargement des stations"""
        energy_monitor = EnergyMonitor()
        energy_monitor.start_monitoring()
        
        tracemalloc.start()
        start_time = time.time()
        start_memory = psutil.virtual_memory().used
        
        # Test de chargement multiple pour moyenner
        iterations = 10
        load_times = []
        
        for i in range(iterations):
            iter_start = time.time()
            graph, positions, stations = load_data()
            iter_end = time.time()
            load_times.append(iter_end - iter_start)
        
        execution_time = time.time() - start_time
        memory_peak = tracemalloc.get_traced_memory()[1]
        energy_metrics = energy_monitor.stop_monitoring()
        tracemalloc.stop()
        
        # Analyse de complexité : O(n) où n = nombre de stations
        station_count = len(stations) if 'stations' in locals() else 0
        complexity_order = f"O(n) où n={station_count} stations"
        
        avg_load_time = np.mean(load_times)
        print(f"   ⏱️  Temps moyen de chargement: {avg_load_time:.3f}s")
        print(f"   📊 Stations chargées: {station_count}")
        print(f"   💾 Mémoire utilisée: {memory_peak/1024/1024:.1f}MB")
        print(f"   ⚡ Énergie consommée: {energy_metrics['energy_joules']:.2f}J")
        
        return PerformanceMetrics(
            operation_name="Station Loading",
            execution_time=avg_load_time,
            memory_peak=memory_peak,
            memory_current=psutil.virtual_memory().used,
            cpu_percent=energy_metrics['peak_cpu'],
            complexity_order=complexity_order,
            carbon_footprint=energy_metrics['carbon_grams'],
            energy_consumption=energy_metrics['energy_joules']
        )
    
    def _audit_realistic_classical_routing(self) -> List[PerformanceMetrics]:
        """Audit des calculs d'itinéraires classiques avec simulation réaliste"""
        results = []
        
        # Génération d'itinéraires réalistes
        print(f"   📍 Génération de {self.test_routes_count} itinéraires réalistes...")
        realistic_routes = self._generate_realistic_routes(self.test_routes_count)
        
        # Statistiques par catégorie
        categories_count = defaultdict(int)
        for _, _, _, _, category in realistic_routes:
            categories_count[category] += 1
        
        print(f"   📊 Répartition: {dict(categories_count)}")
        
        # Tests par batch pour optimiser l'affichage
        batch_size = 20
        successful_tests = 0
        failed_tests = 0
        
        for batch_idx in range(0, len(realistic_routes), batch_size):
            batch = realistic_routes[batch_idx:batch_idx + batch_size]
            print(f"   🔄 Batch {batch_idx//batch_size + 1}/{(len(realistic_routes)-1)//batch_size + 1} ({len(batch)} routes)")
            
            for i, (start_id, end_id, start_name, end_name, category) in enumerate(batch):
                energy_monitor = EnergyMonitor()
                energy_monitor.start_monitoring()
                tracemalloc.start()
                
                start_time = time.time()
                
                try:
                    # Test avec Dijkstra
                    path, distance, _, _ = shortest_path_by_name(start_name, end_name)
                    execution_time = time.time() - start_time
                    
                    memory_peak = tracemalloc.get_traced_memory()[1]
                    energy_metrics = energy_monitor.stop_monitoring()
                    tracemalloc.stop()
                    
                    # Complexité de Dijkstra : O((V + E) log V)
                    if not hasattr(self, '_complexity_calculated'):
                        graph, _, stations = load_data()
                        V = len(stations)
                        E = sum(len(neighbors) for neighbors in graph.values()) // 2
                        self._complexity_order = f"O((V + E) log V) où V={V}, E={E}"
                        self._complexity_calculated = True
                    
                    # Affichage détaillé pour les premiers tests seulement
                    if batch_idx == 0 and i < 5:
                        print(f"      🗺️  {start_name} → {end_name} ({category})")
                        print(f"         ⏱️  Temps: {execution_time:.3f}s")
                        print(f"         🛤️  Distance: {distance}s")
                        print(f"         📊 Étapes: {len(path)}")
                    
                    results.append(PerformanceMetrics(
                        operation_name=f"Classical Routing: {start_name} → {end_name}",
                        execution_time=execution_time,
                        memory_peak=memory_peak,
                        memory_current=psutil.virtual_memory().used,
                        cpu_percent=energy_metrics['peak_cpu'],
                        complexity_order=self._complexity_order,
                        carbon_footprint=energy_metrics['carbon_grams'],
                        energy_consumption=energy_metrics['energy_joules'],
                        route_length=len(path),
                        time_category=category,
                        success_rate=1.0
                    ))
                    
                    successful_tests += 1
                    
                except Exception as e:
                    if batch_idx == 0 and i < 5:
                        print(f"      ❌ Erreur {start_name} → {end_name}: {str(e)[:50]}...")
                    energy_monitor.stop_monitoring()
                    tracemalloc.stop()
                    failed_tests += 1
            
            # Affichage du progrès
            if batch_idx > 0:  # Pas pour le premier batch déjà affiché en détail
                print(f"      ✅ Batch terminé: {successful_tests + failed_tests} tests")
        
        print(f"   📊 Résultats finaux: {successful_tests} succès, {failed_tests} échecs")
        print(f"   💯 Taux de réussite: {successful_tests/(successful_tests + failed_tests)*100:.1f}%")
        
        return results
    
    def _audit_realistic_temporal_routing(self) -> List[PerformanceMetrics]:
        """Audit des calculs d'itinéraires temporels avec horaires et dates variés"""
        results = []
        
        # Génération d'itinéraires pour les tests temporels
        print(f"   📍 Génération de {self.temporal_routes_count} itinéraires temporels...")
        temporal_routes = self._generate_realistic_routes(self.temporal_routes_count)
        
        # Chargement des services temporels
        try:
            temporal_service = get_temporal_service()
        except Exception as e:
            print(f"   ⚠️  Service temporel non disponible: {e}")
            return results
        
        # Tests avec différents créneaux horaires
        successful_tests = 0
        failed_tests = 0
        
        for time_name, (hour, minute) in self.test_times.items():
            print(f"\n   🕘 Tests {time_name} ({hour:02d}:{minute:02d})")
            
            # Base date (lundi pour jours de semaine, samedi pour weekend)
            base_date = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
            if 'weekend' in time_name:
                # Ajuster au prochain samedi
                days_ahead = 5 - base_date.weekday()  # samedi = 5
                if days_ahead <= 0:
                    days_ahead += 7
                base_date += timedelta(days=days_ahead)
            
            # Sélection d'itinéraires pour ce créneau (environ 15-20 par créneau)
            route_sample = random.sample(temporal_routes, min(20, len(temporal_routes)))
            
            for i, (start_id, end_id, start_name, end_name, category) in enumerate(route_sample):
                energy_monitor = EnergyMonitor()
                energy_monitor.start_monitoring()
                tracemalloc.start()
                
                start_time = time.time()
                
                try:
                    # Test avec l'API REST (simulation frontend)
                    response = requests.post(f"{self.base_url}/temporal/alternatives", 
                                           json={
                                               'start_station': start_name,
                                               'end_station': end_name,
                                               'departure_time': base_date.strftime("%H:%M"),
                                               'date': base_date.strftime("%Y-%m-%d")
                                           }, 
                                           timeout=10)
                    
                    if response.status_code == 200:
                        paths_data = response.json()
                        paths_found = len(paths_data.get('paths', []))
                    else:
                        paths_found = 0
                    
                    execution_time = time.time() - start_time
                    memory_peak = tracemalloc.get_traced_memory()[1]
                    energy_metrics = energy_monitor.stop_monitoring()
                    tracemalloc.stop()
                    
                    # Complexité temporelle : O(P * S * T) où P=chemins, S=segments, T=horaires
                    complexity_order = "O(P * S * T) - recherche multi-critères"
                    
                    # Affichage détaillé pour les premiers tests
                    if i < 3:
                        print(f"      🗺️  {start_name} → {end_name} ({category})")
                        print(f"         ⏱️  Temps: {execution_time:.3f}s")
                        print(f"         🛤️  Chemins trouvés: {paths_found}")
                    
                    results.append(PerformanceMetrics(
                        operation_name=f"Temporal Routing: {start_name} → {end_name} ({time_name})",
                        execution_time=execution_time,
                        memory_peak=memory_peak,
                        memory_current=psutil.virtual_memory().used,
                        cpu_percent=energy_metrics['peak_cpu'],
                        complexity_order=complexity_order,
                        carbon_footprint=energy_metrics['carbon_grams'],
                        energy_consumption=energy_metrics['energy_joules'],
                        route_length=0,  # Non calculé pour temporel
                        time_category=time_name,
                        success_rate=1.0 if paths_found > 0 else 0.0,
                        network_calls=1
                    ))
                    
                    successful_tests += 1
                    
                except Exception as e:
                    if i < 3:
                        print(f"      ❌ Erreur {start_name} → {end_name}: {str(e)[:50]}...")
                    energy_monitor.stop_monitoring()
                    tracemalloc.stop()
                    failed_tests += 1
            
            print(f"      ✅ Créneau terminé: {len(route_sample)} tests")
        
        print(f"\n   📊 Tests temporels finaux: {successful_tests} succès, {failed_tests} échecs")
        print(f"   💯 Taux de réussite: {successful_tests/(successful_tests + failed_tests)*100:.1f}%")
        
        return results
    
    def _audit_concurrent_routing(self) -> Dict[str, Any]:
        """Tests de charge avec utilisateurs concurrents"""
        results = {}
        
        # Tests avec différents nombres d'utilisateurs simultanés
        for user_count in self.concurrent_users:
            print(f"\n   👥 Test avec {user_count} utilisateurs simultanés")
            
            # Générer des routes avec IDs de stations pour l'API
            graph, positions, stations = load_data()
            all_station_ids = list(stations.keys())
            test_routes = []
            for _ in range(user_count):
                start_id, end_id = random.sample(all_station_ids, 2)
                category = "charge"
                test_routes.append((start_id, end_id, category))
            
            def make_routing_request(route_data):
                start_id, end_id, category = route_data
                start_time = time.time()
                
                try:
                    # Test itinéraire classique
                    response = requests.post(f"{self.base_url}/shortest-path", 
                                           json={
                                               'start': start_id,
                                               'end': end_id
                                           }, 
                                           timeout=15)
                    
                    execution_time = time.time() - start_time
                    success = response.status_code == 200
                    
                    return {
                        'success': success,
                        'time': execution_time,
                        'category': category,
                        'status_code': response.status_code if success else 500
                    }
                    
                except requests.exceptions.Timeout:
                    return {
                        'success': False,
                        'time': 15.0,  # timeout
                        'category': category,
                        'status_code': 408
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'time': time.time() - start_time,
                        'category': category,
                        'status_code': 500
                    }
            
            # Exécution concurrente
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=min(user_count, 20)) as executor:
                futures = [executor.submit(make_routing_request, route) 
                          for route in test_routes[:user_count]]
                test_results = [future.result() for future in as_completed(futures)]
            
            total_time = time.time() - start_time
            
            # Analyse des résultats
            successful_requests = sum(1 for r in test_results if r['success'])
            failed_requests = len(test_results) - successful_requests
            
            if successful_requests > 0:
                avg_response_time = np.mean([r['time'] for r in test_results if r['success']])
                percentile_95 = np.percentile([r['time'] for r in test_results if r['success']], 95)
                percentile_99 = np.percentile([r['time'] for r in test_results if r['success']], 99)
            else:
                avg_response_time = 0
                percentile_95 = 0
                percentile_99 = 0
            
            throughput = successful_requests / total_time if total_time > 0 else 0
            
            results[f"{user_count}_users"] = {
                'user_count': user_count,
                'total_requests': len(test_results),
                'successful_requests': successful_requests,
                'failed_requests': failed_requests,
                'success_rate': successful_requests / len(test_results) * 100,
                'total_time': total_time,
                'avg_response_time': avg_response_time,
                'percentile_95': percentile_95,
                'percentile_99': percentile_99,
                'throughput_rps': throughput
            }
            
            print(f"      📊 Résultats: {successful_requests}/{len(test_results)} succès")
            print(f"      ⏱️  Temps moyen: {avg_response_time:.3f}s")
            print(f"      🚀 Débit: {throughput:.1f} req/s")
            print(f"      💯 Taux de réussite: {successful_requests / len(test_results) * 100:.1f}%")
        
        return results
    
    def _audit_acpm_calculation(self) -> PerformanceMetrics:
        """Audit du calcul de l'ACPM avec Kruskal"""
        energy_monitor = EnergyMonitor()
        energy_monitor.start_monitoring()
        tracemalloc.start()
        
        start_time = time.time()
        
        # Chargement des données et préparation des arêtes
        graph, positions, stations = load_data()
        
        edges = []
        seen = set()
        for s1 in graph:
            for s2, weight_data in graph[s1].items():
                if (s2, s1) not in seen:
                    # Extraction du poids selon le format
                    if isinstance(weight_data, list) and len(weight_data) > 0:
                        weight = weight_data[0]['time'] if isinstance(weight_data[0], dict) else weight_data[0]
                    elif isinstance(weight_data, dict):
                        weight = weight_data.get('time', weight_data)
                    else:
                        weight = weight_data
                    
                    edges.append((weight, s1, s2))
                    seen.add((s1, s2))
        
        edges.sort()
        
        # Calcul de l'ACPM avec Kruskal
        mst, total_weight = kruskal_mst(edges, len(graph))
        
        execution_time = time.time() - start_time
        memory_peak = tracemalloc.get_traced_memory()[1]
        energy_metrics = energy_monitor.stop_monitoring()
        tracemalloc.stop()
        
        # Complexité de Kruskal : O(E log E) où E = nombre d'arêtes
        E = len(edges)
        complexity_order = f"O(E log E) où E={E} arêtes"
        
        print(f"   ⏱️  Temps de calcul: {execution_time:.3f}s")
        print(f"   🌳 Arêtes MST: {len(mst)}")
        print(f"   ⚖️  Poids total: {total_weight}")
        print(f"   📊 Arêtes analysées: {E}")
        
        return PerformanceMetrics(
            operation_name="ACPM Calculation (Kruskal)",
            execution_time=execution_time,
            memory_peak=memory_peak,
            memory_current=psutil.virtual_memory().used,
            cpu_percent=energy_metrics['peak_cpu'],
            complexity_order=complexity_order,
            carbon_footprint=energy_metrics['carbon_grams'],
            energy_consumption=energy_metrics['energy_joules']
        )
    
    def _audit_connectivity_analysis(self) -> PerformanceMetrics:
        """Audit de l'analyse de connexité"""
        energy_monitor = EnergyMonitor()
        energy_monitor.start_monitoring()
        tracemalloc.start()
        
        start_time = time.time()
        
        # Test de connexité avec DFS
        checker = ConnexiteChecker()
        is_connected = checker.is_connected()
        unreachable = checker.get_unreachable_stations()
        
        execution_time = time.time() - start_time
        memory_peak = tracemalloc.get_traced_memory()[1]
        energy_metrics = energy_monitor.stop_monitoring()
        tracemalloc.stop()
        
        # Complexité DFS : O(V + E) où V = sommets, E = arêtes
        graph, _, stations = load_data()
        V = len(stations)
        E = sum(len(neighbors) for neighbors in graph.values()) // 2
        complexity_order = f"O(V + E) où V={V}, E={E}"
        
        print(f"   ⏱️  Temps de calcul: {execution_time:.3f}s")
        print(f"   🔗 Graphe connexe: {'✅ Oui' if is_connected else '❌ Non'}")
        print(f"   📊 Stations analysées: {V}")
        print(f"   🚫 Stations inaccessibles: {len(unreachable)}")
        
        return PerformanceMetrics(
            operation_name="Connectivity Analysis (DFS)",
            execution_time=execution_time,
            memory_peak=memory_peak,
            memory_current=psutil.virtual_memory().used,
            cpu_percent=energy_metrics['peak_cpu'],
            complexity_order=complexity_order,
            carbon_footprint=energy_metrics['carbon_grams'],
            energy_consumption=energy_metrics['energy_joules']
        )
    
    def _analyze_overall_performance(self) -> Dict[str, Any]:
        """Analyse des performances globales"""
        
        # Test de charge avec requêtes simultanées
        print("   🚀 Test de charge avec requêtes simultanées...")
        
        def make_request():
            try:
                response = requests.get(f"{self.base_url}/stations", timeout=5)
                return response.status_code == 200, response.elapsed.total_seconds()
            except:
                return False, float('inf')
        
        start_time = time.time()
        concurrent_requests = 50
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(concurrent_requests)]
            results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        successful_requests = sum(1 for success, _ in results if success)
        avg_response_time = np.mean([time for success, time in results if success and time != float('inf')])
        
        print(f"   📊 Requêtes réussies: {successful_requests}/{concurrent_requests}")
        print(f"   ⏱️  Temps moyen de réponse: {avg_response_time:.3f}s")
        print(f"   🔄 Débit: {successful_requests/total_time:.1f} req/s")
        
        return {
            'concurrent_requests_test': {
                'total_requests': concurrent_requests,
                'successful_requests': successful_requests,
                'success_rate': successful_requests / concurrent_requests * 100,
                'average_response_time': avg_response_time,
                'throughput_rps': successful_requests / total_time,
                'total_test_time': total_time
            }
        }
    
    def _calculate_environmental_impact(self) -> Dict[str, Any]:
        """Calcul de l'impact environnemental"""
        
        # Collecte de toutes les métriques énergétiques par catégorie
        station_energy = sum(metric.energy_consumption for metric in self.results 
                           if hasattr(metric, 'energy_consumption') and 'Station Loading' in metric.operation_name)
        
        classical_energy = sum(metric.energy_consumption for metric in self.results 
                             if hasattr(metric, 'energy_consumption') and 'Classical Routing' in metric.operation_name)
        
        temporal_energy = sum(metric.energy_consumption for metric in self.results 
                            if hasattr(metric, 'energy_consumption') and 'Temporal Routing' in metric.operation_name)
        
        acpm_energy = sum(metric.energy_consumption for metric in self.results 
                         if hasattr(metric, 'energy_consumption') and 'ACPM' in metric.operation_name)
        
        connectivity_energy = sum(metric.energy_consumption for metric in self.results 
                                if hasattr(metric, 'energy_consumption') and 'Connectivity' in metric.operation_name)
        
        # Énergie totale
        total_energy = station_energy + classical_energy + temporal_energy + acpm_energy + connectivity_energy
        total_carbon = sum(metric.carbon_footprint for metric in self.results if hasattr(metric, 'carbon_footprint'))
        
        # Estimation annuelle basée sur l'utilisation
        daily_usage_estimate = 1000  # Nombre d'utilisations par jour estimé
        annual_energy = total_energy * daily_usage_estimate * 365
        annual_carbon = total_carbon * daily_usage_estimate * 365
        
        # Équivalences pour la sensibilisation
        car_km_equivalent = annual_carbon / 120  # 120g CO2/km pour une voiture moyenne
        tree_equivalent = annual_carbon / 22000  # Un arbre absorbe ~22kg CO2/an
        
        print(f"   ⚡ Énergie totale mesurée: {total_energy:.2f}J")
        print(f"   🌍 Empreinte carbone: {total_carbon:.3f}g CO2")
        print(f"   📅 Projection annuelle: {annual_carbon/1000:.1f}kg CO2")
        print(f"   🚗 Équivalent: {car_km_equivalent:.0f}km en voiture")
        print(f"   🌳 Compensation: {tree_equivalent:.2f} arbres")
        
        return {
            'measured_energy_joules': total_energy,
            'measured_carbon_grams': total_carbon,
            'energy_by_function': {
                'station_loading': station_energy,
                'classical_routing': classical_energy,
                'temporal_routing': temporal_energy,
                'acpm_calculation': acpm_energy,
                'connectivity_analysis': connectivity_energy
            },
            'annual_projection': {
                'energy_kwh': annual_energy / 3600000,
                'carbon_kg': annual_carbon / 1000,
                'car_km_equivalent': car_km_equivalent,
                'trees_needed': tree_equivalent
            },
            'recommendations': [
                "Optimiser les algorithmes pour réduire la complexité temporelle",
                "Implémenter un cache plus efficace pour éviter les recalculs",
                "Utiliser l'hébergement vert (énergies renouvelables)",
                "Optimiser les requêtes de base de données"
            ]
        }
    
    def _generate_statistical_analysis(self, classical_results: List[PerformanceMetrics], 
                                      temporal_results: List[PerformanceMetrics]) -> Dict[str, Any]:
        """Génère une analyse statistique détaillée des résultats"""
        analysis = {}
        
        # Analyse des itinéraires classiques
        if classical_results:
            exec_times = [r.execution_time for r in classical_results]
            memory_peaks = [r.memory_peak / 1024 / 1024 for r in classical_results]  # MB
            route_lengths = [r.route_length for r in classical_results if r.route_length > 0]
            
            analysis['classical_routing'] = {
                'total_tests': len(classical_results),
                'execution_time': {
                    'mean': np.mean(exec_times),
                    'median': np.median(exec_times),
                    'std': np.std(exec_times),
                    'min': np.min(exec_times),
                    'max': np.max(exec_times),
                    'percentile_95': np.percentile(exec_times, 95),
                    'percentile_99': np.percentile(exec_times, 99)
                },
                'memory_usage': {
                    'mean_mb': np.mean(memory_peaks),
                    'median_mb': np.median(memory_peaks),
                    'max_mb': np.max(memory_peaks),
                    'std_mb': np.std(memory_peaks)
                },
                'route_analysis': {
                    'avg_length': np.mean(route_lengths) if route_lengths else 0,
                    'length_distribution': {
                        'short_routes': sum(1 for l in route_lengths if l <= 4),
                        'medium_routes': sum(1 for l in route_lengths if 5 <= l <= 8),
                        'long_routes': sum(1 for l in route_lengths if l >= 9)
                    }
                }
            }
        
        # Analyse des itinéraires temporels
        if temporal_results:
            temp_times = [r.execution_time for r in temporal_results]
            success_rates = [r.success_rate for r in temporal_results]
            
            # Analyse par créneau horaire
            time_categories = defaultdict(list)
            for r in temporal_results:
                if r.time_category:
                    time_categories[r.time_category].append(r.execution_time)
            
            analysis['temporal_routing'] = {
                'total_tests': len(temporal_results),
                'execution_time': {
                    'mean': np.mean(temp_times),
                    'median': np.median(temp_times),
                    'std': np.std(temp_times),
                    'percentile_95': np.percentile(temp_times, 95)
                },
                'success_rate': {
                    'overall': np.mean(success_rates) * 100,
                    'by_time_category': {
                        category: {
                            'avg_time': np.mean(times),
                            'test_count': len(times)
                        } for category, times in time_categories.items()
                    }
                }
            }
        
        # Calculs de performance globale
        total_energy = sum(r.energy_consumption for r in classical_results + temporal_results)
        total_carbon = sum(r.carbon_footprint for r in classical_results + temporal_results)
        
        analysis['environmental_impact'] = {
            'total_energy_joules': total_energy,
            'total_carbon_grams': total_carbon,
            'avg_energy_per_request': total_energy / len(classical_results + temporal_results) if classical_results + temporal_results else 0,
            'carbon_per_day_estimate': total_carbon * (24 * 60 * 60) / (len(classical_results + temporal_results) * np.mean([r.execution_time for r in classical_results + temporal_results])) if classical_results + temporal_results else 0
        }
        
        return analysis
    
    def _generate_enhanced_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Génère des recommandations basées sur l'analyse statistique avancée"""
        recommendations = []
        
        # Recommandations basées sur les performances classiques
        if 'classical_routing' in stats:
            classical = stats['classical_routing']
            avg_time = classical['execution_time']['mean']
            p95_time = classical['execution_time']['percentile_95']
            
            if avg_time > 0.5:
                recommendations.append(
                    f"⚠️ **Performance des itinéraires classiques**: Temps moyen élevé ({avg_time:.3f}s). "
                    "Considérer l'implémentation d'un cache des chemins fréquents."
                )
            
            if p95_time > 1.0:
                recommendations.append(
                    f"🚨 **Latence P95 critique**: 95% des requêtes prennent moins de {p95_time:.3f}s. "
                    "Optimiser l'algorithme de Dijkstra avec des heuristiques A*."
                )
            
            memory_peak = classical['memory_usage']['max_mb']
            if memory_peak > 100:
                recommendations.append(
                    f"💾 **Consommation mémoire élevée**: Pic à {memory_peak:.1f}MB. "
                    "Implémenter un garbage collection plus agressif."
                )
        
        # Recommandations temporelles
        if 'temporal_routing' in stats:
            temporal = stats['temporal_routing']
            success_rate = temporal['success_rate']['overall']
            
            if success_rate < 95:
                recommendations.append(
                    f"⏰ **Taux de succès temporel faible**: {success_rate:.1f}%. "
                    "Améliorer la robustesse du service temporel."
                )
            
            # Analyse par créneau horaire
            for time_cat, data in temporal['success_rate']['by_time_category'].items():
                if data['avg_time'] > 2.0:
                    recommendations.append(
                        f"🕐 **Performance {time_cat}**: Temps élevé ({data['avg_time']:.3f}s). "
                        "Pré-calculer les horaires pour ce créneau."
                    )
        
        # Recommandations environnementales
        if 'environmental_impact' in stats:
            env = stats['environmental_impact']
            daily_carbon = env.get('carbon_per_day_estimate', 0)
            
            if daily_carbon > 10:  # > 10g CO2 par jour
                recommendations.append(
                    f"🌱 **Impact carbone significatif**: Estimation {daily_carbon:.1f}g CO₂/jour. "
                    "Optimiser les algorithmes pour réduire la consommation."
                )
            
            avg_energy = env.get('avg_energy_per_request', 0)
            if avg_energy > 1:  # > 1 joule par requête
                recommendations.append(
                    f"⚡ **Consommation énergétique élevée**: {avg_energy:.2f}J par requête. "
                    "Implémenter des stratégies de mise en cache."
                )
        
        # Recommandations générales de scalabilité
        recommendations.extend([
            "🚀 **Scalabilité**: Implémenter un load balancer pour distribuer la charge.",
            "📊 **Monitoring**: Ajouter des métriques temps réel (Prometheus/Grafana).",
            "🔄 **Cache distribué**: Utiliser Redis pour partager les caches entre instances.",
            "⚡ **Optimisations**: Considérer l'utilisation de WebSockets pour les mises à jour temps réel.",
            "🛡️ **Robustesse**: Implémenter des circuit breakers pour les services externes."
        ])
        
        return recommendations
        
        # Analyse des temps d'exécution
        if hasattr(self, 'results') and self.results:
            avg_time = np.mean([r.execution_time for r in self.results if hasattr(r, 'execution_time')])
            if avg_time > 1.0:
                recommendations.append("⚠️ Temps d'exécution élevé détecté - Considérer l'optimisation des algorithmes")
        
        # Analyse mémoire
        memory_usage = psutil.virtual_memory().percent
        if memory_usage > 80:
            recommendations.append("⚠️ Utilisation mémoire élevée - Optimiser la gestion mémoire et le cache")
        
        # Recommandations générales
        recommendations.extend([
            "✅ Implémenter un cache Redis pour les calculs d'itinéraires fréquents",
            "✅ Utiliser la compression gzip pour les réponses API",
            "✅ Optimiser les requêtes GTFS avec des index appropriés",
            "✅ Implémenter un système de pagination pour les grandes listes",
            "✅ Utiliser un CDN pour servir les ressources statiques",
            "✅ Monitorer les performances en production avec des métriques",
            "✅ Implémenter des tests de charge automatisés",
            "✅ Optimiser les algorithmes pour les cas d'usage fréquents"
        ])
        
        return recommendations
    
    def _generate_enhanced_markdown_report(self, results: AuditResults):
        """Génère le rapport markdown complet et détaillé"""
        report_path = "AUDIT_PERFORMANCE_RAPPORT.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"# 🚇 Audit de Performance & Impact Écologique - MetroCity\n")
            f.write(f"_Date de l'audit : {results.timestamp}_\n\n")

            f.write("## 🖥️ Informations Système\n")
            for k, v in results.system_info.items():
                f.write(f"- **{k}** : {v}\n")
            f.write("\n")

            f.write("## 🚦 Chargement des stations\n")
            f.write(f"- Temps de chargement : {results.station_loading.execution_time:.3f}s\n")
            f.write(f"- Mémoire pic : {results.station_loading.memory_peak/1024/1024:.1f}MB\n")
            f.write(f"- Empreinte carbone : {results.station_loading.carbon_footprint:.3f}g CO₂\n\n")

            f.write("## 🚇 Itinéraires classiques (simulation réaliste)\n")
            stats = results.statistical_analysis.get('classical_routing', {})
            if stats:
                f.write(f"- Nombre de tests : {stats['total_tests']}\n")
                f.write(f"- Temps moyen : {stats['execution_time']['mean']:.3f}s\n")
                f.write(f"- Temps médian : {stats['execution_time']['median']:.3f}s\n")
                f.write(f"- P95 : {stats['execution_time']['percentile_95']:.3f}s\n")
                f.write(f"- Longueur moyenne des routes : {stats['route_analysis']['avg_length']:.1f}\n")
                f.write(f"- Distribution : {stats['route_analysis']['length_distribution']}\n")
                f.write(f"- Mémoire pic max : {stats['memory_usage']['max_mb']:.1f}MB\n\n")

            f.write("## 🕘 Itinéraires temporels (simulation réaliste)\n")
            tstats = results.statistical_analysis.get('temporal_routing', {})
            if tstats:
                f.write(f"- Nombre de tests : {tstats['total_tests']}\n")
                f.write(f"- Temps moyen : {tstats['execution_time']['mean']:.3f}s\n")
                f.write(f"- Taux de succès global : {tstats['success_rate']['overall']:.1f}%\n")
                for cat, data in tstats['success_rate']['by_time_category'].items():
                    f.write(f"  - {cat} : {data['avg_time']:.3f}s sur {data['test_count']} tests\n")
                f.write("\n")

            f.write("## 👥 Tests de charge (utilisateurs concurrents)\n")
            for k, v in results.concurrent_routing.items():
                f.write(f"- {k} : {v['successful_requests']}/{v['total_requests']} succès, "
                        f"temps moyen {v['avg_response_time']:.3f}s, débit {v['throughput_rps']:.1f} req/s\n")
            f.write("\n")

            f.write("## 🌱 Impact environnemental\n")
            env = results.statistical_analysis.get('environmental_impact', {})
            if env:
                f.write(f"- Énergie totale : {env['total_energy_joules']:.2f} J\n")
                f.write(f"- Carbone total : {env['total_carbon_grams']:.2f} g CO₂\n")
                f.write(f"- Énergie moyenne par requête : {env['avg_energy_per_request']:.3f} J\n")
                f.write(f"- Estimation carbone/jour : {env['carbon_per_day_estimate']:.2f} g CO₂\n\n")

            f.write("## 💡 Recommandations\n")
            for rec in results.recommendations:
                f.write(f"- {rec}\n")
            f.write("\n")

            f.write("## 📊 RÉSUMÉ COMPLET DES PERFORMANCES\n")
            f.write("### ⏱️ Temps de chargement des stations\n")
            f.write(f"- **Temps moyen** : {results.station_loading.execution_time:.3f} secondes\n")
            f.write(f"- **Complexité** : {results.station_loading.complexity_order}\n")
            f.write(f"- **Mémoire utilisée** : {results.station_loading.memory_peak/1024/1024:.1f} MB\n")
            f.write(f"- **Consommation énergétique** : {results.station_loading.energy_consumption:.2f} J\n")
            f.write(f"- **Empreinte carbone** : {results.station_loading.carbon_footprint:.3f} g CO₂\n\n")

            f.write("### 🗺️ Calcul d'itinéraire classique (Dijkstra)\n")
            if 'classical_routing' in stats:
                classical = stats['classical_routing']
                f.write(f"- **Temps moyen** : {classical['execution_time']['mean']:.3f} secondes\n")
                f.write(f"- **Temps médian** : {classical['execution_time']['median']:.3f} secondes\n")
                f.write(f"- **P95** : {classical['execution_time']['percentile_95']:.3f} secondes\n")
                f.write(f"- **Complexité** : O((V + E) log V) où V=sommets, E=arêtes\n")
                f.write(f"- **Mémoire pic** : {classical['memory_usage']['max_mb']:.1f} MB\n")
                f.write(f"- **Longueur moyenne des routes** : {classical['route_analysis']['avg_length']:.1f} stations\n")
                f.write(f"- **Tests réussis** : {classical['total_tests']}\n\n")

            f.write("### 🕘 Calcul d'itinéraire temporel\n")
            if 'temporal_routing' in tstats:
                temporal = tstats['temporal_routing']
                f.write(f"- **Temps moyen** : {temporal['execution_time']['mean']:.3f} secondes\n")
                f.write(f"- **Temps médian** : {temporal['execution_time']['median']:.3f} secondes\n")
                f.write(f"- **P95** : {temporal['execution_time']['percentile_95']:.3f} secondes\n")
                f.write(f"- **Complexité** : O(P × S × T) où P=chemins, S=segments, T=horaires\n")
                f.write(f"- **Taux de succès global** : {temporal['success_rate']['overall']:.1f}%\n")
                f.write(f"- **Tests réussis** : {temporal['total_tests']}\n\n")

            f.write("### 🌳 Calcul de l'ACPM (Kruskal)\n")
            f.write(f"- **Temps de calcul** : {results.acpm_calculation.execution_time:.3f} secondes\n")
            f.write(f"- **Complexité** : {results.acpm_calculation.complexity_order}\n")
            f.write(f"- **Mémoire utilisée** : {results.acpm_calculation.memory_peak/1024/1024:.1f} MB\n")
            f.write(f"- **Consommation énergétique** : {results.acpm_calculation.energy_consumption:.2f} J\n")
            f.write(f"- **Empreinte carbone** : {results.acpm_calculation.carbon_footprint:.3f} g CO₂\n\n")

            f.write("### 🔗 Analyse de connexité (DFS)\n")
            f.write(f"- **Temps de calcul** : {results.connectivity_analysis.execution_time:.3f} secondes\n")
            f.write(f"- **Complexité** : {results.connectivity_analysis.complexity_order}\n")
            f.write(f"- **Mémoire utilisée** : {results.connectivity_analysis.memory_peak/1024/1024:.1f} MB\n")
            f.write(f"- **Consommation énergétique** : {results.connectivity_analysis.energy_consumption:.2f} J\n")
            f.write(f"- **Empreinte carbone** : {results.connectivity_analysis.carbon_footprint:.3f} g CO₂\n\n")

            f.write("### ⚡ Consommation énergétique par fonctionnalité\n")
            if 'environmental_impact' in env and 'energy_by_function' in env:
                energy_by_func = env['energy_by_function']
                f.write(f"- **Chargement des stations** : {energy_by_func.get('station_loading', 0):.2f} J\n")
                f.write(f"- **Itinéraires classiques** : {energy_by_func.get('classical_routing', 0):.2f} J\n")
                f.write(f"- **Itinéraires temporels** : {energy_by_func.get('temporal_routing', 0):.2f} J\n")
                f.write(f"- **Calcul ACPM** : {energy_by_func.get('acpm_calculation', 0):.2f} J\n")
                f.write(f"- **Analyse de connexité** : {energy_by_func.get('connectivity_analysis', 0):.2f} J\n")
                f.write(f"- **Énergie totale mesurée** : {env['total_energy_joules']:.2f} J\n")
                f.write(f"- **Énergie moyenne par requête** : {env['avg_energy_per_request']:.3f} J\n\n")

            f.write("### 🌍 Impact environnemental global\n")
            if 'environmental_impact' in env:
                f.write(f"- **Empreinte carbone totale** : {env['total_carbon_grams']:.2f} g CO₂\n")
                f.write(f"- **Estimation carbone/jour** : {env['carbon_per_day_estimate']:.2f} g CO₂\n")
                f.write(f"- **Projection annuelle** : {env['total_carbon_grams'] * 365 / 1000:.1f} kg CO₂\n")
                f.write(f"- **Équivalent voiture** : {env['total_carbon_grams'] * 365 / 120:.0f} km/an\n")
                f.write(f"- **Arbres nécessaires** : {env['total_carbon_grams'] * 365 / 22000:.2f} arbres/an\n\n")

            f.write("### 📈 Métriques de performance globales\n")
            if 'concurrent_requests_test' in results.overall_performance:
                perf = results.overall_performance['concurrent_requests_test']
                f.write(f"- **Requêtes simultanées testées** : {perf['total_requests']}\n")
                f.write(f"- **Taux de succès** : {perf['success_rate']:.1f}%\n")
                f.write(f"- **Temps de réponse moyen** : {perf['average_response_time']:.3f} secondes\n")
                f.write(f"- **Débit** : {perf['throughput_rps']:.1f} requêtes/seconde\n")
                f.write(f"- **Temps total de test** : {perf['total_test_time']:.2f} secondes\n\n")

            f.write("### 🔍 Analyse de complexité algorithmique\n")
            f.write("| Algorithme | Complexité | Description |\n")
            f.write("|------------|------------|-------------|\n")
            f.write("| Chargement stations | O(n) | n = nombre de stations |\n")
            f.write("| Dijkstra (classique) | O((V+E) log V) | V=sommets, E=arêtes |\n")
            f.write("| Routage temporel | O(P×S×T) | P=chemins, S=segments, T=horaires |\n")
            f.write("| Kruskal (ACPM) | O(E log E) | E = nombre d'arêtes |\n")
            f.write("| DFS (connexité) | O(V+E) | V=sommets, E=arêtes |\n\n")

            f.write("---\n")
            f.write("_Rapport généré automatiquement par l'audit MetroCity._\n")

        print(f"\n✅ Rapport généré : {report_path}\n")

def main():
    print("=" * 80)
    auditor = RealisticPerformanceAuditor()
    results = auditor.run_full_realistic_audit()
    print("\n" + "=" * 80)

if __name__ == "__main__":
    main() 