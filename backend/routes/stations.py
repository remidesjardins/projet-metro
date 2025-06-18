from flask import Blueprint, jsonify, request
from utils.parser import load_data
import logging
import time

logger = logging.getLogger(__name__)
stations_bp = Blueprint('stations', __name__)

@stations_bp.route('/stations', methods=['GET', 'HEAD'])
def get_stations():
    """Retourne la liste des stations avec leurs coordonnées, groupées par nom."""
    start_time = time.time()
    logger.info(f"Début du traitement de la requête {request.method} /stations")
    
    try:
        # Pour les requêtes HEAD, on retourne juste un statut 200
        if request.method == 'HEAD':
            logger.info("Requête HEAD détectée, retour immédiat")
            return '', 200
            
        logger.info("Chargement des données...")
        load_start = time.time()
        graph, positions, stations = load_data()
        logger.info(f"Données chargées en {time.time() - load_start:.2f} secondes")
        
        logger.info("Groupement des stations par nom...")
        group_start = time.time()
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
            # Si station_data['line'] est une liste, on ajoute tous ses éléments à l'ensemble
            if isinstance(station_data['line'], list):
                station_groups[name]['lines'].update(station_data['line'])
            else:
                station_groups[name]['lines'].add(station_data['line'])
            station_groups[name]['ids'].append(station_id)
            # Prendre la première position trouvée (ou améliorer pour moyenne)
            if not station_groups[name]['position'] and station_id in positions:
                station_groups[name]['position'] = positions[station_id]
        logger.info(f"Groupement terminé en {time.time() - group_start:.2f} secondes")

        # Formater la liste finale
        logger.info("Formatage de la réponse...")
        format_start = time.time()
        stations_list = []
        for group in station_groups.values():
            stations_list.append({
                'name': group['name'],
                'lines': list(group['lines']),
                'ids': group['ids'],
                'position': group['position']
            })
        logger.info(f"Formatage terminé en {time.time() - format_start:.2f} secondes")

        total_time = time.time() - start_time
        logger.info(f"Traitement terminé en {total_time:.2f} secondes. {len(stations_list)} stations groupées.")
        
        return jsonify({
            'stations': stations_list,
            'count': len(stations_list)
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la requête: {str(e)}", exc_info=True)
        return jsonify({'error': 'Erreur interne du serveur'}), 500 

@stations_bp.route('/stations/list', methods=['GET'])
def get_stations_list():
    """Retourne la liste des stations uniques avec leurs lignes associées et leurs IDs."""
    start_time = time.time()
    logger.info(f"Début du traitement de la requête GET /stations/list")
    
    try:
        logger.info("Chargement des données...")
        load_start = time.time()
        graph, positions, stations = load_data()
        logger.info(f"Données chargées en {time.time() - load_start:.2f} secondes")
        
        # Créer un dictionnaire pour stocker les stations et leurs informations
        stations_dict = {}
        for station_id, station in stations.items():
            name = station['name']
            if name not in stations_dict:
                stations_dict[name] = {
                    'lines': set(),
                    'ids': set()
                }
            # Si station['line'] est une liste, on ajoute tous ses éléments
            if isinstance(station['line'], list):
                stations_dict[name]['lines'].update(station['line'])
            else:
                stations_dict[name]['lines'].add(station['line'])
            stations_dict[name]['ids'].add(station_id)
        
        # Convertir en liste triée avec les lignes et les IDs
        stations_list = [
            {
                'name': name,
                'lines': sorted(list(info['lines'])),
                'ids': sorted(list(info['ids']))
            }
            for name, info in sorted(stations_dict.items())
        ]
        
        total_time = time.time() - start_time
        logger.info(f"Traitement terminé en {total_time:.2f} secondes. {len(stations_list)} stations uniques trouvées.")
        
        return jsonify({
            'stations': stations_list,
            'count': len(stations_list)
        })
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la requête: {str(e)}", exc_info=True)
        return jsonify({'error': 'Erreur interne du serveur'}), 500 