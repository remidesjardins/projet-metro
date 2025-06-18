import logging
from pathlib import Path
from utils.gtfs_parser import parse_gtfs_to_graph
from utils.parser import load_data

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_gtfs_parser():
    """Test du parser GTFS et affichage des statistiques"""
    print("\n=== Test du parser GTFS ===")
    
    # Chemin vers les données GTFS
    data_dir = Path(__file__).parent / 'data' / 'gtfs'
    
    # Test du parser GTFS
    print("\n1. Test du parser GTFS direct :")
    gtfs_graph, gtfs_positions, gtfs_lines, gtfs_terminus, gtfs_branches = parse_gtfs_to_graph(str(data_dir))
    
    print(f"\nNombre de stations dans le graphe GTFS : {len(gtfs_graph)}")
    print(f"Nombre de positions : {len(gtfs_positions)}")
    print(f"Nombre de lignes uniques : {len(set().union(*[set(l) for l in gtfs_lines.values()]))}")
    print(f"Nombre de stations terminus : {len(gtfs_terminus)}")
    print(f"Nombre de stations avec branches : {len(gtfs_branches)}")
    
    # Afficher les stations et leurs lignes
    print("\nStations et leurs lignes :")
    print("-" * 50)
    for station, lines in sorted(gtfs_lines.items()):
        terminus_mark = " (Terminus)" if station in gtfs_terminus else ""
        branch_mark = f" (Branche {gtfs_branches[station]})" if station in gtfs_branches else ""
        print(f"{station:<30} | Lignes: {', '.join(sorted(lines))}{terminus_mark}{branch_mark}")
    print("-" * 50)
    
    # Afficher quelques exemples
    print("\nExemples de stations :")
    for i, (station, neighbors) in enumerate(gtfs_graph.items()):
        if i >= 3:  # Afficher seulement 3 exemples
            break
        print(f"\nStation : {station}")
        print(f"  Lignes : {', '.join(sorted(gtfs_lines[station]))}")
        print(f"  Position : {gtfs_positions.get(station, 'Non définie')}")
        print(f"  Est terminus : {station in gtfs_terminus}")
        print(f"  Numéro de branche : {gtfs_branches.get(station, 0)}")
        print(f"  Voisins : {neighbors[:3]}...")  # Afficher les 3 premiers voisins
    
    # Test du parser principal
    print("\n2. Test du parser principal :")
    graph, positions, stations = load_data()
    
    print(f"\nNombre de stations : {len(stations)}")
    print(f"Nombre de positions : {len(positions)}")
    print(f"Nombre de connexions : {sum(len(neighbors) for neighbors in graph.values()) // 2}")
    print(f"Nombre de stations terminus : {sum(1 for station in stations.values() if station['terminus'])}")
    print(f"Nombre de stations avec branche : {sum(1 for station in stations.values() if station['branche'] > 0)}")
    
    # Afficher quelques exemples de stations
    print("\nExemples de stations (format final) :")
    for i, (station_id, station_data) in enumerate(stations.items()):
        if i >= 3:  # Afficher seulement 3 exemples
            break
        print(f"\nStation ID : {station_id}")
        print(f"  Nom : {station_data['name']}")
        print(f"  Lignes : {station_data['line']}")
        print(f"  Est terminus : {station_data['terminus']}")
        print(f"  Numéro de branche : {station_data['branche']}")
        print(f"  Position : {positions.get(station_id, 'Non définie')}")
        print(f"  Voisins : {list(graph[station_id].items())[:3]}...")  # Afficher les 3 premiers voisins

if __name__ == '__main__':
    test_gtfs_parser() 