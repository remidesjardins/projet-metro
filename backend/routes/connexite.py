"""
MetroCity - Mastercamp 2025
Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
Fichier: connexite.py
Description: Routes Flask pour les tests de connexité du réseau de métro
"""

from flask import Blueprint, jsonify, request
from services.connexite import ConnexiteChecker

connexite_bp = Blueprint('connexite', __name__)

@connexite_bp.route('/connexity', methods=['GET'])
def check_connexity():
    """
    Vérifie la connexité du réseau de métro.
    
    Args:
        station (str, optional): Nom de la station de départ pour le test de connexité
        
    Returns:
        JSON: Résultats du test de connexité avec stations inaccessibles
    """
    try:
        checker = ConnexiteChecker()
        
        if 'station' in request.args:
            station_name = request.args['station']
            # Vérifier la connexité à partir de la station spécifiée
            start_from = station_name
        else:
            # Vérifier la connexité générale du graphe
            start_from = None
        
        if start_from:
            # Tester la connexité à partir de la station spécifiée
            is_connected, unreachable_stations = checker.check_connexity_from_station(start_from)
            
            return jsonify({
                'is_connected': is_connected,
                'start_station': start_from,
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
