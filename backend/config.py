"""
MetroCity - Mastercamp 2025
Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
Fichier: config.py
Description: Configuration de l'application Flask avec gestion des environnements
"""

# Configuration de l'application
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration de base"""
    SECRET_KEY = os.getenv('SECRET_KEY', None)
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    ENV = os.getenv('ENV', 'development')
    
    # Configuration du serveur
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5050))
    
    # Configuration GTFS
    GTFS_DATA_PATH = os.environ.get('GTFS_DATA_PATH') or os.path.join(os.path.dirname(__file__), 'data', 'gtfs')
    
    # Configuration de l'algorithme temporel
    TEMPORAL_MAX_STRUCTURAL_PATHS = int(os.environ.get('TEMPORAL_MAX_STRUCTURAL_PATHS', 10))
    TEMPORAL_DEFAULT_MAX_PATHS = int(os.environ.get('TEMPORAL_DEFAULT_MAX_PATHS', 3))
    TEMPORAL_DEFAULT_MAX_WAIT_TIME = int(os.environ.get('TEMPORAL_DEFAULT_MAX_WAIT_TIME', 1800))
    
    # Configuration du cache
    CACHE_TIMEOUT = int(os.environ.get('CACHE_TIMEOUT', 3600))
    CACHE_ENABLED = os.environ.get('CACHE_ENABLED', 'True').lower() == 'true'
    
    # Configuration des logs
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', '%(asctime)s - %(levelname)s - %(message)s')
    
    # Configuration CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')
    CORS_METHODS = os.getenv('CORS_METHODS', 'GET,POST,OPTIONS').split(',')
    CORS_ALLOW_HEADERS = os.getenv('CORS_ALLOW_HEADERS', 'Content-Type,Authorization').split(',')
    CORS_SUPPORTS_CREDENTIALS = os.getenv('CORS_SUPPORTS_CREDENTIALS', 'False').lower() == 'true'
    
    # Limite la taille des requêtes à 2 Mo par défaut
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 2 * 1024 * 1024))
    
    # Headers de sécurité
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=63072000; includeSubDomains; preload',
        'Content-Security-Policy': os.getenv('CSP', "default-src 'self'")
    }

    @classmethod
    def validate(cls):
        if cls.ENV == 'production':
            if not cls.SECRET_KEY or cls.SECRET_KEY == 'changeme':
                raise RuntimeError('SECRET_KEY doit être défini en production !')
            cls.DEBUG = False

class DevelopmentConfig(Config):
    """Configuration pour le développement"""
    DEBUG = False  # Désactivé pour éviter le double chargement
    ENV = 'development'

class ProductionConfig(Config):
    """Configuration pour la production"""
    DEBUG = False
    ENV = 'production'
    
    def __init__(self):
        # En production, utiliser des valeurs sécurisées
        if not os.environ.get('SECRET_KEY'):
            raise ValueError("SECRET_KEY must be set in production environment")
        
        # CORS plus restrictif en production
        cors_origins = os.environ.get('CORS_ORIGINS', '').split(',')
        if not cors_origins or cors_origins == ['']:
            raise ValueError("CORS_ORIGINS must be set in production environment")
        
        self.CORS_ORIGINS = cors_origins
        self.SECRET_KEY = os.environ.get('SECRET_KEY')

class TestingConfig(Config):
    """Configuration pour les tests"""
    TESTING = True
    DEBUG = True
    CACHE_ENABLED = False

# Configuration par défaut selon l'environnement
def get_config():
    """Retourne la configuration appropriée selon l'environnement"""
    env = os.getenv('ENV', 'development')
    
    if env == 'production':
        ProductionConfig.validate()
        return ProductionConfig()
    elif env == 'testing':
        return TestingConfig()
    else:
        DevelopmentConfig.validate()
        return DevelopmentConfig()
