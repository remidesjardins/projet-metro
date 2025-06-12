from flask import Flask, jsonify
from flask_cors import CORS
from routes.stations import stations_bp
from routes.graph import graph_bp
from routes.connexity import connexity_bp
from routes.acpm import acpm_bp
from routes.shortest_path import shortest_path_bp
from routes.itineraire import itineraire_bp

app = Flask(__name__)
# Configuration CORS plus permissive pour le développement
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:5173", "http://127.0.0.1:5173"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Enregistrer les blueprints
app.register_blueprint(stations_bp)
app.register_blueprint(graph_bp)
app.register_blueprint(connexity_bp)
app.register_blueprint(acpm_bp)
app.register_blueprint(shortest_path_bp)
app.register_blueprint(itineraire_bp)

@app.route('/')
def index():
    """Page d'accueil de l'API."""
    return {
        'name': 'Paris Metro API',
        'version': '1.0',
        'endpoints': {
            'GET /stations': 'Liste des stations avec coordonnées',
            'GET /graph': 'Graphe complet du métro',
            'GET /connexity': 'Vérification de la connexité du graphe',
            'GET /acpm': 'Arbre couvrant de poids minimal (Kruskal)',
            'POST /shortest-path': 'Plus court chemin entre deux stations',
            'POST /itineraire': 'Calcul d\'itinéraire entre deux stations',
            'GET /stations/list': 'Liste de toutes les stations uniques'
        }
    }

if __name__ == '__main__':
    app.run(debug=True, port=5050)
