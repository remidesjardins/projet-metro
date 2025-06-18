from flask import Blueprint, jsonify, request
from services.dijkstra import dijkstra
from utils.parser import load_data
from collections import OrderedDict

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
    
    # Nouvelle fonction utilitaire pour regrouper le chemin par ligne
    def group_path_by_line_with_labels(path, stations, positions):
        """
        Retourne une liste ordonnée de dictionnaires avec labels explicites et informations détaillées sur les stations :
        [
          {
            "Ligne": "7",
            "Stations": [
              {
                "Nom Station": "Villejuif - Louis Aragon",
                "ID": "0306",
                "Lignes": ["7"],
                "Position": [x, y],
                "Est Terminus": false
              },
              ...
            ]
          },
          ...
        ]
        """
        if not path:
            return []
        result = []
        current_line = None
        current_stations = []
        
        for i in range(len(path) - 1):
            station_id = path[i]
            next_station_id = path[i + 1]
            station = stations[station_id]
            next_station = stations[next_station_id]
            lines = set(station['line'].split(',') if isinstance(station['line'], str) else station['line'])
            next_lines = set(next_station['line'].split(',') if isinstance(next_station['line'], str) else next_station['line'])
            common_lines = lines & next_lines
            
            # Choisir la ligne commune (celle du trajet)
            chosen_line = None
            if current_line and current_line in common_lines:
                chosen_line = current_line
            elif common_lines:
                chosen_line = list(common_lines)[0]
            else:
                # Cas rare : pas de ligne commune, on prend la première de la station courante
                chosen_line = list(lines)[0]
            
            # Créer l'objet station avec toutes les informations (Nom Station en premier)
            station_info = {
                "Nom Station": station['name'],
                "ID": station_id,
                "Lignes": sorted(list(lines)),
                "Position": positions.get(station_id, None),
                "Type": station.get('type', 'metro')  # 'metro' par défaut
            }
            
            # Si on change de ligne
            if current_line is not None and chosen_line != current_line:
                # Ajouter la station de correspondance à la fin de la ligne précédente
                current_stations.append(station_info)
                result.append({
                    "Ligne": current_line,
                    "Stations": current_stations
                })
                # Nouvelle ligne, on commence par la station de correspondance
                current_stations = [station_info]
            elif current_line is None:
                # Première ligne
                current_stations = [station_info]
            else:
                current_stations.append(station_info)
            current_line = chosen_line
        
        # Ajouter la dernière station au dernier tronçon
        last_station = stations[path[-1]]
        last_station_info = {
            "Nom Station": last_station['name'],
            "ID": path[-1],
            "Lignes": sorted(list(set(last_station['line'].split(',') if isinstance(last_station['line'], str) else last_station['line']))),
            "Position": positions.get(path[-1], None),
            "Type": last_station.get('type', 'metro')  # 'metro' par défaut
        }
        current_stations.append(last_station_info)
        result.append({
            "Ligne": current_line,
            "Stations": current_stations
        })
        return result

    # Nouveau format groupé par ligne avec labels et informations détaillées
    path_by_line = group_path_by_line_with_labels(path, stations, positions)

    return jsonify({
        'chemin': path_by_line,
        'duration': dist,
        'stations_count': len(path)
    }) 