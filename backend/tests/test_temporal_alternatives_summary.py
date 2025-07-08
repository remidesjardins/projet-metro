"""
MetroCity - Mastercamp 2025
Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
Fichier: test_temporal_alternatives_summary.py
Description: Tests unitaires pour les résumés de chemins alternatifs temporels
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))
import pytest
import json
from app import app
from utils.data_manager import DataManager
from services.graph_service import GraphService

TRAJET_DEPART = 'Villejuif - Louis Aragon'
TRAJET_ARRIVEE = 'Gare du Nord'

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_temporal_alternatives_summary(client):
    """Affiche un résumé synthétique des 20 meilleurs chemins structurels ET temporels pour un trajet donné."""
    # --- Affichage des chemins structurels ---
    graph, positions, stations = DataManager.get_data()
    graph_service = GraphService(graph, stations)
    struct_paths = graph_service.find_multiple_paths(TRAJET_DEPART, TRAJET_ARRIVEE, max_paths=20)
    print("\nRésumé des 20 meilleurs chemins structurels :")
    for idx, path in enumerate(struct_paths):
        lines = [seg['line'] for seg in path]
        lines_grouped = [lines[0]] if lines else []
        for l in lines[1:]:
            if l != lines_grouped[-1]:
                lines_grouped.append(l)
        n_changes = max(0, len(lines_grouped) - 1)
        cost = graph_service._calculate_path_cost(path)
        summary = f"{idx+1:2d}. Lignes: {' → '.join(lines_grouped)} | Changements: {n_changes} | Coût structurel: {cost//60} min"
        print(summary)
    # --- Affichage des chemins temporels réels ---
    data = {
        'start_station': TRAJET_DEPART,
        'end_station': TRAJET_ARRIVEE,
        'departure_time': '08:30',
        'date': '2024-03-15',
        'max_paths': 20
    }
    response = client.post('/temporal/alternatives', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert 'paths' in result
    print("\nRésumé des 20 meilleurs chemins temporels (réels) :")
    for idx, path in enumerate(result['paths']):
        duration_min = int(round(path['total_duration'] / 60))
        lines = [seg['line'] for seg in path['segments']]
        lines_grouped = [lines[0]] if lines else []
        for l in lines[1:]:
            if l != lines_grouped[-1]:
                lines_grouped.append(l)
        n_changes = max(0, len(lines_grouped) - 1)
        summary = f"{idx+1:2d}. Durée: {duration_min:2d} min | Lignes: {' → '.join(lines_grouped)} | Changements: {n_changes}"
        print(summary)

def test_temporal_alternatives_summary_vja_montparnasse(client):
    """Affiche un résumé synthétique des 20 meilleurs chemins structurels ET temporels pour Villejuif - Louis Aragon -> Montparnasse."""
    graph, positions, stations = DataManager.get_data()
    graph_service = GraphService(graph, stations)
    struct_paths = graph_service.find_multiple_paths('Villejuif - Louis Aragon', 'Montparnasse Bienvenue', max_paths=20)
    print("\nRésumé des 20 meilleurs chemins structurels (VJA -> Montparnasse Bienvenue) :")
    for idx, path in enumerate(struct_paths):
        lines = [seg['line'] for seg in path]
        lines_grouped = [lines[0]] if lines else []
        for l in lines[1:]:
            if l != lines_grouped[-1]:
                lines_grouped.append(l)
        n_changes = max(0, len(lines_grouped) - 1)
        cost = graph_service._calculate_path_cost(path)
        summary = f"{idx+1:2d}. Lignes: {' → '.join(lines_grouped)} | Changements: {n_changes} | Coût structurel: {cost//60} min"
        print(summary)
    # --- Chemins temporels ---
    data = {
        'start_station': 'Villejuif - Louis Aragon',
        'end_station': 'Montparnasse Bienvenue',
        'departure_time': '08:30',
        'date': '2024-03-15',
        'max_paths': 20
    }
    response = client.post('/temporal/alternatives', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 200
    result = json.loads(response.data)
    assert 'paths' in result
    print("\nRésumé des 20 meilleurs chemins temporels (réels, VJA -> Montparnasse Bienvenue) :")
    for idx, path in enumerate(result['paths']):
        duration_min = int(round(path['total_duration'] / 60))
        lines = [seg['line'] for seg in path['segments']]
        lines_grouped = [lines[0]] if lines else []
        for l in lines[1:]:
            if l != lines_grouped[-1]:
                lines_grouped.append(l)
        n_changes = max(0, len(lines_grouped) - 1)
        summary = f"{idx+1:2d}. Durée: {duration_min:2d} min | Lignes: {' → '.join(lines_grouped)} | Changements: {n_changes}"
        print(summary)

def test_symmetry_vja_montparnasse(client):
    """Teste la symétrie des chemins structurels et temporels entre Villejuif - Louis Aragon et Montparnasse Bienvenue dans les deux sens."""
    from utils.data_manager import DataManager
    from services.graph_service import GraphService
    graph, positions, stations = DataManager.get_data()
    graph_service = GraphService(graph, stations)
    stations_pair = [
        ('Villejuif - Louis Aragon', 'Montparnasse Bienvenue'),
        ('Montparnasse Bienvenue', 'Villejuif - Louis Aragon')
    ]
    for start, end in stations_pair:
        struct_paths = graph_service.find_multiple_paths(start, end, max_paths=10)
        print(f"\nChemins structurels {start} -> {end} :")
        for idx, path in enumerate(struct_paths):
            lines = [seg['line'] for seg in path]
            lines_grouped = [lines[0]] if lines else []
            for l in lines[1:]:
                if l != lines_grouped[-1]:
                    lines_grouped.append(l)
            n_changes = max(0, len(lines_grouped) - 1)
            cost = graph_service._calculate_path_cost(path)
            summary = f"{idx+1:2d}. Lignes: {' → '.join(lines_grouped)} | Changements: {n_changes} | Coût: {cost//60} min"
            print(summary)
        # Test temporel
        data = {
            'start_station': start,
            'end_station': end,
            'departure_time': '08:30',
            'date': '2024-03-15',
            'max_paths': 10
        }
        response = client.post('/temporal/alternatives', data=json.dumps(data), content_type='application/json')
        assert response.status_code == 200
        result = json.loads(response.data)
        print(f"\nChemins temporels {start} -> {end} :")
        for idx, path in enumerate(result['paths']):
            duration_min = int(round(path['total_duration'] / 60))
            lines = [seg['line'] for seg in path['segments']]
            lines_grouped = [lines[0]] if lines else []
            for l in lines[1:]:
                if l != lines_grouped[-1]:
                    lines_grouped.append(l)
            n_changes = max(0, len(lines_grouped) - 1)
            summary = f"{idx+1:2d}. Durée: {duration_min} min | Lignes: {' → '.join(lines_grouped)} | Changements: {n_changes}"
            print(summary) 