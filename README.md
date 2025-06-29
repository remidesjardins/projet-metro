# 🚇 Paris Metro API & Frontend

Application complète pour la recherche d'itinéraires dans le métro parisien avec calculs temporels et visualisation cartographique.

## 🏗️ Architecture

- **Backend** : Flask API avec algorithmes de graphes (Dijkstra, Kruskal)
- **Frontend** : Vue 3 + Leaflet pour la cartographie
- **Données** : GTFS (General Transit Feed Specification)
- **Cache** : Système de cache optimisé pour les performances

## 🚀 Installation

### Prérequis

- Python 3.8+
- Node.js 16+
- npm ou yarn

### Backend

1. **Cloner le projet**
```bash
git clone <repository-url>
cd projet-metro/backend
```

2. **Créer un environnement virtuel**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

4. **Configuration**
```bash
# Copier le fichier d'exemple
cp env.example .env

# Éditer les variables d'environnement
nano .env
```

5. **Lancer le serveur**
```bash
python app.py
```

Le serveur sera accessible sur `http://localhost:5050`

### Frontend

1. **Installer les dépendances**
```bash
cd ../frontend
npm install
```

2. **Configuration**
```bash
# Copier le fichier d'exemple
cp env.example .env

# Éditer les variables d'environnement
nano .env
```

3. **Lancer en mode développement**
```bash
npm run dev
```

L'application sera accessible sur `http://localhost:5173`

## ⚙️ Configuration

### Variables d'environnement Backend

| Variable | Description | Défaut |
|----------|-------------|---------|
| `FLASK_ENV` | Environnement (development/production/testing) | development |
| `FLASK_DEBUG` | Mode debug | True |
| `FLASK_HOST` | Host du serveur | 0.0.0.0 |
| `FLASK_PORT` | Port du serveur | 5050 |
| `SECRET_KEY` | Clé secrète Flask | dev-secret-key |
| `CORS_ORIGINS` | Origines autorisées pour CORS | http://localhost:5173 |
| `GTFS_DATA_PATH` | Chemin vers les données GTFS | data/gtfs |
| `CACHE_ENABLED` | Activer le cache | True |
| `LOG_LEVEL` | Niveau de log | INFO |

### Variables d'environnement Frontend

| Variable | Description | Défaut |
|----------|-------------|---------|
| `VITE_API_URL` | URL de l'API backend | http://localhost:5050 |
| `VITE_APP_TITLE` | Titre de l'application | Paris Metro |
| `VITE_APP_VERSION` | Version de l'application | 3.0.0 |

## 📚 API Endpoints

### Stations
- `GET /stations` - Liste des stations avec coordonnées
- `GET /stations/list` - Liste des stations uniques
- `GET /stations/ordered_by_line` - Stations ordonnées par ligne

### Itinéraires
- `POST /shortest-path` - Plus court chemin entre deux stations
- `POST /itineraire` - Calcul d'itinéraire détaillé

### Algorithmes
- `GET /connexity` - Vérification de la connexité du graphe
- `GET /acpm` - Arbre couvrant de poids minimal (Kruskal)

### Temporel
- `POST /temporal/path` - Chemin temporel optimal
- `POST /temporal/alternatives` - Chemins alternatifs temporels
- `GET /temporal/stations` - Stations pour calculs temporels

### Cache
- `GET /cache/info` - Informations sur l'état du cache
- `POST /cache/clear` - Effacer le cache
- `POST /cache/reload` - Recharger les données

## 🧪 Tests

### Backend
```bash
cd backend
python -m pytest tests/ -v
```

### Frontend
```bash
cd frontend
npm run build
```

## 🚀 Production

### Backend
```bash
# Définir l'environnement
export FLASK_ENV=production
export SECRET_KEY=your-secure-secret-key
export CORS_ORIGINS=https://yourdomain.com

# Lancer avec Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5050 app:app
```

### Frontend
```bash
# Build de production
npm run build

# Servir les fichiers statiques
npm install -g serve
serve -s dist -l 3000
```

## 📁 Structure du projet

```
projet-metro/
├── backend/
│   ├── app.py                 # Application Flask principale
│   ├── config.py              # Configuration
│   ├── requirements.txt       # Dépendances Python
│   ├── routes/                # Routes API
│   ├── services/              # Services métier
│   ├── utils/                 # Utilitaires
│   ├── data/                  # Données GTFS
│   └── tests/                 # Tests
├── frontend/
│   ├── src/
│   │   ├── components/        # Composants Vue
│   │   ├── views/             # Vues
│   │   ├── services/          # Services API
│   │   └── router/            # Routeur Vue
│   ├── package.json           # Dépendances Node.js
│   └── vite.config.js         # Configuration Vite
└── README.md
```

## 🔧 Développement

### Ajouter une nouvelle route
1. Créer un nouveau fichier dans `backend/routes/`
2. Définir le blueprint
3. Enregistrer dans `app.py`

### Ajouter un nouveau composant
1. Créer le composant dans `frontend/src/components/`
2. Importer et utiliser dans les vues

## 📝 Logs

Les logs sont configurés selon l'environnement :
- **Development** : DEBUG
- **Production** : WARNING
- **Testing** : INFO

## 🤝 Contribution

1. Fork le projet
2. Créer une branche feature
3. Commiter les changements
4. Pousser vers la branche
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. 