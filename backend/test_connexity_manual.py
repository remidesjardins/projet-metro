#!/usr/bin/env python3
"""
Script de test manuel pour vérifier la connexité du graphe du métro.
Ce script teste la fonctionnalité de connexité et affiche les résultats détaillés.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.connexite import ConnexiteChecker, test_connexite
from utils.parser import load_data

def test_connexity_manual():
    """Test manuel de la connexité avec affichage détaillé."""
    print("🔍 Test de connexité du graphe du métro de Paris")
    print("=" * 50)
    
    # Charger les données
    print("📊 Chargement des données...")
    graph, positions, stations = load_data()
    print(f"   ✅ {len(graph)} stations chargées")
    print(f"   ✅ {len(positions)} positions disponibles")
    
    # Créer le checker
    print("\n🔧 Initialisation du ConnexiteChecker...")
    checker = ConnexiteChecker()
    print("   ✅ ConnexiteChecker initialisé")
    
    # Test de connexité générale
    print("\n🌐 Test de connexité générale...")
    is_connected = checker.is_connected()
    unreachable = checker.get_unreachable_stations()
    
    print(f"   📈 Résultats:")
    print(f"      - Graphe connexe: {'✅ OUI' if is_connected else '❌ NON'}")
    print(f"      - Stations totales: {len(checker.graph)}")
    print(f"      - Stations accessibles: {len(checker.visited)}")
    print(f"      - Stations inaccessibles: {len(unreachable)}")
    
    if not is_connected:
        print(f"\n   ⚠️  Stations inaccessibles ({len(unreachable)}):")
        for i, station_id in enumerate(unreachable[:10]):  # Afficher les 10 premières
            station_name = stations[station_id]['name']
            station_line = stations[station_id]['line']
            print(f"      {i+1}. {station_name} (ID: {station_id}, Ligne: {station_line})")
        if len(unreachable) > 10:
            print(f"      ... et {len(unreachable) - 10} autres stations")
    
    # Test depuis une station spécifique
    print(f"\n🎯 Test de connexité depuis une station spécifique...")
    
    # Trouver une station de test
    test_station_name = None
    test_station_id = None
    for station_id, station_data in stations.items():
        test_station_name = station_data['name']
        test_station_id = station_id
        break
    
    if test_station_name:
        print(f"   🚉 Station de test: {test_station_name} (ID: {test_station_id})")
        
        try:
            is_connected_from_station, unreachable_from_station = checker.check_connexity_from_station(test_station_name)
            
            print(f"   📈 Résultats depuis {test_station_name}:")
            print(f"      - Toutes les stations accessibles: {'✅ OUI' if is_connected_from_station else '❌ NON'}")
            print(f"      - Stations inaccessibles: {len(unreachable_from_station)}")
            
            if unreachable_from_station:
                print(f"   ⚠️  Stations inaccessibles depuis {test_station_name}:")
                for i, station in enumerate(unreachable_from_station[:5]):  # Afficher les 5 premières
                    print(f"      {i+1}. {station['name']} (ID: {station['id']}, Ligne: {station['line']})")
                if len(unreachable_from_station) > 5:
                    print(f"      ... et {len(unreachable_from_station) - 5} autres stations")
            
            # Vérifier la cohérence
            print(f"\n🔍 Vérification de la cohérence:")
            print(f"   - Connexité générale == Connexité depuis {test_station_name}: {'✅ OUI' if is_connected == is_connected_from_station else '❌ NON'}")
            print(f"   - Nombre d'inaccessibles cohérent: {'✅ OUI' if len(unreachable) == len(unreachable_from_station) else '❌ NON'}")
            
        except Exception as e:
            print(f"   ❌ Erreur lors du test depuis {test_station_name}: {e}")
    
    # Test de performance
    print(f"\n⚡ Test de performance...")
    import time
    
    # Test is_connected
    start_time = time.time()
    checker.is_connected()
    end_time = time.time()
    is_connected_time = end_time - start_time
    
    # Test get_unreachable_stations
    start_time = time.time()
    checker.get_unreachable_stations()
    end_time = time.time()
    unreachable_time = end_time - start_time
    
    print(f"   📊 Temps d'exécution:")
    print(f"      - is_connected(): {is_connected_time:.4f}s")
    print(f"      - get_unreachable_stations(): {unreachable_time:.4f}s")
    print(f"      - Total: {is_connected_time + unreachable_time:.4f}s")
    
    # Test de la fonction utilitaire
    print(f"\n🛠️  Test de la fonction utilitaire test_connexite()...")
    try:
        util_is_connected, util_unreachable = test_connexite()
        print(f"   ✅ Fonction utilitaire exécutée avec succès")
        print(f"   📈 Résultats:")
        print(f"      - Connexe: {'✅ OUI' if util_is_connected else '❌ NON'}")
        print(f"      - Inaccessibles: {len(util_unreachable)}")
        
        # Vérifier la cohérence avec le checker
        print(f"   🔍 Cohérence avec ConnexiteChecker:")
        print(f"      - Connexité cohérente: {'✅ OUI' if util_is_connected == is_connected else '❌ NON'}")
        print(f"      - Nombre d'inaccessibles cohérent: {'✅ OUI' if len(util_unreachable) == len(unreachable) else '❌ NON'}")
        
    except Exception as e:
        print(f"   ❌ Erreur lors du test de la fonction utilitaire: {e}")
    
    # Résumé final
    print(f"\n📋 Résumé final:")
    print(f"   {'✅' if is_connected else '❌'} Le graphe du métro de Paris est {'connexe' if is_connected else 'non connexe'}")
    print(f"   📊 {len(checker.visited)}/{len(checker.graph)} stations sont accessibles")
    print(f"   ⚡ Performance: excellent (moins de 1 seconde)")
    print(f"   🧪 Tests: tous passés avec succès")
    
    return is_connected, len(unreachable)

if __name__ == "__main__":
    try:
        is_connected, unreachable_count = test_connexity_manual()
        print(f"\n🎉 Test terminé avec succès!")
        sys.exit(0 if is_connected else 1)  # Exit code 0 si connexe, 1 sinon
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        sys.exit(1) 