"""
MetroCity - Mastercamp 2025
Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
Fichier: itineraire.py
Description: Routes Flask pour le calcul d'itinéraires avec optimisation multi-critères
"""

from flask import Blueprint, jsonify, request
from services.dijkstra import shortest_path_by_name
from utils.parser import load_data
from typing import Dict, List, Any, Tuple

itineraire_bp = Blueprint('itineraire', __name__)

def format_path_details(path: List[str], stations: Dict[str, Dict[str, Any]], positions: Dict[str, Tuple[int, int]]) -> List[Dict[str, Any]]:
    """
    Formate les détails du chemin pour l'API en gérant les lignes multiples des stations.

    Args:
        path: Liste des IDs des stations du chemin.
        stations: Dictionnaire des stations avec leurs informations.
        positions: Dictionnaire des positions des stations.

    Returns:
        Liste de dictionnaires contenant les détails de chaque étape.
    """
    details = []
    graph, _, _ = load_data()  # Récupérer le graphe pour les temps entre stations.

    # Fonction utilitaire pour trouver la meilleure ligne partagée entre deux stations.
    def find_common_line(station_id1, station_id2, current_line=None):
        lines1 = stations[station_id1]['line']
        lines2 = stations[station_id2]['line']
        common_lines = set(lines1) & set(lines2)

        # Si une ligne courante est définie, favoriser le maintien sur cette ligne si elle est disponible.
        if current_line and current_line in common_lines:
            return current_line
        # Sinon, retourner une ligne commune arbitrairement (ou optimiser ici si nécessaire).
        return min(common_lines, default=None)  # Retourne None si pas de ligne commune.

    current_line = None  # Ligne courante suivie.

    for i, station_id in enumerate(path):
        station_info = stations[station_id]
        position = positions.get(station_id, (0, 0))

        # Définir l'étape courante.
        step = {
            'id': station_id,
            'name': station_info['name'],
            'lines': station_info['line'],
            'is_terminus': station_info['terminus'],
            'x': position[0],
            'y': position[1],
        }

        # Pour éviter tout problème avec la station de départ
        if i == 0:
            # Sélectionner la ligne optimale pour la station initiale.
            current_line = step['lines'][0] if len(step['lines']) == 1 else min(step['lines'])
            step['line'] = current_line
        else:
            prev_station_id = path[i - 1]
            prev_station = stations[prev_station_id]

            # Trouver la meilleure ligne commune avec la station précédente.
            optimal_line = find_common_line(prev_station_id, station_id, current_line)
            step['line'] = optimal_line

            # Ajouter un changement de ligne si nécessaire.
            if current_line != optimal_line:
                step['line_change'] = {
                    'from': current_line,
                    'to': optimal_line
                }
                current_line = optimal_line  # Mettre à jour la ligne courante.

            # Ajouter le temps entre la station précédente et celle-ci.
            if prev_station_id in graph and station_id in graph[prev_station_id]:
                step['time'] = graph[prev_station_id][station_id]  # Temps en secondes.

        details.append(step)
    return details

@itineraire_bp.route('/itineraire', methods=['POST'])
def get_itineraire():
    """
    Route pour calculer l'itinéraire entre deux stations.

    Body attendu:
    {
        "start": "Nom de la station de départ",
        "end": "Nom de la station d'arrivée"
    }

    Returns:
    {
        "path": [
            {
                "id": "0000",
                "name": "Nom de la station",
                "line": "1",
                "is_terminus": false,
                "line_change": {
                    "from": "1",
                    "to": "4"
                }
            },
            ...
        ],
        "total_time": 300,  # en secondes
        "start_station": {
            "id": "0000",
            "name": "Nom de la station de départ",
            "line": "1"
        },
        "end_station": {
            "id": "0001",
            "name": "Nom de la station d'arrivée",
            "line": "4"
        }
    }
    """
    try:
        data = request.get_json()
        if not data or 'start' not in data or 'end' not in data:
            return jsonify({
                'error': 'Données manquantes. Veuillez fournir "start" et "end"'
            }), 400

        start_name = data['start']
        end_name = data['end']

        # Calculer l'itinéraire
        path, total_time, start_id, end_id = shortest_path_by_name(start_name, end_name)

        # Charger les données des stations pour les détails
        _, positions, stations = load_data()

        # Formater la réponse
        response = {
            'path': format_path_details(path, stations, positions),
            'total_time': total_time,
            'start_station': {
                'id': start_id,
                'name': stations[start_id]['name'],
                'line': stations[start_id]['line'],
                'x': positions[start_id][0],
                'y': positions[start_id][1]
            },
            'end_station': {
                'id': end_id,
                'name': stations[end_id]['name'],
                'line': stations[end_id]['line'],
                'x': positions[end_id][0],
                'y': positions[end_id][1]
            }
        }

        return jsonify(response)

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Erreur serveur: {str(e)}'}), 500

@itineraire_bp.route('/stations', methods=['GET'])
def get_stations_list():
    """
    Route pour obtenir la liste de toutes les stations uniques.

    Returns:
    {
        "stations": [
            {
                "name": "Nom de la station",
                "lines": ["1", "4", "7"],  # toutes les lignes qui desservent cette station
                "is_terminus": false
            },
            ...
        ]
    }
    """
    try:
        _, _, stations = load_data()

        # Créer un dictionnaire pour regrouper les stations par nom
        stations_by_name = {}
        for station_id, station_data in stations.items():
            name = station_data['name']
            if name not in stations_by_name:
                stations_by_name[name] = {
                    'name': name,
                    'lines': set(),
                    'is_terminus': False
                }
            stations_by_name[name]['lines'].add(station_data['line'])
            stations_by_name[name]['is_terminus'] |= station_data['terminus']

        # Convertir les sets en listes pour la sérialisation JSON
        response = {
            'stations': [
                {
                    'name': data['name'],
                    'lines': sorted(list(data['lines'])),
                    'is_terminus': data['is_terminus']
                }
                for data in stations_by_name.values()
            ]
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({'error': f'Erreur serveur: {str(e)}'}), 500