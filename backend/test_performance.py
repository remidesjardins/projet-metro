#!/usr/bin/env python3
"""
Script de test pour mesurer les performances du cache.
"""

import time
from utils.data_manager import DataManager

def test_cache_performance():
    """Teste les performances du cache."""
    print("=== Test de Performance du Cache ===\n")
    
    # Test 1: Premier accès (depuis le cache)
    print("1. Premier accès (depuis le cache):")
    start = time.time()
    graph, positions, stations = DataManager.get_data()
    first_access = time.time() - start
    print(f"   Temps: {first_access:.4f}s")
    print(f"   Stations: {len(stations)}")
    print(f"   Connexions: {sum(len(v) for v in graph.values()) // 2}")
    print()
    
    # Test 2: Accès multiples (données en mémoire)
    print("2. Accès multiples (données en mémoire):")
    times = []
    for i in range(10):
        start = time.time()
        DataManager.get_data()
        access_time = time.time() - start
        times.append(access_time)
        print(f"   Accès {i+1}: {access_time:.4f}s")
    
    avg_time = sum(times) / len(times)
    print(f"   Moyenne: {avg_time:.4f}s")
    print(f"   Min: {min(times):.4f}s")
    print(f"   Max: {max(times):.4f}s")
    print()
    
    # Test 3: Informations sur le cache
    print("3. Informations sur le cache:")
    cache_info = DataManager.get_cache_info()
    for key, value in cache_info.items():
        print(f"   {key}: {value}")
    print()
    
    # Test 4: Comparaison avec l'ancien système
    print("4. Comparaison avec l'ancien système:")
    print(f"   Ancien temps de chargement: ~3.47s")
    print(f"   Nouveau temps (cache): {first_access:.4f}s")
    print(f"   Nouveau temps (mémoire): {avg_time:.4f}s")
    print(f"   Amélioration (cache): {3.47/first_access:.1f}x plus rapide")
    print(f"   Amélioration (mémoire): {3.47/avg_time:.1f}x plus rapide")
    print()
    
    # Test 5: Test de l'endpoint de performance
    print("5. Test de l'endpoint de performance:")
    try:
        from routes.cache import test_performance
        results = test_performance()
        print("   Endpoint fonctionnel")
    except Exception as e:
        print(f"   Erreur: {e}")

if __name__ == "__main__":
    test_cache_performance() 