"""
MetroCity - Mastercamp 2025
Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
Fichier: acpm.py
Description: Routes Flask pour le calcul de l'Arbre Couvrant de Poids Minimum (Kruskal)
"""

from flask import Blueprint, jsonify
from flask_cors import cross_origin
from services.kruskal import kruskal_mst
from utils.parser import load_data

acpm_bp = Blueprint('acpm', __name__)

@acpm_bp.route('/acpm', methods=['GET'])
@cross_origin()
def get_mst():
    """
    Calcule l'Arbre Couvrant de Poids Minimum (ACPM) du réseau de métro.
    
    Returns:
        JSON: ACPM avec arêtes, poids total et statistiques
    """
    graph, positions, stations = load_data()
    
    # Calculer l'ACPM
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
    
    edges.sort()
    mst = []
    total_weight = 0
    
    # Union-Find pour Kruskal
    parent = {s: s for s in graph}
    rank = {s: 0 for s in graph}
    
    def find(x):
        """Trouve le représentant de l'ensemble contenant x (Union-Find)."""
        if parent[x] != x:
            parent[x] = find(parent[x])  # Compression de chemin
        return parent[x]
    
    def union(x, y):
        """Unit deux ensembles contenant x et y (Union-Find)."""
        root_x = find(x)
        root_y = find(y)
        if root_x != root_y:
            if rank[root_x] < rank[root_y]:
                parent[root_x] = root_y
            elif rank[root_x] > rank[root_y]:
                parent[root_y] = root_x
            else:
                parent[root_y] = root_x
                rank[root_x] += 1
    
    for weight, s1, s2 in edges:
        if find(s1) != find(s2):  # Si pas déjà connectés
            union(s1, s2)  # Les connecter
            
            # S'assurer que le poids est un nombre
            numeric_weight = weight if isinstance(weight, (int, float)) else int(weight)
            
            mst.append({
                'from': {
                    'id': s1,
                    'name': stations[s1]['name']
                },
                'to': {
                    'id': s2,
                    'name': stations[s2]['name']
                },
                'weight': numeric_weight
            })
            total_weight += numeric_weight
            if len(mst) == len(graph) - 1:
                break
    
    return jsonify({
        'mst': mst,
        'total_weight': total_weight,
        'edges_count': len(mst)
    })
