import pytest
from app import app
import json

@pytest.fixture
def client():
    """Fixture pour créer un client de test Flask."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index(client):
    """Test la route d'accueil."""
    response = client.get('/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'name' in data
    assert 'version' in data
    assert 'endpoints' in data

def test_get_stations(client):
    """Test la route GET /stations."""
    response = client.get('/stations')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'stations' in data
    assert 'count' in data
    assert len(data['stations']) > 0
    
    # Vérifier la structure d'une station
    station = data['stations'][0]
    assert 'id' in station
    assert 'name' in station
    assert 'line' in station
    assert 'position' in station

def test_get_graph(client):
    """Test la route GET /graph."""
    response = client.get('/graph')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'graph' in data
    assert 'stations_count' in data
    assert 'connections_count' in data
    
    # Vérifier la structure du graphe
    graph = data['graph']
    assert len(graph) > 0
    for station_id, station_data in graph.items():
        assert 'name' in station_data
        assert 'neighbors' in station_data

def test_get_connexity(client):
    """Test la route GET /connexity."""
    response = client.get('/connexity')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'is_connected' in data
    assert 'components_count' in data
    
    # Si le graphe n'est pas connexe, vérifier les composantes
    if not data['is_connected']:
        assert 'components' in data
        assert len(data['components']) > 0

def test_get_acpm(client):
    """Test la route GET /acpm."""
    response = client.get('/acpm')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'mst' in data
    assert 'total_weight' in data
    assert 'edges_count' in data
    
    # Vérifier la structure de l'ACPM
    mst = data['mst']
    assert len(mst) > 0
    for edge in mst:
        assert 'from' in edge
        assert 'to' in edge
        assert 'weight' in edge
        assert 'id' in edge['from']
        assert 'name' in edge['from']
        assert 'id' in edge['to']
        assert 'name' in edge['to']

def test_shortest_path(client):
    """Test la route POST /shortest-path."""
    # Test avec des stations valides
    valid_data = {
        'start': '0000',  # Abbesses
        'end': '0016'     # Bastille
    }
    response = client.post('/shortest-path',
                          data=json.dumps(valid_data),
                          content_type='application/json')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'path' in data
    assert 'duration' in data
    assert 'stations_count' in data
    
    # Vérifier la structure du chemin
    path = data['path']
    assert len(path) > 0
    for station in path:
        assert 'id' in station
        assert 'name' in station
        assert 'line' in station
        assert 'position' in station
    
    # Test avec des stations invalides
    invalid_data = {
        'start': 'invalid',
        'end': 'invalid'
    }
    response = client.post('/shortest-path',
                          data=json.dumps(invalid_data),
                          content_type='application/json')
    assert response.status_code == 400
    
    # Test avec des données manquantes
    missing_data = {
        'start': '0000'
    }
    response = client.post('/shortest-path',
                          data=json.dumps(missing_data),
                          content_type='application/json')
    assert response.status_code == 400 