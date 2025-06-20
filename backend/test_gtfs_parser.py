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
    # Chemin vers les données GTFS
    data_dir = Path(__file__).parent / 'data' / 'gtfs'
    
    # Test du parser GTFS
    gtfs_graph, gtfs_positions, gtfs_lines, gtfs_terminus, gtfs_branches = parse_gtfs_to_graph(str(data_dir))
    
    # Test du parser principal
    graph, positions, stations = load_data()
    
    return {
        'gtfs_stations': len(gtfs_graph),
        'gtfs_positions': len(gtfs_positions),
        'gtfs_lines': len(set().union(*[set(l) for l in gtfs_lines.values()])),
        'gtfs_terminus': len(gtfs_terminus),
        'gtfs_branches': len(gtfs_branches),
        'final_stations': len(stations),
        'final_positions': len(positions),
        'final_connections': sum(len(neighbors) for neighbors in graph.values()) // 2,
        'final_terminus': sum(1 for station in stations.values() if station['terminus']),
        'final_branches': sum(1 for station in stations.values() if station['branche'] > 0)
    }

if __name__ == '__main__':
    results = test_gtfs_parser()
    print("Résultats du test GTFS parser:")
    for key, value in results.items():
        print(f"  {key}: {value}") 