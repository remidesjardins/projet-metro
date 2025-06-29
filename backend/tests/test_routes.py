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
    """Test la route GET /."""
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
    assert isinstance(data['stations'], list)
    assert len(data['stations']) > 0
    # Vérifier la structure d'une station
    first_station = data['stations'][0]
    assert 'name' in first_station
    assert 'lines' in first_station or 'line' in first_station
    assert 'position' in first_station

def test_get_graph(client):
    """Test la route GET /graph."""
    response = client.get('/graph')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'graph' in data
    assert len(data['graph']) > 0

def test_get_connexity(client):
    """Test la route GET /connexity."""
    response = client.get('/connexity')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'is_connected' in data
    assert 'reachable_stations' in data
    assert 'total_stations' in data
    # Si le graphe n'est pas connexe, vérifier les stations inaccessibles
    if not data['is_connected']:
        assert 'unreachable_stations' in data
        assert 'unreachable_count' in data

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
    assert isinstance(mst, list)
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
    assert 'chemin' in data
    assert 'duration' in data
    assert 'emissions' in data
    assert 'stations_count' in data

    # Vérifier la structure du chemin (nouvelle structure)
    chemin = data['chemin']
    assert len(chemin) > 0
    for segment in chemin:
        assert 'Ligne' in segment
        assert 'Stations' in segment
        assert 'Duration' in segment

        stations = segment['Stations']
        assert len(stations) > 0
        for station in stations:
            assert 'ID' in station
            assert 'Nom Station' in station
            assert 'Lignes' in station
            assert 'Position' in station

    # Test avec des stations invalides (maintenant retourne 404)
    invalid_data = {
        'start': 'invalid',
        'end': 'invalid'
    }
    response = client.post('/shortest-path',
                          data=json.dumps(invalid_data),
                          content_type='application/json')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error']['code'] == 'NOT_FOUND'

    # Test avec des données manquantes
    missing_data = {}
    response = client.post('/shortest-path',
                          data=json.dumps(missing_data),
                          content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert data['error']['code'] == 'VALIDATION_ERROR' 