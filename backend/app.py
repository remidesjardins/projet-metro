from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_compress import Compress
from routes.stations import stations_bp
from routes.graph import graph_bp
from routes.connexite import connexite_bp
from routes.acpm import acpm_bp
from routes.shortest_path import shortest_path_bp
from routes.itineraire import itineraire_bp
from routes.cache import cache_bp
from routes.temporal_path_flask import temporal_bp
from config import get_config
from utils.error_handler import (
    APIError, ValidationError, NotFoundError, ServiceUnavailableError,
    create_error_response, handle_generic_error
)
import logging
import time

def create_app(config_class=None):
    """Factory function pour créer l'application Flask"""
    app = Flask(__name__)
    
    # Charger la configuration
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)
    
    # Configuration du logging
    logging.basicConfig(
        level=getattr(logging, app.config['LOG_LEVEL']),
        format=app.config['LOG_FORMAT']
    )
    
    # Configuration de la compression
    Compress(app)
    
    # Configuration CORS dynamique
    CORS(app, resources={
        r"/*": {
            "origins": app.config['CORS_ORIGINS'],
            "methods": app.config['CORS_METHODS'],
            "allow_headers": app.config['CORS_ALLOW_HEADERS'],
            "supports_credentials": app.config['CORS_SUPPORTS_CREDENTIALS']
        }
    })

    # Enregistrement des blueprints
    app.register_blueprint(stations_bp)
    app.register_blueprint(graph_bp)
    app.register_blueprint(connexite_bp)
    app.register_blueprint(acpm_bp)
    app.register_blueprint(shortest_path_bp)
    app.register_blueprint(itineraire_bp)
    app.register_blueprint(cache_bp)
    app.register_blueprint(temporal_bp)

    @app.route('/')
    def index():
        """Page d'accueil de l'API."""
        return {
            'name': 'Paris Metro API',
            'version': '3.0',
            'environment': app.config['ENV'] if hasattr(app.config, 'ENV') else 'development',
            'endpoints': {
                'GET /stations': 'Liste des stations avec coordonnées',
                'GET /graph': 'Graphe complet du métro',
                'GET /connexity': 'Vérification de la connexité du graphe',
                'GET /acpm': 'Arbre couvrant de poids minimal (Kruskal)',
                'POST /shortest-path': 'Plus court chemin entre deux stations',
                'POST /itineraire': 'Calcul d\'itinéraire entre deux stations',
                'GET /stations/list': 'Liste de toutes les stations uniques',
                'GET /cache/info': 'Informations sur l\'état du cache',
                'POST /cache/clear': 'Effacer le cache',
                'POST /cache/reload': 'Recharger les données depuis GTFS',
                'GET /performance/test': 'Test de performance',
                'POST /temporal/path': 'Chemin temporel optimal avec horaires',
                'POST /temporal/alternatives': 'Chemins alternatifs temporels',
                'GET /temporal/stations': 'Liste des stations pour calculs temporels',
                'GET /temporal/station/{station}/lines': 'Lignes desservant une station',
                'GET /temporal/next-departure': 'Prochain départ d\'une ligne'
            }
        }

    @app.route('/health')
    def health():
        """Endpoint de monitoring de santé."""
        return {
            'status': 'ok',
            'environment': app.config['ENV'],
            'debug': app.config['DEBUG']
        }

    @app.before_request
    def start_timer():
        request._start_time = time.time()

    @app.after_request
    def log_request(response):
        duration = None
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
        logger = logging.getLogger('request_logger')
        logger.info(
            f"{request.remote_addr} {request.method} {request.path} {response.status_code} "
            f"{duration:.3f}s"
        )
        return response

    @app.after_request
    def set_security_headers(response):
        headers = app.config.get('SECURITY_HEADERS', {})
        for k, v in headers.items():
            response.headers[k] = v
        return response

    # Gestionnaires d'erreurs standardisés
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        return create_error_response(error)

    @app.errorhandler(NotFoundError)
    def handle_not_found_error(error):
        return create_error_response(error)

    @app.errorhandler(ServiceUnavailableError)
    def handle_service_unavailable_error(error):
        return create_error_response(error)

    @app.errorhandler(APIError)
    def handle_api_error(error):
        return create_error_response(error)

    @app.errorhandler(404)
    def not_found(error):
        return create_error_response(NotFoundError("Endpoint non trouvé"))

    @app.errorhandler(500)
    def internal_error(error):
        return handle_generic_error(error)

    @app.errorhandler(Exception)
    def handle_exception(error):
        return handle_generic_error(error)

    return app

# Instance de l'application
app = create_app()

if __name__ == '__main__':
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )