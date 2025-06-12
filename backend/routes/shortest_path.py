from flask import Blueprint, jsonify, request
from services.dijkstra import dijkstra
from utils.parser import load_data

shortest_path_bp = Blueprint('shortest_path', __name__)

@shortest_path_bp.route('/shortest-path', methods=['POST'])
def get_shortest_path():
    """Calcule le plus court chemin entre deux stations."""
    data = request.get_json()
    
    if not data or 'start' not in data or 'end' not in data:
        return jsonify({
            'error': 'Missing required parameters: start and end station IDs'
        }), 400
    
    start_id = data['start']
    end_id = data['end']
    
    graph, positions, stations = load_data()
    
    # Vérifier que les stations existent
    if start_id not in stations or end_id not in stations:
        return jsonify({
            'error': 'Invalid station ID(s)'
        }), 400
    
    # Calculer le plus court chemin
    dist, path = dijkstra(graph, start_id, end_id)
    
    if not path:
        return jsonify({
            'error': 'No path found between the specified stations'
        }), 404
    
    # Formater le chemin pour la réponse
    formatted_path = []
    for station_id in path:
        formatted_path.append({
            'id': station_id,
            'name': stations[station_id]['name'],
            'line': stations[station_id]['line'],
            'position': positions.get(station_id, None)
        })
    
    return jsonify({
        'path': formatted_path,
        'duration': dist,
        'stations_count': len(path)
    }) 