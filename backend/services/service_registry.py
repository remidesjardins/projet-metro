from utils.data_manager import DataManager
from services.graph_service import GraphService
from services.gtfs_temporal import GTFSemporalService
from services.temporal_path import TemporalPathService
import os

_graph_service = None
_gtfs_service = None
_temporal_service = None

def get_graph_service():
    global _graph_service
    if _graph_service is None:
        graph, positions, stations = DataManager.get_data()
        _graph_service = GraphService(graph, stations)
        print('[INIT] GraphService chargé')
    return _graph_service

def get_gtfs_service():
    global _gtfs_service
    if _gtfs_service is None:
        gtfs_dir = os.path.join(os.path.dirname(__file__), 'data/gtfs')
        if not os.path.exists(gtfs_dir):
            gtfs_dir = os.path.join(os.path.dirname(__file__), '../data/gtfs')
        _gtfs_service = GTFSemporalService(gtfs_dir)
        print('[INIT] GTFSemporalService chargé')
    return _gtfs_service

def get_temporal_service():
    global _temporal_service
    if _temporal_service is None:
        _temporal_service = TemporalPathService(get_graph_service(), get_gtfs_service())
        print('[INIT] TemporalPathService chargé')
    return _temporal_service

def init_all_services():
    get_graph_service()
    get_gtfs_service()
    get_temporal_service()
    print('[INIT] Tous les services ont été préchargés au démarrage')

# Appel automatique au démarrage du serveur
init_all_services() 