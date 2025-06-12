from flask import Blueprint, jsonify
from utils.parser import load_data
import logging

stations_bp = Blueprint('stations', __name__)

@stations_bp.route('/stations', methods=['GET'])
def get_stations():
    """Retourne la liste des stations avec leurs coordonnées, groupées par nom."""
    graph, positions, stations = load_data()
    station_groups = {}
    for station_id, station_data in stations.items():
        name = station_data['name']
        if name not in station_groups:
            station_groups[name] = {
                'name': name,
                'lines': set(),
                'ids': [],
                'position': None
            }
        station_groups[name]['lines'].add(station_data['line'])
        station_groups[name]['ids'].append(station_id)
        # Prendre la première position trouvée (ou améliorer pour moyenne)
        if not station_groups[name]['position'] and station_id in positions:
            station_groups[name]['position'] = positions[station_id]

    # Formater la liste finale
    stations_list = []
    for group in station_groups.values():
        stations_list.append({
            'name': group['name'],
            'lines': list(group['lines']),
            'ids': group['ids'],
            'position': group['position']
        })

    return jsonify({
        'stations': stations_list,
        'count': len(stations_list)
    }) 