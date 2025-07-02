from flask import Blueprint, jsonify, request
from flask_cors import cross_origin
from services.dijkstra import dijkstra
from utils.parser import load_data
from utils.error_handler import ValidationError, NotFoundError, validate_required_fields, validate_station_exists
from collections import OrderedDict
import math

shortest_path_bp = Blueprint('shortest_path', __name__)

@shortest_path_bp.route('/shortest-path', methods=['POST'])
@cross_origin()
def get_shortest_path():
    """Calcule le plus court chemin entre deux stations."""
    try:
        data = request.get_json()
        
        # Validation des champs requis
        validate_required_fields(data, ['start', 'end'])
        
        start_id = data['start']
        end_id = data['end']
        
        # Récupérer le paramètre include_rer (par défaut True)
        include_rer = data.get('include_rer', True)
        
        graph, positions, stations = load_data()
        
        # Vérifier que les stations existent
        validate_station_exists(start_id, stations)
        validate_station_exists(end_id, stations)
        
        # Si include_rer est False, créer un graphe filtré sans les connexions RER
        if not include_rer:
            filtered_graph = {}
            rer_lines = {'A', 'B', 'C', 'D', 'E'}
            
            for station_id, neighbors in graph.items():
                filtered_neighbors = set()
                station_lines = set(stations[station_id]['line'].split(',') if isinstance(stations[station_id]['line'], str) else stations[station_id]['line'])
                
                for neighbor_id in neighbors:
                    neighbor_lines = set(stations[neighbor_id]['line'].split(',') if isinstance(stations[neighbor_id]['line'], str) else stations[neighbor_id]['line'])
                    
                    # Vérifier si la connexion passe par une ligne RER
                    connection_lines = station_lines & neighbor_lines
                    if not (connection_lines & rer_lines):
                        # Pas de ligne RER dans la connexion, on peut l'inclure
                        filtered_neighbors.add(neighbor_id)
                
                if filtered_neighbors:
                    filtered_graph[station_id] = filtered_neighbors
            
            # Utiliser le graphe filtré pour le calcul
            dist, path = dijkstra(filtered_graph, start_id, end_id)
        else:
            # Utiliser le graphe complet
            dist, path = dijkstra(graph, start_id, end_id)
        
        if not path:
            raise NotFoundError('Aucun chemin trouvé entre les stations spécifiées')
        
        # Fonction pour calculer la distance entre deux points GPS (en km)
        def calculate_distance_km(lat1, lon1, lat2, lon2):
            """
            Calcule la distance entre deux points GPS avec la formule de Haversine.
            Retourne la distance en kilomètres.
            """
            if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
                return 0
            
            # Rayon de la Terre en km
            R = 6371.0
            
            # Conversion en radians
            lat1_rad = math.radians(lat1)
            lon1_rad = math.radians(lon1)
            lat2_rad = math.radians(lat2)
            lon2_rad = math.radians(lon2)
            
            # Différences
            dlat = lat2_rad - lat1_rad
            dlon = lon2_rad - lon1_rad
            
            # Formule de Haversine
            a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            distance = R * c

            return distance
        
        # Fonction pour calculer les émissions carbone
        def calculate_emissions(path, stations, positions):
            """Calcule les émissions de CO2 totales du trajet en grammes."""
            if len(path) < 2:
                return 0
            
            total_emissions = 0
            # Facteurs d'émission en g CO2/km
            emission_factors = {
                'metro': 2.8,
                'rer': 2.9,
                'bus': 19.0
            }
            
            for i in range(len(path) - 1):
                station_id = path[i]
                next_station_id = path[i + 1]
                
                # Récupérer les positions (lat, lon)
                pos1 = positions.get(station_id)
                pos2 = positions.get(next_station_id)
                
                if pos1 and pos2:
                    # pos1 et pos2 sont des [latitude, longitude]
                    lat1, lon1 = pos1[0]/1000, pos1[1]/1000
                    lat2, lon2 = pos2[0]/1000, pos2[1]/1000
                    
                    # Calculer la distance réelle
                    distance_km = calculate_distance_km(lat1, lon1, lat2, lon2)
                    
                    # Déterminer le type de transport (metro par défaut)
                    station_type = stations[station_id].get('type', 'metro')
                    emission_factor = emission_factors.get(station_type, 2.8)
                    
                    # Ajouter les émissions pour ce segment
                    total_emissions += distance_km * emission_factor
            
            return round(total_emissions, 2)

        # Nouvelle fonction utilitaire pour regrouper le chemin par ligne
        def group_path_by_line_with_labels(path, stations, positions, dist):
            """
            Retourne une liste ordonnée de dictionnaires avec labels explicites et informations détaillées sur les stations
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
                
                # Créer l'objet station avec toutes les informations
                station_info = {
                    "Nom Station": station['name'],
                    "ID": station_id,
                    "Lignes": sorted(list(lines)),
                    "Position": positions.get(station_id, None),
                    "Type": station.get('type', 'metro')
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
            
            # Ajouter la dernière station
            last_station = stations[path[-1]]
            last_station_info = {
                "Nom Station": last_station['name'],
                "ID": path[-1],
                "Lignes": sorted(list(set(last_station['line'].split(',') if isinstance(last_station['line'], str) else last_station['line']))),
                "Position": positions.get(path[-1], None),
                "Type": last_station.get('type', 'metro')
            }
            current_stations.append(last_station_info)
            result.append({
                "Ligne": current_line,
                "Stations": current_stations
            })
            
            # ✅ NOUVEAU : Calculer la durée pour chaque segment
            total_duration = dist  # Durée totale du trajet
            total_segments = sum(max(0, len(segment["Stations"]) - 1) for segment in result)
            
            for segment in result:
                stations_in_segment = max(0, len(segment["Stations"]) - 1)
                if total_segments > 0:
                    segment["Duration"] = int((stations_in_segment / total_segments) * total_duration)
                else:
                    segment["Duration"] = 0
            
            return result

        # Calculer les émissions
        emissions = calculate_emissions(path, stations, positions)
        
        # Formater le chemin
        chemin = group_path_by_line_with_labels(path, stations, positions, dist)
        
        # Compter le nombre de stations uniques
        all_station_ids = []
        for segment in chemin:
            all_station_ids.extend([station["ID"] for station in segment["Stations"]])
        unique_stations_count = len(set(all_station_ids))
        
        return jsonify({
            'chemin': chemin,
            'duration': dist,
            'emissions': emissions,
            'stations_count': unique_stations_count
        })
        
    except (ValidationError, NotFoundError):
        # Ces erreurs sont déjà gérées par les gestionnaires d'erreurs
        raise
    except Exception as e:
        # Log l'erreur et la relancer pour le gestionnaire générique
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors du calcul du plus court chemin: {str(e)}", exc_info=True)
        raise