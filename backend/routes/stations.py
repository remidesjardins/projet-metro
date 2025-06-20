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
    Retourne, pour chaque ligne, un tableau de branches (chaque branche = séquence complète depuis le terminus principal jusqu'au bout de la branche, en passant par la bifurcation).
    Pour chaque composante connexe du sous-graphe, génère le chemin le plus long entre deux terminus (ou un chemin simple si pas de terminus), sans cycle.
    """
    graph, positions, stations = load_data()
    from collections import defaultdict, deque
    # Regrouper les stations par ligne
    line_to_station_ids = defaultdict(list)
    # Pour chaque ligne, construire le graphe de la ligne
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
        # Trouver toutes les composantes connexes du sous-graphe
        visited_global = set()
        branches = []
        for node in g:
            if node in visited_global:
                continue
            # BFS pour trouver la composante connexe
            component = set()
            queue = deque([node])
            while queue:
                u = queue.popleft()
                if u in component:
                    continue
                component.add(u)
                for v in g[u]:
                    if v not in component:
                        queue.append(v)
            visited_global.update(component)
            # Pour cette composante, trouver les terminus
            subg = {k: g[k] for k in component}
            terminus = [sid for sid, neighbors in subg.items() if len(neighbors) == 1]
            # Si au moins 2 terminus, chercher le chemin le plus long entre eux
            if len(terminus) >= 2:
                # Pour chaque couple de terminus, chercher le chemin le plus long
                max_path = []
                for i in range(len(terminus)):
                    for j in range(i+1, len(terminus)):
                        start, end = terminus[i], terminus[j]
                        # BFS pour trouver le chemin simple entre start et end
                        queue2 = deque([(start, [start])])
                        visited2 = set()
                        while queue2:
                            current, path = queue2.popleft()
                            if current == end:
                                if len(path) > len(max_path):
                                    max_path = path
                                break
                            visited2.add(current)
                            for neighbor in subg[current]:
                                if neighbor not in visited2 and neighbor not in path:
                                    queue2.append((neighbor, path + [neighbor]))
                if max_path:
                    branch = [{
                        'id': sid,
                        'name': stations[sid]['name'],
                        'position': positions.get(sid)
                    } for sid in max_path]
                    branches.append(branch)
            else:
                # Pas de terminus (cycle ou composante isolée) : DFS pour un chemin couvrant tous les sommets sans repasser
                def dfs_path(u, visited, path):
                    visited.add(u)
                    path.append(u)
                    if len(visited) == len(subg):
                        return list(path)
                    for v in subg[u]:
                        if v not in visited:
                            res = dfs_path(v, visited, path)
                            if res:
                                return res
                    path.pop()
                    visited.remove(u)
                    return None
                found = False
                for start in subg:
                    visited = set()
                    path = []
                    res = dfs_path(start, visited, path)
                    if res:
                        branch = [{
                            'id': sid,
                            'name': stations[sid]['name'],
                            'position': positions.get(sid)
                        } for sid in res]
                        branches.append(branch)
                        found = True
                        break
        result[line] = branches
    return jsonify(result) 