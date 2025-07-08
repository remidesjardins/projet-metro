"""
MetroCity - Mastercamp 2025
Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
Fichier: service_registry.py
Description: Registre centralisé des services pour l'injection de dépendances
"""

from utils.data_manager import DataManager
from services.graph_service import GraphService
from services.gtfs_temporal import GTFSemporalService
from services.temporal_path import TemporalPathService
import os
import logging

_graph_service = None
_gtfs_service = None
_temporal_service = None

logger = logging.getLogger(__name__)

def get_graph_service() -> GraphService:
    """Obtient l'instance du GraphService (singleton)."""
    global _graph_service
    if _graph_service is None:
        graph, positions, stations = DataManager.get_data()
        _graph_service = GraphService(graph, stations)
        logger.info('[INIT] GraphService chargé')
    return _graph_service

def get_gtfs_service() -> GTFSemporalService:
    """Obtient l'instance du GTFSTemporalService (singleton)."""
    global _gtfs_service
    if _gtfs_service is None:
        gtfs_dir = os.path.join(os.path.dirname(__file__), 'data/gtfs')
        if not os.path.exists(gtfs_dir):
            gtfs_dir = os.path.join(os.path.dirname(__file__), '../data/gtfs')
        _gtfs_service = GTFSemporalService(gtfs_dir)
        logger.info('[INIT] GTFSemporalService chargé')
    return _gtfs_service

def get_temporal_service() -> TemporalPathService:
    """Obtient l'instance du TemporalService (singleton)."""
    global _temporal_service
    if _temporal_service is None:
        _temporal_service = TemporalPathService(get_graph_service(), get_gtfs_service())
        logger.info('[INIT] TemporalPathService chargé')
    return _temporal_service

def preload_services():
    """Précharge tous les services au démarrage de l'application."""
    get_graph_service()
    get_gtfs_service()
    get_temporal_service()
    logger.info('[INIT] Tous les services ont été préchargés au démarrage')

# Appel automatique au démarrage du serveur
preload_services() 