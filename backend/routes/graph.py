"""
MetroCity - Mastercamp 2025
Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
Fichier: graph.py
Description: Routes Flask pour l'accès au graphe complet du métro parisien
"""

from flask import Blueprint, jsonify
from utils.parser import load_data

graph_bp = Blueprint('graph', __name__)

@graph_bp.route('/graph', methods=['GET'])
def get_graph():
    """Retourne le graphe complet du métro."""
    graph, positions, stations = load_data()
    
    # Formater le graphe pour l'API
    formatted_graph = {}
    for station_id, neighbors in graph.items():
        formatted_graph[station_id] = {
            'name': stations[station_id]['name'],
            'neighbors': neighbors
        }
    
    return jsonify({
        'graph': formatted_graph,
        'stations_count': len(graph),
        'connections_count': sum(len(neighbors) for neighbors in graph.values()) // 2
    }) 