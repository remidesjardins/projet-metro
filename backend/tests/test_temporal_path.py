import pytest
from datetime import datetime, timedelta
from app import app
import json

# Remplacement du trajet de test par défaut
TRAJET_DEPART = 'Villejuif - Louis Aragon'
TRAJET_ARRIVEE = 'Gare du Nord'

# --- TESTS D'INTEGRATION API ---
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_temporal_path_basic(client):
    """Test API /temporal/path pour un trajet long (Villejuif - Louis Aragon -> Gare du Nord)"""
    data = {
        'start_station': TRAJET_DEPART,
        'end_station': TRAJET_ARRIVEE,
        'departure_time': '08:30',
        'date': '2024-06-25'
    }
    response = client.post('/temporal/path', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert 'segments' in result
    assert 'total_duration' in result
    assert len(result['segments']) > 0
    # Vérifier la structure d'un segment
    seg = result['segments'][0]
    assert 'from_station' in seg
    assert 'to_station' in seg
    assert 'line' in seg
    assert 'departure_time' in seg
    assert 'arrival_time' in seg
    assert 'wait_time' in seg
    assert 'travel_time' in seg

def test_temporal_path_no_service(client):
    """Test API /temporal/path pour un horaire hors service (retourne 200 avec métro du lendemain)"""
    data = {
        'start_station': TRAJET_DEPART,
        'end_station': TRAJET_ARRIVEE,
        'departure_time': '02:00',
        'date': '2024-06-25'
    }
    response = client.post('/temporal/path', data=json.dumps(data), content_type='application/json')
    assert response.status_code in [200, 404]
    result = json.loads(response.data)
    if response.status_code == 200:
        assert 'segments' in result
        assert 'total_duration' in result
        assert len(result['segments']) > 0
    else:
        assert 'error' in result
        assert 'service_info' in result
        assert not result['service_info']['is_service_available']

def test_temporal_path_invalid_station(client):
    """Test API /temporal/path avec une station inconnue (retourne 404)"""
    data = {
        'start_station': 'StationInconnue',
        'end_station': TRAJET_ARRIVEE,
        'departure_time': '08:30',
        'date': '2024-06-25'
    }
    response = client.post('/temporal/path', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 404
    result = json.loads(response.data)
    assert 'error' in result

# --- TEST DE COHERENCE BACKEND/API ---
def test_temporal_path_consistency(client):
    """Vérifie la cohérence entre le service backend et la réponse API pour un trajet long."""
    from services.temporal_path import TemporalPathService
    from services.graph_service import GraphService
    from services.gtfs_temporal import GTFSemporalService
    from utils.data_manager import DataManager
    
    graph, positions, stations = DataManager.get_data()
    graph_service = GraphService(graph, stations)
    gtfs_service = GTFSemporalService("data/gtfs")
    temporal_service = TemporalPathService(graph_service, gtfs_service)
    
    start = TRAJET_DEPART
    end = TRAJET_ARRIVEE
    dt = datetime(2024, 6, 25, 8, 30)
    backend_path = temporal_service.find_optimal_temporal_path(start, end, dt)
    
    data = {
        'start_station': start,
        'end_station': end,
        'departure_time': '08:30',
        'date': '2024-06-25'
    }
    response = client.post('/temporal/path', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 200
    api_result = json.loads(response.data)
    assert abs(api_result['total_duration'] - backend_path.total_duration) < 120
    api_segments = api_result['segments']
    backend_segments = backend_path.segments
    assert api_segments[0]['from_station'] == backend_segments[0].from_station
    assert api_segments[-1]['to_station'] == backend_segments[-1].to_station
    assert len(api_segments) <= len(backend_segments)

# --- TESTS DE NON-REGRESSION STRUCTURELLE ---
def test_temporal_path_segments_grouping(client):
    """Vérifie que les segments sont bien regroupés par ligne (pas un segment par station)."""
    data = {
        'start_station': TRAJET_DEPART,
        'end_station': TRAJET_ARRIVEE,
        'departure_time': '08:30',
        'date': '2024-06-25'
    }
    response = client.post('/temporal/path', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 200
    result = json.loads(response.data)
    segments = result['segments']
    assert len(segments) < 10  # tolérance plus large pour un long trajet
    last_line = None
    for seg in segments:
        if last_line is not None:
            assert seg['line'] == last_line or seg['transfer_time'] > 0
        last_line = seg['line']

# --- TESTS /temporal/alternatives ---
def test_temporal_alternatives_basic(client):
    """Test API /temporal/alternatives pour un trajet long (Villejuif - Louis Aragon -> Gare du Nord)"""
    data = {
        'start_station': TRAJET_DEPART,
        'end_station': TRAJET_ARRIVEE,
        'departure_time': '08:30',
        'date': '2024-06-25',
        'max_paths': 3
    }
    response = client.post('/temporal/alternatives', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert 'paths' in result
    assert len(result['paths']) > 0
    alt = result['paths'][0]
    assert 'segments' in alt
    assert 'total_duration' in alt
    assert len(alt['segments']) > 0

def test_temporal_alternatives_no_alternative(client):
    """Test API /temporal/alternatives pour un trajet impossible (retourne 404)"""
    data = {
        'start_station': 'StationInconnue',
        'end_station': TRAJET_ARRIVEE,
        'departure_time': '08:30',
        'date': '2024-06-25',
        'max_paths': 3
    }
    response = client.post('/temporal/alternatives', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 404
    result = json.loads(response.data)
    assert 'error' in result

def test_temporal_alternatives_structure(client):
    """Vérifie la structure des chemins alternatifs (groupement par ligne, cohérence des horaires)"""
    data = {
        'start_station': TRAJET_DEPART,
        'end_station': TRAJET_ARRIVEE,
        'departure_time': '08:30',
        'date': '2024-06-25',
        'max_paths': 3
    }
    response = client.post('/temporal/alternatives', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 200
    result = json.loads(response.data)
    for path in result['paths']:
        segments = path['segments']
        assert len(segments) < 12  # tolérance plus large pour un long trajet
        last_line = None
        for seg in segments:
            if last_line is not None:
                assert seg['line'] == last_line or seg['transfer_time'] > 0
            last_line = seg['line'] 