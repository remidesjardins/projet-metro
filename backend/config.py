# Configuration de l'application
import os

class Config:
    """Configuration de base"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Configuration GTFS
    GTFS_DATA_PATH = os.path.join(os.path.dirname(__file__), 'data', 'gtfs')
    
    # Configuration de l'algorithme temporel
    TEMPORAL_MAX_STRUCTURAL_PATHS = 10  # Nombre optimal de chemins structurels
    TEMPORAL_DEFAULT_MAX_PATHS = 3     # Nombre de chemins alternatifs par défaut
    TEMPORAL_DEFAULT_MAX_WAIT_TIME = 1800  # Temps d'attente maximum par défaut (30 min)
    
    # Configuration du cache
    CACHE_TIMEOUT = 3600  # 1 heure
    
    # Configuration des logs
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
