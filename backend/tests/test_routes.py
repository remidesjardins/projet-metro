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
    """Test complet de la route GET /connexity."""
    # Test 1: Vérification de la connexité générale
    response = client.get('/connexity')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Vérifier la structure de base de la réponse
    assert 'is_connected' in data
    assert 'total_stations' in data
    assert 'reachable_stations' in data
    assert isinstance(data['is_connected'], bool)
    assert isinstance(data['total_stations'], int)
    assert isinstance(data['reachable_stations'], int)
    
    # Vérifier la cohérence des données
    assert data['total_stations'] > 0
    assert data['reachable_stations'] > 0
    assert data['reachable_stations'] <= data['total_stations']
    
    # Si le graphe n'est pas connexe, vérifier les stations inaccessibles
    if not data['is_connected']:
        assert 'unreachable_stations' in data
        assert 'unreachable_count' in data
        assert isinstance(data['unreachable_stations'], list)
        assert isinstance(data['unreachable_count'], int)
        assert data['unreachable_count'] == len(data['unreachable_stations'])
        assert data['reachable_stations'] + data['unreachable_count'] == data['total_stations']
        
        # Vérifier la structure des stations inaccessibles
        for station in data['unreachable_stations']:
            assert 'id' in station
            assert 'name' in station
            assert 'line' in station
            assert isinstance(station['id'], str)
            assert isinstance(station['name'], str)
            assert isinstance(station['line'], (str, list))
    else:
        # Si connexe, vérifier que toutes les stations sont accessibles
        assert data['reachable_stations'] == data['total_stations']
        assert 'unreachable_stations' not in data or len(data['unreachable_stations']) == 0
        assert 'unreachable_count' not in data or data['unreachable_count'] == 0
    
    # Test 2: Vérification de la connexité à partir de plusieurs stations spécifiques
    stations_response = client.get('/stations')
    assert stations_response.status_code == 200
    stations_data = json.loads(stations_response.data)
    
    # Tester avec plusieurs stations différentes
    test_stations = [
        stations_data['stations'][0]['name'],  # Première station
        stations_data['stations'][len(stations_data['stations'])//2]['name'],  # Station du milieu
        stations_data['stations'][-1]['name']  # Dernière station
    ]
    
    for test_station in test_stations:
        print(f"Testing connexity from station: {test_station}")
        response_from_station = client.get(f'/connexity?station={test_station}')
        assert response_from_station.status_code == 200, f"Erreur pour la station {test_station}"
        data_from_station = json.loads(response_from_station.data)
        
        # Vérifier la structure spécifique à une station de départ
        assert 'is_connected' in data_from_station, f"Champ 'is_connected' manquant pour {test_station}"
        assert 'start_station' in data_from_station, f"Champ 'start_station' manquant pour {test_station}"
        assert 'total_stations' in data_from_station, f"Champ 'total_stations' manquant pour {test_station}"
        assert 'reachable_stations' in data_from_station, f"Champ 'reachable_stations' manquant pour {test_station}"
        assert data_from_station['start_station'] == test_station, f"Station de départ incorrecte pour {test_station}"
        
        # Vérifier la cohérence avec le test général
        assert data_from_station['total_stations'] == data['total_stations'], f"Nombre total de stations incohérent pour {test_station}"
        assert data_from_station['is_connected'] == data['is_connected'], f"Connexité incohérente pour {test_station}"
        assert data_from_station['reachable_stations'] == data['reachable_stations'], f"Nombre de stations accessibles incohérent pour {test_station}"
        
        # Vérifier que le nombre de stations accessibles est cohérent
        if data_from_station['is_connected']:
            assert data_from_station['reachable_stations'] == data_from_station['total_stations'], f"Toutes les stations doivent être accessibles depuis {test_station}"
            assert 'unreachable_stations' not in data_from_station or len(data_from_station['unreachable_stations']) == 0, f"Pas de stations inaccessibles depuis {test_station}"
        else:
            assert data_from_station['reachable_stations'] < data_from_station['total_stations'], f"Certaines stations doivent être inaccessibles depuis {test_station}"
            assert 'unreachable_stations' in data_from_station, f"Stations inaccessibles manquantes pour {test_station}"
            assert len(data_from_station['unreachable_stations']) > 0, f"Liste des stations inaccessibles vide pour {test_station}"
    
    # Test 2b: Vérification de la connexité avec des stations de correspondance importantes
    # Chercher des stations qui ont plusieurs lignes (correspondances)
    correspondence_stations = []
    for station in stations_data['stations']:
        if len(station['lines']) > 1:
            correspondence_stations.append(station['name'])
            if len(correspondance_stations) >= 3:  # Tester avec 3 stations de correspondance
                break
    
    for test_station in correspondence_stations:
        print(f"Testing connexity from correspondence station: {test_station}")
        response_from_station = client.get(f'/connexity?station={test_station}')
        assert response_from_station.status_code == 200, f"Erreur pour la station de correspondance {test_station}"
        data_from_station = json.loads(response_from_station.data)
        
        # Vérifier que les résultats sont cohérents
        assert data_from_station['is_connected'] == data['is_connected'], f"Connexité incohérente pour la station de correspondance {test_station}"
        assert data_from_station['total_stations'] == data['total_stations'], f"Nombre total de stations incohérent pour la station de correspondance {test_station}"
    
    # Test 3: Vérification avec une station inexistante
    response_invalid = client.get('/connexity?station=StationInexistante')
    assert response_invalid.status_code == 500
    error_data = json.loads(response_invalid.data)
    assert 'error' in error_data
    
    # Test 4: Vérification de la performance (temps de réponse raisonnable)
    import time
    start_time = time.time()
    response_perf = client.get('/connexity')
    end_time = time.time()
    assert response_perf.status_code == 200
    assert (end_time - start_time) < 5.0  # Doit répondre en moins de 5 secondes
    
    # Test 5: Vérification de la cohérence des données avec le graphe
    graph_response = client.get('/graph')
    assert graph_response.status_code == 200
    graph_data = json.loads(graph_response.data)
    graph_stations_count = len(graph_data['graph'])
    
    # Le nombre de stations dans la connexité doit correspondre au graphe
    assert data['total_stations'] == graph_stations_count

def test_get_acpm(client):
    """Test complet de la route GET /acpm."""
    # Test 1: Vérification de base de l'ACPM
    response = client.get('/acpm')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Vérifier la structure de base
    assert 'mst' in data
    assert 'total_weight' in data
    assert 'edges_count' in data
    assert isinstance(data['mst'], list)
    assert isinstance(data['total_weight'], (int, float))
    assert isinstance(data['edges_count'], int)
    
    # Vérifier la cohérence des données
    mst = data['mst']
    assert len(mst) == data['edges_count'], "Le nombre d'arêtes doit correspondre"
    assert data['total_weight'] >= 0, "Le poids total ne peut pas être négatif"
    
    # Test 2: Vérification détaillée de chaque arête
    for i, edge in enumerate(mst):
        assert 'from' in edge, f"Arête {i}: champ 'from' manquant"
        assert 'to' in edge, f"Arête {i}: champ 'to' manquant"
        assert 'weight' in edge, f"Arête {i}: champ 'weight' manquant"
        
        # Vérifier la structure de 'from'
        assert 'id' in edge['from'], f"Arête {i}: 'from' doit avoir un 'id'"
        assert 'name' in edge['from'], f"Arête {i}: 'from' doit avoir un 'name'"
        assert isinstance(edge['from']['id'], str), f"Arête {i}: 'from.id' doit être une string"
        assert isinstance(edge['from']['name'], str), f"Arête {i}: 'from.name' doit être une string"
        
        # Vérifier la structure de 'to'
        assert 'id' in edge['to'], f"Arête {i}: 'to' doit avoir un 'id'"
        assert 'name' in edge['to'], f"Arête {i}: 'to' doit avoir un 'name'"
        assert isinstance(edge['to']['id'], str), f"Arête {i}: 'to.id' doit être une string"
        assert isinstance(edge['to']['name'], str), f"Arête {i}: 'to.name' doit être une string"
        
        # Vérifier le poids
        assert isinstance(edge['weight'], (int, float)), f"Arête {i}: 'weight' doit être un nombre"
        assert edge['weight'] >= 0, f"Arête {i}: 'weight' ne peut pas être négatif"
        
        # Vérifier que les IDs sont différents
        assert edge['from']['id'] != edge['to']['id'], f"Arête {i}: les IDs 'from' et 'to' doivent être différents"
    
    # Test 3: Vérification de la propriété d'arbre couvrant
    # Récupérer le nombre de stations depuis l'API stations
    stations_response = client.get('/stations')
    assert stations_response.status_code == 200
    stations_data = json.loads(stations_response.data)
    total_stations = stations_data['count']
    
    # Un arbre couvrant doit avoir exactement (n-1) arêtes pour n stations
    expected_edges = total_stations - 1
    assert len(mst) == expected_edges, f"L'ACPM doit avoir {expected_edges} arêtes pour {total_stations} stations, pas {len(mst)}"
    
    # Test 4: Vérification de la connexité de l'ACPM
    # Construire le graphe de l'ACPM
    acpm_graph = {}
    for edge in mst:
        from_id = edge['from']['id']
        to_id = edge['to']['id']
        
        if from_id not in acpm_graph:
            acpm_graph[from_id] = set()
        if to_id not in acpm_graph:
            acpm_graph[to_id] = set()
        
        acpm_graph[from_id].add(to_id)
        acpm_graph[to_id].add(from_id)
    
    # Vérifier que l'ACPM est connexe (DFS)
    visited = set()
    if acpm_graph:
        start_station = next(iter(acpm_graph))
        
        def dfs(node):
            visited.add(node)
            for neighbor in acpm_graph.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor)
        
        dfs(start_station)
        
        # Toutes les stations doivent être accessibles
        assert len(visited) == total_stations, f"ACPM non connexe: {len(visited)}/{total_stations} stations accessibles"
    
    # Test 5: Vérification de la minimalité (pas de cycles)
    # Vérifier qu'il n'y a pas de doublons dans les arêtes
    edge_set = set()
    for edge in mst:
        from_id = edge['from']['id']
        to_id = edge['to']['id']
        # Normaliser l'ordre des IDs pour éviter les doublons
        edge_tuple = tuple(sorted([from_id, to_id]))
        assert edge_tuple not in edge_set, f"Arête dupliquée détectée: {from_id}-{to_id}"
        edge_set.add(edge_tuple)
    
    # Test 6: Vérification de la performance
    import time
    start_time = time.time()
    response_perf = client.get('/acpm')
    end_time = time.time()
    assert response_perf.status_code == 200
    assert (end_time - start_time) < 5.0, "L'ACPM doit être calculé en moins de 5 secondes"
    
    # Test 7: Vérification de la cohérence du poids total
    calculated_total = sum(edge['weight'] for edge in mst)
    assert abs(calculated_total - data['total_weight']) < 0.01, f"Poids total incohérent: calculé={calculated_total}, API={data['total_weight']}"
    
    # Test 8: Vérification des valeurs raisonnables
    assert data['total_weight'] > 0, "Le poids total doit être positif"
    assert data['total_weight'] < 1000000, f"Le poids total semble trop élevé: {data['total_weight']}"
    
    # Test 9: Vérification que toutes les stations sont présentes dans l'ACPM
    stations_in_acpm = set()
    for edge in mst:
        stations_in_acpm.add(edge['from']['id'])
        stations_in_acpm.add(edge['to']['id'])
    
    # Récupérer toutes les stations depuis l'API
    all_stations_response = client.get('/stations/list')
    assert all_stations_response.status_code == 200
    all_stations_data = json.loads(all_stations_response.data)
    
    # Vérifier que toutes les stations sont dans l'ACPM
    # Note: L'ACPM peut ne pas inclure toutes les stations si certaines sont isolées
    # Mais il doit inclure au moins la majorité des stations
    assert len(stations_in_acpm) >= total_stations * 0.9, f"L'ACPM doit inclure au moins 90% des stations: {len(stations_in_acpm)}/{total_stations}"

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