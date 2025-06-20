from flask import Blueprint, jsonify
from utils.data_manager import DataManager
import time
import logging

logger = logging.getLogger(__name__)
cache_bp = Blueprint('cache', __name__)

@cache_bp.route('/cache/info', methods=['GET'])
def get_cache_info():
    """Retourne les informations sur l'état du cache."""
    try:
        cache_info = DataManager.get_cache_info()
        return jsonify(cache_info)
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des informations du cache: {str(e)}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

@cache_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Efface le cache et force un rechargement des données."""
    try:
        start_time = time.time()
        DataManager.clear_cache()
        clear_time = time.time() - start_time
        
        logger.info(f"Cache effacé en {clear_time:.3f}s")
        return jsonify({
            'message': 'Cache effacé avec succès',
            'clear_time': clear_time
        })
    except Exception as e:
        logger.error(f"Erreur lors de l'effacement du cache: {str(e)}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

@cache_bp.route('/cache/reload', methods=['POST'])
def reload_cache():
    """Force un rechargement des données depuis les fichiers GTFS."""
    try:
        start_time = time.time()
        
        # Effacer le cache existant
        DataManager.clear_cache()
        
        # Recharger les données
        graph, positions, stations = DataManager.get_data()
        
        reload_time = time.time() - start_time
        
        logger.info(f"Données rechargées en {reload_time:.3f}s")
        
        return jsonify({
            'message': 'Données rechargées avec succès',
            'reload_time': reload_time,
            'stations_count': len(stations),
            'connections_count': sum(len(v) for v in graph.values()) // 2
        })
    except Exception as e:
        logger.error(f"Erreur lors du rechargement des données: {str(e)}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500

@cache_bp.route('/performance/test', methods=['GET'])
def test_performance():
    """Teste les performances de chargement des données."""
    try:
        results = {}
        
        # Test 1: Chargement depuis le cache (si disponible)
        if DataManager.get_cache_info()['cache_loaded']:
            start_time = time.time()
            graph, positions, stations = DataManager.get_data()
            cache_load_time = time.time() - start_time
            results['cache_load_time'] = cache_load_time
            results['cache_load_success'] = True
        else:
            results['cache_load_time'] = None
            results['cache_load_success'] = False
        
        # Test 2: Chargement complet (force le rechargement)
        DataManager.clear_cache()
        start_time = time.time()
        graph, positions, stations = DataManager.get_data()
        full_load_time = time.time() - start_time
        
        results['full_load_time'] = full_load_time
        results['stations_count'] = len(stations)
        results['connections_count'] = sum(len(v) for v in graph.values()) // 2
        
        # Test 3: Accès mémoire (données déjà chargées)
        start_time = time.time()
        for _ in range(10):  # 10 accès pour avoir une moyenne
            graph, positions, stations = DataManager.get_data()
        memory_access_time = (time.time() - start_time) / 10
        
        results['memory_access_time'] = memory_access_time
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Erreur lors du test de performance: {str(e)}")
        return jsonify({'error': 'Erreur interne du serveur'}), 500 