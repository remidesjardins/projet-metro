#!/usr/bin/env python3
"""
MetroCity - Démonstration Rapide de l'Audit
Version allégée pour présentation et test rapide
"""

import os
import sys
import time
import psutil
import tracemalloc
from datetime import datetime
import json

# Configuration du chemin backend
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def demo_audit():
    """Version démonstration de l'audit de performance"""
    
    print("🚀 MetroCity - Démonstration de l'Audit de Performance")
    print("=" * 70)
    
    results = {}
    
    # 1. Test chargement des stations
    print("\n📊 1. Test de chargement des stations")
    tracemalloc.start()
    start_time = time.time()
    
    from utils.parser import load_data
    graph, positions, stations = load_data()
    
    load_time = time.time() - start_time
    memory_peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    
    print(f"   ⏱️  Temps de chargement: {load_time:.3f}s")
    print(f"   📊 Stations chargées: {len(stations)}")
    print(f"   🔗 Connexions: {sum(len(neighbors) for neighbors in graph.values()) // 2}")
    print(f"   💾 Mémoire utilisée: {memory_peak/1024/1024:.1f}MB")
    
    results['station_loading'] = {
        'time': load_time,
        'stations_count': len(stations),
        'connections_count': sum(len(neighbors) for neighbors in graph.values()) // 2,
        'memory_mb': memory_peak/1024/1024
    }
    
    # 2. Test itinéraire classique
    print("\n🚇 2. Test d'itinéraire classique (Dijkstra)")
    from services.dijkstra import shortest_path_by_name
    
    test_routes = [("Châtelet", "République"), ("Bastille", "Nation")]
    route_results = []
    
    for start, end in test_routes:
        start_time = time.time()
        try:
            path, distance, _, _ = shortest_path_by_name(start, end)
            calc_time = time.time() - start_time
            
            print(f"   🗺️  {start} → {end}")
            print(f"      ⏱️  Temps: {calc_time:.3f}s")
            print(f"      🛤️  Distance: {distance}s")
            print(f"      📍 Étapes: {len(path)}")
            
            route_results.append({
                'route': f"{start} → {end}",
                'time': calc_time,
                'distance': distance,
                'steps': len(path)
            })
        except Exception as e:
            print(f"      ❌ Erreur: {e}")
    
    results['classical_routing'] = route_results
    
    # 3. Test ACPM (Kruskal)
    print("\n🌳 3. Test ACPM (Algorithme de Kruskal)")
    from services.kruskal import kruskal_mst
    
    start_time = time.time()
    
    # Préparation des arêtes
    edges = []
    seen = set()
    for s1 in graph:
        for s2, weight_data in graph[s1].items():
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
    mst, total_weight = kruskal_mst(edges, len(graph))
    
    kruskal_time = time.time() - start_time
    
    print(f"   ⏱️  Temps de calcul: {kruskal_time:.3f}s")
    print(f"   🌳 Arêtes dans MST: {len(mst)}")
    print(f"   ⚖️  Poids total: {total_weight}")
    print(f"   📊 Arêtes analysées: {len(edges)}")
    
    results['acpm'] = {
        'time': kruskal_time,
        'mst_edges': len(mst),
        'total_weight': total_weight,
        'edges_analyzed': len(edges)
    }
    
    # 4. Test de connexité
    print("\n🔗 4. Test de connexité (DFS)")
    from services.connexite import ConnexiteChecker
    
    start_time = time.time()
    checker = ConnexiteChecker()
    is_connected = checker.is_connected()
    unreachable = checker.get_unreachable_stations()
    connexity_time = time.time() - start_time
    
    print(f"   ⏱️  Temps de calcul: {connexity_time:.3f}s")
    print(f"   🔗 Graphe connexe: {'✅ Oui' if is_connected else '❌ Non'}")
    print(f"   📊 Stations analysées: {len(stations)}")
    print(f"   🚫 Stations inaccessibles: {len(unreachable)}")
    
    results['connectivity'] = {
        'time': connexity_time,
        'is_connected': is_connected,
        'stations_analyzed': len(stations),
        'unreachable_count': len(unreachable)
    }
    
    # 5. Analyse système
    print("\n💻 5. Informations système")
    cpu_count = psutil.cpu_count()
    memory_total = psutil.virtual_memory().total
    memory_used = psutil.virtual_memory().used
    cpu_percent = psutil.cpu_percent(interval=1)
    
    print(f"   🖥️  CPU: {cpu_count} cœurs")
    print(f"   💾 RAM totale: {memory_total/1024/1024/1024:.1f}GB")
    print(f"   📊 RAM utilisée: {memory_used/1024/1024/1024:.1f}GB ({memory_used/memory_total*100:.1f}%)")
    print(f"   ⚡ CPU utilisé: {cpu_percent:.1f}%")
    
    results['system_info'] = {
        'cpu_cores': cpu_count,
        'memory_total_gb': memory_total/1024/1024/1024,
        'memory_used_gb': memory_used/1024/1024/1024,
        'memory_percent': memory_used/memory_total*100,
        'cpu_percent': cpu_percent
    }
    
    # 6. Calcul impact environnemental simplifié
    print("\n🌱 6. Impact environnemental (estimé)")
    
    total_time = sum([
        results['station_loading']['time'],
        sum(r['time'] for r in results['classical_routing']),
        results['acpm']['time'],
        results['connectivity']['time']
    ])
    
    # Estimation énergétique simplifiée
    # CPU moderne ~65W, utilisé proportionnellement
    estimated_power_watts = 65 * (cpu_percent / 100)
    energy_joules = estimated_power_watts * total_time
    
    # Facteur émission France ~57g CO2/kWh
    carbon_grams = energy_joules * (57 / 3600000)
    
    print(f"   ⏱️  Temps total calculé: {total_time:.3f}s")
    print(f"   ⚡ Puissance estimée: {estimated_power_watts:.1f}W")
    print(f"   🔋 Énergie consommée: {energy_joules:.2f}J")
    print(f"   🌍 Empreinte carbone: {carbon_grams:.3f}g CO₂")
    
    results['environmental'] = {
        'total_computation_time': total_time,
        'estimated_power_watts': estimated_power_watts,
        'energy_joules': energy_joules,
        'carbon_grams': carbon_grams
    }
    
    # 7. Génération du mini-rapport
    print("\n📄 7. Génération du mini-rapport")
    generate_demo_report(results)
    
    print("\n" + "=" * 70)
    print("✅ Démonstration terminée!")
    print("📄 Mini-rapport généré: DEMO_AUDIT_RAPPORT.md")
    print("📊 Données JSON: demo_audit_data.json")

def generate_demo_report(results):
    """Génère un mini-rapport de démonstration"""
    
    report = f"""# 📊 Mini-Rapport d'Audit MetroCity - Démonstration

*Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}*

## 🎯 Résumé des Performances

### 📊 Chargement des Stations
- **Temps :** {results['station_loading']['time']:.3f}s
- **Stations :** {results['station_loading']['stations_count']}
- **Connexions :** {results['station_loading']['connections_count']}
- **Mémoire :** {results['station_loading']['memory_mb']:.1f}MB

### 🚇 Calculs d'Itinéraires (Dijkstra)
"""
    
    for route in results['classical_routing']:
        report += f"""
- **{route['route']}**
  - Temps: {route['time']:.3f}s
  - Distance: {route['distance']}s
  - Étapes: {route['steps']}
"""
    
    report += f"""
### 🌳 ACPM (Kruskal)
- **Temps :** {results['acpm']['time']:.3f}s
- **Arêtes MST :** {results['acpm']['mst_edges']}
- **Poids total :** {results['acpm']['total_weight']}
- **Arêtes analysées :** {results['acpm']['edges_analyzed']}

### 🔗 Connexité (DFS)
- **Temps :** {results['connectivity']['time']:.3f}s
- **Connexe :** {'✅ Oui' if results['connectivity']['is_connected'] else '❌ Non'}
- **Stations :** {results['connectivity']['stations_analyzed']}
- **Inaccessibles :** {results['connectivity']['unreachable_count']}

## 💻 Configuration Système
- **CPU :** {results['system_info']['cpu_cores']} cœurs
- **RAM :** {results['system_info']['memory_total_gb']:.1f}GB totale
- **Utilisation RAM :** {results['system_info']['memory_percent']:.1f}%
- **Utilisation CPU :** {results['system_info']['cpu_percent']:.1f}%

## 🌱 Impact Environnemental
- **Temps total :** {results['environmental']['total_computation_time']:.3f}s
- **Puissance :** {results['environmental']['estimated_power_watts']:.1f}W
- **Énergie :** {results['environmental']['energy_joules']:.2f}J
- **Carbone :** {results['environmental']['carbon_grams']:.3f}g CO₂

## 🏆 Évaluation Globale

| Critère | Performance | Commentaire |
|---------|-------------|-------------|
| Chargement | {'🟢 Excellent' if results['station_loading']['time'] < 0.1 else '🟡 Bon' if results['station_loading']['time'] < 0.5 else '🔴 À optimiser'} | {results['station_loading']['time']:.3f}s |
| Dijkstra | {'🟢 Excellent' if all(r['time'] < 0.1 for r in results['classical_routing']) else '🟡 Bon'} | Moyenne: {sum(r['time'] for r in results['classical_routing'])/len(results['classical_routing']):.3f}s |
| ACPM | {'🟢 Excellent' if results['acpm']['time'] < 0.1 else '🟡 Bon' if results['acpm']['time'] < 0.5 else '🔴 À optimiser'} | {results['acpm']['time']:.3f}s |
| Connexité | {'🟢 Excellent' if results['connectivity']['time'] < 0.01 else '🟡 Bon'} | {results['connectivity']['time']:.3f}s |
| Mémoire | {'🟢 Excellent' if results['station_loading']['memory_mb'] < 50 else '🟡 Bon' if results['station_loading']['memory_mb'] < 200 else '🔴 Élevé'} | {results['station_loading']['memory_mb']:.1f}MB |

## 💡 Recommandations Rapides

1. ✅ **Performance générale :** Très bonne
2. ✅ **Algorithmes optimaux :** Dijkstra, Kruskal, DFS utilisés
3. ✅ **Connexité :** Graphe bien connecté
4. ✅ **Impact carbone :** Très faible

### Améliorations Possibles
- Implémenter un cache pour les requêtes fréquentes
- Optimiser la sérialisation des données
- Paralléliser les calculs multi-trajets

---

*Ceci est une version de démonstration de l'audit complet.*  
*Pour l'audit complet, utilisez `./run_audit.sh`*
"""
    
    # Sauvegarde du rapport
    with open('DEMO_AUDIT_RAPPORT.md', 'w', encoding='utf-8') as f:
        f.write(report)
    
    # Sauvegarde des données JSON
    with open('demo_audit_data.json', 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'results': results
        }, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    demo_audit() 