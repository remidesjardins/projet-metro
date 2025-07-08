"""
MetroCity - Mastercamp 2025
Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
Fichier: co2.py
Description: Calculateur d'émissions CO2 pour les trajets de métro et RER
"""

import math

# Facteurs d'émissions CO2 par type de transport (en g CO2 / km / passager)

def calculate_distance_km(lat1, lon1, lat2, lon2):
    """
    Calcule la distance entre deux points GPS avec la formule de Haversine.
    Retourne la distance en kilomètres.
    """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return 0
    R = 6371.0
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    return distance

def calculate_emissions_from_ids(path, stations, positions):
    """
    Calcule les émissions de CO2 totales du trajet en grammes à partir d'une liste d'IDs de stations.
    """
    if len(path) < 2:
        return 0
    total_emissions = 0
    emission_factors = {
        'metro': 2.8,
        'rer': 2.9,
        'bus': 19.0
    }
    for i in range(len(path) - 1):
        station_id = path[i]
        next_station_id = path[i + 1]
        pos1 = positions.get(station_id)
        pos2 = positions.get(next_station_id)
        if pos1 and pos2:
            # pos1 et pos2 sont des (longitude, latitude) en degrés décimaux
            lat1, lon1 = pos1[1], pos1[0]  # Inverser car pos1 est (lon, lat)
            lat2, lon2 = pos2[1], pos2[0]  # Inverser car pos2 est (lon, lat)
            distance_km = calculate_distance_km(lat1, lon1, lat2, lon2)
            station_type = stations[station_id].get('type', 'metro')
            emission_factor = emission_factors.get(station_type, 2.8)
            total_emissions += distance_km * emission_factor
    return round(total_emissions, 2)

def calculate_emissions_from_segments(segments, stations, positions):
    """
    Calcule les émissions de CO2 totales du trajet en grammes à partir d'une liste de segments (chemin temporel).
    """
    if len(segments) < 1:
        return 0
    total_emissions = 0
    emission_factors = {
        'metro': 2.8,
        'rer': 2.9,
        'bus': 19.0
    }
    
    def find_station_id(name, line):
        """Trouve l'ID de station correspondant au nom et à la ligne."""
        # D'abord, essayer de trouver une correspondance exacte nom + ligne
        for sid, s in stations.items():
            if s['name'] == name:
                lines = s['line'] if isinstance(s['line'], list) else [s['line']]
                if line in lines:
                    return sid
        
        # Si pas trouvé, essayer de trouver par nom seulement (pour les correspondances)
        for sid, s in stations.items():
            if s['name'] == name:
                return sid
        
        return None
    
    for segment in segments:
        from_id = find_station_id(segment['from_station'], segment['line'])
        to_id = find_station_id(segment['to_station'], segment['line'])
        if from_id and to_id:
            pos1 = positions.get(from_id)
            pos2 = positions.get(to_id)
            if pos1 and pos2:
                # pos1 et pos2 sont des (longitude, latitude) en degrés décimaux
                lat1, lon1 = pos1[1], pos1[0]  # Inverser car pos1 est (lon, lat)
                lat2, lon2 = pos2[1], pos2[0]  # Inverser car pos2 est (lon, lat)
                distance_km = calculate_distance_km(lat1, lon1, lat2, lon2)
                station_type = stations[from_id].get('type', 'metro')
                emission_factor = emission_factors.get(station_type, 2.8)
                segment_emissions = distance_km * emission_factor
                total_emissions += segment_emissions
    
    return round(total_emissions, 2) 