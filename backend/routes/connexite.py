from flask import Blueprint, jsonify, request
from services.connexite import ConnexiteChecker

connexite_bp = Blueprint('connexite', __name__)

@connexite_bp.route('/connexity', methods=['GET'])
def check_connexity():
    """
    Route pour vérifier la connexité du graphe du métro.
    Accepte un paramètre optionnel 'station' pour tester la connexité
    à partir d'une station spécifique.
    """
    try:
        checker = ConnexiteChecker()
        
        # Vérifier si une station de départ est spécifiée
        station_name = request.args.get('station')
        
        if station_name:
            # Tester la connexité à partir de la station spécifiée
            is_connected, unreachable_stations = checker.check_connexity_from_station(station_name)
            
            return jsonify({
                'is_connected': is_connected,
                'start_station': station_name,
                'unreachable_stations': unreachable_stations,
                'total_stations': len(checker.graph),
                'reachable_stations': len(checker.visited),
                'unreachable_count': len(unreachable_stations)
            })
        else:
            # Tester la connexité générale du graphe
            is_connected = checker.is_connected()
            unreachable = checker.get_unreachable_stations()
            
            return jsonify({
                'is_connected': is_connected,
                'unreachable_stations': unreachable,
                'total_stations': len(checker.graph),
                'reachable_stations': len(checker.visited),
                'unreachable_count': len(unreachable)
            })
            
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500
