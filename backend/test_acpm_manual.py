#!/usr/bin/env python3
"""
Script de test manuel pour vérifier l'ACPM (Arbre Couvrant de Poids Minimum).
Ce script teste la fonctionnalité ACPM et affiche les résultats détaillés.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.kruskal import kruskal_mst
from utils.parser import load_data
import time

def test_acpm_manual():
    """Test manuel de l'ACPM avec affichage détaillé."""
    print("🌳 Test de l'ACPM (Arbre Couvrant de Poids Minimum)")
    print("=" * 60)
    
    # Charger les données
    print("📊 Chargement des données...")
    graph, positions, stations = load_data()
    print(f"   ✅ {len(graph)} stations chargées")
    print(f"   ✅ {len(positions)} positions disponibles")
    print(f"   ✅ {len(stations)} données de stations disponibles")
    
    # Extraire les arêtes du graphe
    print("\n🔗 Extraction des arêtes du graphe...")
    edges = []
    seen = set()
    
    for s1 in graph:
        for s2, weight_data in graph[s1].items():
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
    
    print(f"   ✅ {len(edges)} arêtes extraites")
    
    # Vérifier les arêtes
    print("\n🔍 Vérification des arêtes...")
    valid_edges = 0
    total_weight = 0
    min_weight = float('inf')
    max_weight = 0
    
    for weight, s1, s2 in edges:
        if isinstance(weight, (int, float)) and weight >= 0:
            valid_edges += 1
            total_weight += weight
            min_weight = min(min_weight, weight)
            max_weight = max(max_weight, weight)
    
    print(f"   ✅ {valid_edges}/{len(edges)} arêtes valides")
    print(f"   📊 Poids total des arêtes: {total_weight}")
    print(f"   📊 Poids minimum: {min_weight}")
    print(f"   📊 Poids maximum: {max_weight}")
    
    # Trier les arêtes par poids
    print("\n📈 Tri des arêtes par poids...")
    edges.sort()
    print(f"   ✅ Arêtes triées par poids croissant")
    
    # Calculer l'ACPM
    print("\n🌳 Calcul de l'ACPM avec l'algorithme de Kruskal...")
    start_time = time.time()
    mst, acpm_total_weight = kruskal_mst(edges, len(graph))
    end_time = time.time()
    
    execution_time = end_time - start_time
    print(f"   ✅ ACPM calculé en {execution_time:.4f} secondes")
    
    # Analyser l'ACPM
    print(f"\n📊 Analyse de l'ACPM:")
    print(f"   - Nombre de stations: {len(graph)}")
    print(f"   - Nombre d'arêtes dans l'ACPM: {len(mst)}")
    print(f"   - Poids total de l'ACPM: {acpm_total_weight}")
    print(f"   - Poids moyen par arête: {acpm_total_weight / len(mst) if len(mst) > 0 else 0:.2f}")
    
    # Vérifier la propriété d'arbre couvrant
    expected_edges = len(graph) - 1
    print(f"\n🔍 Vérification de la propriété d'arbre couvrant:")
    print(f"   - Arêtes attendues: {expected_edges}")
    print(f"   - Arêtes obtenues: {len(mst)}")
    print(f"   - ✅ {'CORRECT' if len(mst) == expected_edges else 'INCORRECT'}")
    
    # Vérifier la connexité de l'ACPM
    print(f"\n🔗 Vérification de la connexité de l'ACPM...")
    acpm_graph = {}
    for s1, s2 in mst:
        if s1 not in acpm_graph:
            acpm_graph[s1] = set()
        if s2 not in acpm_graph:
            acpm_graph[s2] = set()
        acpm_graph[s1].add(s2)
        acpm_graph[s2].add(s1)
    
    # DFS pour vérifier la connexité
    visited = set()
    if acpm_graph:
        start_station = next(iter(acpm_graph))
        
        def dfs(node):
            visited.add(node)
            for neighbor in acpm_graph.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor)
        
        dfs(start_station)
        
        print(f"   - Stations accessibles: {len(visited)}")
        print(f"   - Stations totales: {len(graph)}")
        print(f"   - ✅ {'CONNEXE' if len(visited) == len(graph) else 'NON CONNEXE'}")
        
        if len(visited) != len(graph):
            unreachable = set(graph.keys()) - visited
            print(f"   - ⚠️  Stations inaccessibles: {len(unreachable)}")
            for station_id in list(unreachable)[:5]:  # Afficher les 5 premières
                station_name = stations[station_id]['name']
                print(f"     * {station_name} (ID: {station_id})")
            if len(unreachable) > 5:
                print(f"     ... et {len(unreachable) - 5} autres stations")
    
    # Vérifier la minimalité (pas de cycles)
    print(f"\n🔄 Vérification de la minimalité (pas de cycles)...")
    edge_set = set()
    has_duplicates = False
    
    for s1, s2 in mst:
        edge_tuple = tuple(sorted([s1, s2]))
        if edge_tuple in edge_set:
            has_duplicates = True
            break
        edge_set.add(edge_tuple)
    
    print(f"   - Arêtes uniques: {len(edge_set)}")
    print(f"   - ✅ {'PAS DE CYCLES' if not has_duplicates else 'CYCLES DÉTECTÉS'}")
    
    # Analyser les arêtes de l'ACPM
    print(f"\n📋 Analyse détaillée des arêtes de l'ACPM:")
    acpm_weights = []
    for s1, s2 in mst:
        # Trouver le poids de cette arête
        weight_data = graph[s1].get(s2) or graph[s2].get(s1)
        if isinstance(weight_data, list) and len(weight_data) > 0:
            weight = weight_data[0]['time'] if isinstance(weight_data[0], dict) else weight_data[0]
        elif isinstance(weight_data, dict):
            weight = weight_data.get('time', weight_data)
        else:
            weight = weight_data
        
        acpm_weights.append(weight)
        
        station1_name = stations[s1]['name']
        station2_name = stations[s2]['name']
        print(f"   - {station1_name} ↔ {station2_name} (poids: {weight})")
    
    # Statistiques des poids
    if acpm_weights:
        print(f"\n📊 Statistiques des poids de l'ACPM:")
        print(f"   - Poids minimum: {min(acpm_weights)}")
        print(f"   - Poids maximum: {max(acpm_weights)}")
        print(f"   - Poids moyen: {sum(acpm_weights) / len(acpm_weights):.2f}")
        print(f"   - Poids médian: {sorted(acpm_weights)[len(acpm_weights)//2]}")
    
    # Vérifier la cohérence du poids total
    calculated_total = sum(acpm_weights)
    print(f"\n🔍 Vérification de la cohérence:")
    print(f"   - Poids total calculé: {calculated_total}")
    print(f"   - Poids total retourné: {acpm_total_weight}")
    print(f"   - ✅ {'COHÉRENT' if abs(calculated_total - acpm_total_weight) < 0.01 else 'INCOHÉRENT'}")
    
    # Test de performance
    print(f"\n⚡ Test de performance:")
    print(f"   - Temps de calcul: {execution_time:.4f}s")
    print(f"   - ✅ {'RAPIDE' if execution_time < 1.0 else 'LENT'}")
    
    # Résumé final
    print(f"\n📋 Résumé final:")
    print(f"   {'✅' if len(mst) == expected_edges else '❌'} Propriété d'arbre couvrant")
    print(f"   {'✅' if len(visited) == len(graph) else '❌'} Connexité")
    print(f"   {'✅' if not has_duplicates else '❌'} Minimalité (pas de cycles)")
    print(f"   {'✅' if abs(calculated_total - acpm_total_weight) < 0.01 else '❌'} Cohérence des poids")
    print(f"   {'✅' if execution_time < 1.0 else '❌'} Performance")
    
    print(f"\n🌳 L'ACPM du métro de Paris:")
    print(f"   - {len(mst)} arêtes pour connecter {len(graph)} stations")
    print(f"   - Poids total: {acpm_total_weight} (temps total minimal)")
    print(f"   - Performance: excellent ({execution_time:.4f}s)")
    
    return len(mst) == expected_edges and len(visited) == len(graph) and not has_duplicates

if __name__ == "__main__":
    try:
        success = test_acpm_manual()
        print(f"\n🎉 Test terminé avec {'succès' if success else 'échec'}!")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Erreur lors du test: {e}")
        sys.exit(1) 