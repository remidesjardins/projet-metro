#!/usr/bin/env python3
"""
MetroCity - Test Rapide de l'Audit
Script de test pour vérifier que l'audit peut s'exécuter correctement
"""

import os
import sys
import time
import traceback

# Configuration du chemin backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_imports():
    """Test des imports nécessaires"""
    print("🔍 Test des imports...")
    
    try:
        import psutil
        import numpy as np
        import requests
        print("  ✅ Dépendances système OK")
    except ImportError as e:
        print(f"  ❌ Erreur import système: {e}")
        return False
    
    try:
        from utils.parser import load_data
        from services.dijkstra import shortest_path_by_name
        from services.connexite import test_connexite
        print("  ✅ Services backend OK")
    except ImportError as e:
        print(f"  ❌ Erreur import backend: {e}")
        return False
    
    return True

def test_data_loading():
    """Test du chargement des données"""
    print("📊 Test du chargement des données...")
    
    try:
        from utils.parser import load_data
        start_time = time.time()
        graph, positions, stations = load_data()
        load_time = time.time() - start_time
        
        print(f"  ✅ Données chargées en {load_time:.3f}s")
        print(f"  📈 Stations: {len(stations)}")
        print(f"  📈 Connexions: {sum(len(neighbors) for neighbors in graph.values()) // 2}")
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur chargement: {e}")
        return False

def test_basic_algorithms():
    """Test des algorithmes de base"""
    print("🧮 Test des algorithmes de base...")
    
    try:
        # Test connexité
        from services.connexite import test_connexite
        start_time = time.time()
        is_connected, unreachable = test_connexite()
        connexite_time = time.time() - start_time
        print(f"  ✅ Connexité calculée en {connexite_time:.3f}s - Connexe: {is_connected}")
        
        # Test Dijkstra
        from services.dijkstra import shortest_path_by_name
        start_time = time.time()
        path, distance, _, _ = shortest_path_by_name("Châtelet", "République")
        dijkstra_time = time.time() - start_time
        print(f"  ✅ Dijkstra calculé en {dijkstra_time:.3f}s - Distance: {distance}s")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur algorithmes: {e}")
        traceback.print_exc()
        return False

def test_server_connection():
    """Test de connexion au serveur"""
    print("🌐 Test de connexion au serveur...")
    
    try:
        import requests
        response = requests.get("http://localhost:5050/health", timeout=5)
        if response.status_code == 200:
            print("  ✅ Serveur backend accessible")
            return True
        else:
            print(f"  ⚠️  Serveur répond mais code {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("  ⚠️  Serveur backend non accessible (normal si pas démarré)")
        return False
    except Exception as e:
        print(f"  ❌ Erreur connexion: {e}")
        return False

def main():
    """Test principal"""
    print("🧪 MetroCity - Test Rapide de l'Audit")
    print("=" * 50)
    
    tests_passed = 0
    total_tests = 4
    
    # Test 1: Imports
    if test_imports():
        tests_passed += 1
    
    # Test 2: Chargement données
    if test_data_loading():
        tests_passed += 1
    
    # Test 3: Algorithmes
    if test_basic_algorithms():
        tests_passed += 1
    
    # Test 4: Serveur
    if test_server_connection():
        tests_passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Résultats: {tests_passed}/{total_tests} tests réussis")
    
    if tests_passed == total_tests:
        print("✅ Tous les tests sont passés! L'audit peut être lancé.")
        return True
    elif tests_passed >= 3:
        print("⚠️  Plupart des tests passés. L'audit peut probablement être lancé.")
        return True
    else:
        print("❌ Trop de tests échoués. Vérifiez l'installation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 