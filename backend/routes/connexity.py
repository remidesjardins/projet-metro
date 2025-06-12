from flask import Blueprint, jsonify
from services.connexite import ConnexiteChecker

connexity_bp = Blueprint('connexity', __name__)

@connexity_bp.route('/connexity', methods=['GET'])
def check_connexity():
    """Vérifie la connexité du graphe et retourne les composantes connexes."""
    checker = ConnexiteChecker()
    is_connected = checker.is_connected()
    
    # Si le graphe n'est pas connexe, trouver les composantes connexes
    components = []
    if not is_connected:
        # Utiliser DFS pour trouver les composantes connexes
        visited = set()
        for station in checker.graph:
            if station not in visited:
                component = []
                checker.dfs(station)
                component = list(checker.visited - visited)
                visited.update(component)
                components.append(component)
    
    return jsonify({
        'is_connected': is_connected,
        'components_count': len(components) if not is_connected else 1,
        'components': components if not is_connected else None
    }) 