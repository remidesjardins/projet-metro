from flask import Blueprint, jsonify, request
from utils.parser import load_data
import logging
import time
from collections import defaultdict, deque

logger = logging.getLogger(__name__)
stations_bp = Blueprint('stations', __name__)

@stations_bp.route('/stations', methods=['GET', 'HEAD'])
def get_stations():
    """Retourne la liste des stations avec leurs coordonnées, groupées par nom."""
    start_time = time.time()
    
    try:
        # Pour les requêtes HEAD, on retourne juste un statut 200
        if request.method == 'HEAD':
            return '', 200
        
        # Récupérer le paramètre include_rer
        include_rer = request.args.get('include_rer', 'true').lower() == 'true'
        
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
                # Si station_data['line'] est une liste, on ajoute tous ses éléments à l'ensemble
                if isinstance(station_data['line'], list):
                    station_groups[name]['lines'].update(station_data['line'])
                else:
                    station_groups[name]['lines'].add(station_data['line'])
            else:
                if isinstance(station_data['line'], list):
                    station_groups[name]['lines'].update(station_data['line'])
                else:
                    station_groups[name]['lines'].add(station_data['line'])
            station_groups[name]['ids'].append(station_id)
            # Prendre la première position trouvée (ou améliorer pour moyenne)
            if not station_groups[name]['position'] and station_id in positions:
                station_groups[name]['position'] = positions[station_id]

        # Formater la liste finale
        stations_list = []
        for group in station_groups.values():
            # Si include_rer est False, filtrer les stations qui ont des lignes RER
            if not include_rer:
                rer_lines = {'A', 'B', 'C', 'D', 'E'}
                station_lines = set(group['lines'])
                # Si la station a des lignes RER, l'exclure
                if station_lines & rer_lines:
                    continue
            
            stations_list.append({
                'name': group['name'],
                'lines': list(group['lines']),
                'ids': group['ids'],
                'position': group['position']
            })

        total_time = time.time() - start_time
        logger.info(f"GET /stations - {len(stations_list)} stations groupées en {total_time:.2f}s")
        
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
    
    try:
        graph, positions, stations = load_data()
        
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
        logger.info(f"GET /stations/list - {len(stations_list)} stations uniques en {total_time:.2f}s")

        return jsonify({
            'stations': stations_list,
            'count': len(stations_list)
        }) 
        
    except Exception as e:
        logger.error(f"Erreur lors du traitement de la requête: {str(e)}", exc_info=True)
        return jsonify({'error': 'Erreur interne du serveur'}), 500 

@stations_bp.route('/stations/ordered_by_line', methods=['GET'])
def get_stations_ordered_by_line():
    """
    Retourne, pour chaque ligne, TOUTES les branches (y compris les bifurcations).
    """
    graph, positions, stations = load_data()
    from collections import defaultdict, deque
    
    # Regrouper les stations par ligne
    line_to_station_ids = defaultdict(list)
    line_graphs = defaultdict(lambda: defaultdict(list))
    
    for station_id, station in stations.items():
        lines = station['line'] if isinstance(station['line'], list) else [station['line']]
        for line in lines:
            line_to_station_ids[line].append(station_id)
    
    # Construire le graphe de chaque ligne
    for line, ids in line_to_station_ids.items():
        for station_id in ids:
            for neighbor_id in graph[station_id]:
                neighbor_lines = stations[neighbor_id]['line'] if isinstance(stations[neighbor_id]['line'], list) else [stations[neighbor_id]['line']]
                if line in neighbor_lines:
                    line_graphs[line][station_id].append(neighbor_id)
    
    result = {}
    for line, g in line_graphs.items():
        
        # 1. Identifier tous les terminus (degré 1)
        terminus = []
        for station_id, neighbors in g.items():
            if len(neighbors) == 1:
                terminus.append(station_id)
        
        print(f"Ligne {line}: {len(terminus)} terminus trouvés: {[stations[t]['name'] for t in terminus]}")
        
        branches = []
        
        if len(terminus) >= 2:
            def find_path_between(start, end):
                """BFS pour trouver le chemin entre deux terminus"""
                if start == end:
                    return None
                
                queue = deque([(start, [start])])
                visited = {start}
                
                while queue:
                    current, path = queue.popleft()
                    
                    if current == end:
                        return path
                    
                    for neighbor in g[current]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append((neighbor, path + [neighbor]))
                
                return None
            
            processed_pairs = set()
            
            for i, start_terminus in enumerate(terminus):
                for j, end_terminus in enumerate(terminus):
                    if i >= j:  # Éviter les doublons (A->B et B->A)
                        continue
                    
                    pair = tuple(sorted([start_terminus, end_terminus]))
                    if pair in processed_pairs:
                        continue
                    processed_pairs.add(pair)
                    
                    path = find_path_between(start_terminus, end_terminus)
                    if path and len(path) >= 2:
                        branch = [{
                            'id': sid,
                            'name': stations[sid]['name'],
                            'position': positions.get(sid)
                        } for sid in path]
                        branches.append(branch)
                        
                        print(f"  → Branche trouvée: {stations[start_terminus]['name']} → {stations[end_terminus]['name']} ({len(path)} stations)")
        
        elif len(g) > 0:
            print(f"  → Ligne {line}: Pas de terminus trouvés, utilisation du fallback")
            
            # Trouver le nœud avec le plus petit ID comme point de départ
            start_node = min(g.keys())
            
            # DFS pour parcourir toute la ligne
            def dfs_all_stations(start):
                visited = set()
                path = []
                
                def dfs(node):
                    visited.add(node)
                    path.append(node)
                    
                    for neighbor in g[node]:
                        if neighbor not in visited:
                            dfs(neighbor)
                
                dfs(start)
                return path
            
            path = dfs_all_stations(start_node)
            if len(path) >= 2:
                branch = [{
                    'id': sid,
                    'name': stations[sid]['name'],
                    'position': positions.get(sid)
                } for sid in path]
                branches.append(branch)
        
        print(f"  → {len(branches)} branche(s) générée(s) pour la ligne {line}")
        
        result[line] = branches
    
    return jsonify(result)