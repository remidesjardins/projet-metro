#!/usr/bin/env python3
"""
Exemple d'utilisation de l'API pour tester la fonctionnalité d'itinéraire avec horaire d'arrivée
"""

import requests
import json
from datetime import datetime

def test_arrival_api():
    """Test de l'API d'itinéraire avec horaire d'arrivée"""
    
    # URL de l'API (ajuster selon votre configuration)
    base_url = "http://localhost:5000"
    
    # Test 1: Itinéraire avec horaire d'arrivée
    print("=== Test 1: Itinéraire avec horaire d'arrivée ===")
    
    arrival_data = {
        "start_station": "Châtelet",
        "end_station": "Bastille",
        "arrival_time": "09:00",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "max_wait_time": 1800
    }
    
    try:
        response = requests.post(
            f"{base_url}/temporal/path-arrival",
            json=arrival_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Itinéraire trouvé!")
            print(f"   Départ: {result.get('departure_time', 'N/A')}")
            print(f"   Arrivée: {result.get('arrival_time', 'N/A')}")
            print(f"   Durée totale: {result.get('total_duration', 0) // 60} minutes")
            print(f"   Temps d'attente: {result.get('total_wait_time', 0) // 60} minutes")
            
            # Informations spécifiques à l'arrivée
            arrival_info = result.get('arrival_info', {})
            if arrival_info:
                print(f"   Heure d'arrivée demandée: {arrival_info.get('requested_arrival_time')}")
                print(f"   Heure d'arrivée réelle: {arrival_info.get('actual_arrival_time')}")
                print(f"   Écart: {arrival_info.get('arrival_difference_minutes')} minutes")
            
            # Détails des segments
            segments = result.get('segments', [])
            print(f"\n   Segments ({len(segments)}):")
            for i, segment in enumerate(segments, 1):
                print(f"   {i}. {segment['from_station']} → {segment['to_station']} (Ligne {segment['line']})")
                print(f"      Départ: {segment['departure_time']}, Arrivée: {segment['arrival_time']}")
                if segment.get('wait_time', 0) > 0:
                    print(f"      Attente: {segment['wait_time'] // 60} minutes")
                if segment.get('transfer_time', 0) > 0:
                    print(f"      Correspondance: {segment['transfer_time'] // 60} minutes")
        
        else:
            print(f"❌ Erreur {response.status_code}: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur. Assurez-vous que le serveur backend est démarré.")
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_comparison_api():
    """Compare l'API normale vs l'API avec horaire d'arrivée"""
    
    print("\n=== Test 2: Comparaison API normale vs arrivée ===")
    
    base_url = "http://localhost:5000"
    target_time = "09:00"
    
    # Test avec l'API normale (départ)
    normal_data = {
        "start_station": "Châtelet",
        "end_station": "Bastille",
        "departure_time": target_time,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "max_wait_time": 1800
    }
    
    # Test avec l'API arrivée
    arrival_data = {
        "start_station": "Châtelet",
        "end_station": "Bastille",
        "arrival_time": target_time,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "max_wait_time": 1800
    }
    
    try:
        # Appel API normale
        normal_response = requests.post(
            f"{base_url}/temporal/path",
            json=normal_data,
            headers={"Content-Type": "application/json"}
        )
        
        # Appel API arrivée
        arrival_response = requests.post(
            f"{base_url}/temporal/path-arrival",
            json=arrival_data,
            headers={"Content-Type": "application/json"}
        )
        
        if normal_response.status_code == 200 and arrival_response.status_code == 200:
            normal_result = normal_response.json()
            arrival_result = arrival_response.json()
            
            print("✅ Comparaison réussie!")
            print(f"   Normal - Départ: {normal_result.get('departure_time')}, Arrivée: {normal_result.get('arrival_time')}")
            print(f"   Arrivée - Départ: {arrival_result.get('departure_time')}, Arrivée: {arrival_result.get('arrival_time')}")
            
            # Calculer les écarts
            arrival_info = arrival_result.get('arrival_info', {})
            if arrival_info:
                arrival_diff = arrival_info.get('arrival_difference_minutes', 0)
                print(f"   Écart avec l'heure d'arrivée souhaitée: {arrival_diff} minutes")
                
                if arrival_diff <= 5:
                    print("   ✅ Excellent! L'itinéraire arrive très proche de l'heure souhaitée")
                elif arrival_diff <= 15:
                    print("   ✅ Bon! L'itinéraire arrive proche de l'heure souhaitée")
                else:
                    print("   ⚠️ L'itinéraire arrive avec un écart important")
        
        else:
            print(f"❌ Erreur dans les appels API")
            if normal_response.status_code != 200:
                print(f"   API normale: {normal_response.status_code} - {normal_response.text}")
            if arrival_response.status_code != 200:
                print(f"   API arrivée: {arrival_response.status_code} - {arrival_response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Impossible de se connecter au serveur. Assurez-vous que le serveur backend est démarré.")
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_different_stations():
    """Test avec différentes paires de stations"""
    
    print("\n=== Test 3: Différentes paires de stations ===")
    
    base_url = "http://localhost:5000"
    test_cases = [
        ("Châtelet", "Bastille"),
        ("Gare du Nord", "Gare de Lyon"),
        ("Montparnasse", "Saint-Lazare"),
    ]
    
    for start_station, end_station in test_cases:
        print(f"\nTest: {start_station} → {end_station}")
        
        arrival_data = {
            "start_station": start_station,
            "end_station": end_station,
            "arrival_time": "10:00",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "max_wait_time": 1800
        }
        
        try:
            response = requests.post(
                f"{base_url}/temporal/path-arrival",
                json=arrival_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                arrival_info = result.get('arrival_info', {})
                arrival_diff = arrival_info.get('arrival_difference_minutes', 0)
                print(f"   ✅ Écart: {arrival_diff} minutes")
            else:
                print(f"   ❌ Erreur {response.status_code}")
        
        except Exception as e:
            print(f"   ❌ Erreur: {e}")

if __name__ == "__main__":
    print("🚇 Test de l'API d'itinéraire avec horaire d'arrivée")
    print("=" * 50)
    
    test_arrival_api()
    test_comparison_api()
    test_different_stations()
    
    print("\n" + "=" * 50)
    print("✅ Tests terminés!") 