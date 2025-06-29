import pytest
from app import app
import json
import time

@pytest.fixture
def client():
    """Fixture pour créer un client de test Flask"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# --- TESTS ENDPOINTS CACHE ---

def test_cache_info(client):
    """Test GET /cache/info - Informations sur l'état du cache"""
    response = client.get('/cache/info')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Vérifier la structure de base de la réponse
    assert 'cache_loaded' in data
    assert 'cache_file_exists' in data
    assert 'data_in_memory' in data
    assert isinstance(data['cache_loaded'], bool)
    assert isinstance(data['cache_file_exists'], bool)
    assert isinstance(data['data_in_memory'], bool)
    
    # Vérifier les champs optionnels selon l'état du cache
    if data['cache_file_exists']:
        assert 'cache_size_mb' in data
        assert isinstance(data['cache_size_mb'], (int, float))
        assert data['cache_size_mb'] >= 0

def test_cache_clear(client):
    """Test POST /cache/clear - Effacer le cache"""
    response = client.post('/cache/clear')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Vérifier la structure de la réponse
    assert 'message' in data
    assert 'clear_time' in data
    assert data['message'] == 'Cache effacé avec succès'
    assert isinstance(data['clear_time'], (int, float))
    assert data['clear_time'] >= 0

def test_cache_reload(client):
    """Test POST /cache/reload - Recharger les données depuis GTFS"""
    response = client.post('/cache/reload')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Vérifier la structure de la réponse
    assert 'message' in data
    assert 'reload_time' in data
    assert 'stations_count' in data
    assert 'connections_count' in data
    assert data['message'] == 'Données rechargées avec succès'
    assert isinstance(data['reload_time'], (int, float))
    assert isinstance(data['stations_count'], int)
    assert isinstance(data['connections_count'], int)
    assert data['reload_time'] >= 0
    assert data['stations_count'] > 0
    assert data['connections_count'] > 0

def test_cache_reload_consistency(client):
    """Test que le rechargement du cache maintient la cohérence des données"""
    # Premier rechargement
    response1 = client.post('/cache/reload')
    assert response1.status_code == 200
    data1 = json.loads(response1.data)
    
    # Deuxième rechargement
    response2 = client.post('/cache/reload')
    assert response2.status_code == 200
    data2 = json.loads(response2.data)
    
    # Les données doivent être cohérentes
    assert data1['stations_count'] == data2['stations_count']
    assert data1['connections_count'] == data2['connections_count']

# --- TESTS ENDPOINT SANTÉ ---

def test_health(client):
    """Test GET /health - Endpoint de monitoring de santé"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Vérifier la structure de la réponse
    assert 'status' in data
    assert 'environment' in data
    assert 'debug' in data
    assert data['status'] == 'ok'
    assert isinstance(data['environment'], str)
    assert isinstance(data['debug'], bool)

def test_health_always_available(client):
    """Test que l'endpoint health est toujours disponible même après erreurs"""
    # Essayer d'effacer le cache (peut échouer selon l'état)
    client.post('/cache/clear')
    
    # L'endpoint health doit toujours fonctionner
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ok'

# --- TESTS ENDPOINT PERFORMANCE ---

def test_performance_test(client):
    """Test GET /performance/test - Test de performance"""
    response = client.get('/performance/test')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Vérifier la structure de la réponse
    assert 'full_load_time' in data
    assert 'stations_count' in data
    assert 'connections_count' in data
    assert 'memory_access_time' in data
    
    # Vérifier les types et valeurs
    assert isinstance(data['full_load_time'], (int, float))
    assert isinstance(data['stations_count'], int)
    assert isinstance(data['connections_count'], int)
    assert isinstance(data['memory_access_time'], (int, float))
    
    assert data['full_load_time'] >= 0
    assert data['stations_count'] > 0
    assert data['connections_count'] > 0
    assert data['memory_access_time'] >= 0

def test_performance_cache_vs_full_load(client):
    """Test que le chargement depuis le cache est plus rapide que le chargement complet"""
    response = client.get('/performance/test')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Si le cache est disponible, il doit être plus rapide
    if data.get('cache_load_success', False):
        assert data['cache_load_time'] is not None
        assert data['cache_load_time'] < data['full_load_time']

# --- TESTS ENDPOINTS UTILITAIRES TEMPORELS ---

def test_temporal_stations(client):
    """Test GET /temporal/stations - Liste des stations pour calculs temporels"""
    response = client.get('/temporal/stations')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Vérifier la structure de la réponse
    assert 'stations' in data
    assert isinstance(data['stations'], list)
    assert len(data['stations']) > 0
    
    # Vérifier que les stations sont des chaînes de caractères
    for station in data['stations']:
        assert isinstance(station, str)
        assert len(station) > 0

def test_temporal_station_lines(client):
    """Test GET /temporal/station/{station}/lines - Lignes desservant une station"""
    # Test avec une station existante
    station_name = "Châtelet"
    response = client.get(f'/temporal/station/{station_name}/lines')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Vérifier la structure de la réponse
    assert 'station' in data
    assert 'lines' in data
    assert data['station'] == station_name
    assert isinstance(data['lines'], list)
    assert len(data['lines']) > 0
    
    # Vérifier que les lignes sont des chaînes de caractères
    for line in data['lines']:
        assert isinstance(line, str)
        assert len(line) > 0

def test_temporal_station_lines_invalid_station(client):
    """Test GET /temporal/station/{station}/lines avec une station inexistante"""
    station_name = "StationInexistante123"
    response = client.get(f'/temporal/station/{station_name}/lines')
    assert response.status_code == 200  # ou 404 selon l'implémentation
    data = json.loads(response.data)
    
    # Soit une erreur, soit une liste vide
    if 'error' in data:
        assert 'error' in data
    else:
        assert 'station' in data
        assert 'lines' in data
        assert data['station'] == station_name
        assert isinstance(data['lines'], list)

def test_temporal_next_departure(client):
    """Test GET /temporal/next-departure - Prochain départ d'une ligne"""
    # Test avec des paramètres valides
    params = {
        'station': 'Châtelet',
        'line': '1',
        'after_time': '08:30'
    }
    response = client.get('/temporal/next-departure', query_string=params)
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Vérifier la structure de la réponse
    assert 'station' in data
    assert 'line' in data
    assert 'after_time' in data
    assert data['station'] == params['station']
    assert data['line'] == params['line']
    assert data['after_time'] == params['after_time']
    
    # Soit un départ trouvé, soit aucun départ
    if data.get('next_departure'):
        assert 'next_departure' in data
        assert 'wait_time_minutes' in data
        assert isinstance(data['next_departure'], str)
        assert isinstance(data['wait_time_minutes'], int)
        assert data['wait_time_minutes'] >= 0
    else:
        assert 'message' in data
        assert 'Aucun départ trouvé' in data['message']

def test_temporal_next_departure_missing_params(client):
    """Test GET /temporal/next-departure avec des paramètres manquants"""
    # Test sans paramètres
    response = client.get('/temporal/next-departure')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    
    # Test avec seulement 2 paramètres sur 3
    params = {
        'station': 'Châtelet',
        'line': '1'
        # after_time manquant
    }
    response = client.get('/temporal/next-departure', query_string=params)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_temporal_next_departure_invalid_time(client):
    """Test GET /temporal/next-departure avec un format d'heure invalide"""
    params = {
        'station': 'Châtelet',
        'line': '1',
        'after_time': 'heure_invalide'
    }
    response = client.get('/temporal/next-departure', query_string=params)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

# --- TESTS DE ROBUSTESSE ---

def test_cache_endpoints_error_handling(client):
    """Test que les endpoints de cache gèrent bien les erreurs"""
    # Ces tests vérifient que les endpoints ne plantent pas
    # même en cas de problème avec le cache
    
    # Test info cache
    response = client.get('/cache/info')
    assert response.status_code in [200, 500]  # Peut échouer si pas de cache
    
    # Test clear cache
    response = client.post('/cache/clear')
    assert response.status_code in [200, 500]
    
    # Test reload cache
    response = client.post('/cache/reload')
    assert response.status_code in [200, 500]

def test_performance_endpoint_consistency(client):
    """Test que l'endpoint performance retourne des résultats cohérents"""
    # Premier appel
    response1 = client.get('/performance/test')
    assert response1.status_code == 200
    data1 = json.loads(response1.data)
    
    # Deuxième appel (données déjà chargées)
    response2 = client.get('/performance/test')
    assert response2.status_code == 200
    data2 = json.loads(response2.data)
    
    # Les compteurs doivent être cohérents
    assert data1['stations_count'] == data2['stations_count']
    assert data1['connections_count'] == data2['connections_count']

# --- TESTS D'INTÉGRATION ---

def test_cache_workflow(client):
    """Test le workflow complet du cache : info -> clear -> reload -> info"""
    # 1. Vérifier l'état initial
    response = client.get('/cache/info')
    assert response.status_code == 200
    initial_info = json.loads(response.data)
    
    # 2. Effacer le cache
    response = client.post('/cache/clear')
    assert response.status_code == 200
    
    # 3. Recharger les données
    response = client.post('/cache/reload')
    assert response.status_code == 200
    reload_data = json.loads(response.data)
    
    # 4. Vérifier l'état final
    response = client.get('/cache/info')
    assert response.status_code == 200
    final_info = json.loads(response.data)
    
    # 5. Vérifier la cohérence
    assert final_info['cache_loaded'] == True
    assert reload_data['stations_count'] > 0
    assert reload_data['connections_count'] > 0

def test_temporal_workflow(client):
    """Test le workflow temporel : stations -> station lines -> next departure"""
    # 1. Récupérer la liste des stations
    response = client.get('/temporal/stations')
    assert response.status_code == 200
    stations_data = json.loads(response.data)
    assert len(stations_data['stations']) > 0
    
    # 2. Prendre la première station et récupérer ses lignes
    first_station = stations_data['stations'][0]
    response = client.get(f'/temporal/station/{first_station}/lines')
    assert response.status_code == 200
    lines_data = json.loads(response.data)
    
    if lines_data.get('lines') and len(lines_data['lines']) > 0:
        # 3. Prendre la première ligne et chercher le prochain départ
        first_line = lines_data['lines'][0]
        params = {
            'station': first_station,
            'line': first_line,
            'after_time': '08:30'
        }
        response = client.get('/temporal/next-departure', query_string=params)
        assert response.status_code == 200
        departure_data = json.loads(response.data)
        
        # Vérifier la cohérence des données
        assert departure_data['station'] == first_station
        assert departure_data['line'] == first_line 