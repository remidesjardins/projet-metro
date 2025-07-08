# 🚇 MetroCity - Optimisation de trajets pour le réseau de transport parisien

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.5-green.svg)](https://vuejs.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey.svg)](https://flask.palletsprojects.com)

> Application web complète pour l'optimisation d'itinéraires écologiques dans le réseau de transport parisien, développée dans le cadre du projet **Mastercamp 2025**.

## 📋 Table des matières

- [🎯 Fonctionnalités principales](#-fonctionnalités-principales)
- [🏗️ Architecture technique](#️-architecture-technique)
- [🚀 Installation et démarrage](#-installation-et-démarrage)
- [📊 Utilisation](#-utilisation)
- [🧪 Tests et qualité](#-tests-et-qualité)
- [📈 Performance et optimisations](#-performance-et-optimisations)
- [🌍 Données et sources](#-données-et-sources)
- [👥 Équipe et contributions](#-équipe-et-contributions)
- [📄 Documentation](#-documentation)
- [🤝 Contribuer](#-contribuer)
- [🎓 Contexte académique](#-contexte-académique)

## 🎯 Fonctionnalités principales

### ✨ Recherche d'itinéraires avancée
- **Algorithmes temporels** : Calcul basé sur les horaires réels GTFS
- **Optimisation multi-critères** : Durée, émissions CO₂, nombre de correspondances
- **Chemins alternatifs** : Jusqu'à 3 itinéraires optimisés différents
- **Support Metro + RER** : Intégration complète du réseau francilien

### 🗺️ Interface cartographique interactive
- **Carte Leaflet** : Visualisation en temps réel du réseau
- **Sélection graphique** : Choisir les stations directement sur la carte
- **Polylines colorées** : Lignes métro/RER avec couleurs officielles
- **Design glassmorphism** : Interface moderne et élégante

### 🌱 Impact environnemental
- **Calcul CO₂** : Émissions précises par trajet
- **Comparaison écologique** : Alternatives moins polluantes
- **Sensibilisation RSE** : Objectifs de développement durable

### 🔧 Outils d'analyse réseau
- **Test de connexité** : Vérification de l'intégrité du graphe
- **ACPM (Kruskal)** : Arbre couvrant de poids minimal
- **Visualisation des lignes** : Affichage sélectif du réseau

## 🏗️ Architecture technique

### Structure du projet

```
MetroCity/
├── backend/                 # API Flask Python
│   ├── app.py              # Application principale Flask
│   ├── config.py           # Configuration de l'environnement
│   ├── routes/             # Points d'entrée API
│   │   ├── stations.py     # Gestion des stations
│   │   ├── shortest_path.py # Itinéraires classiques
│   │   ├── temporal_path_flask.py # Itinéraires temporels
│   │   ├── connexite.py    # Tests de connexité
│   │   ├── acpm.py         # Arbre couvrant minimal
│   │   ├── cache.py        # Gestion du cache
│   │   └── itineraire.py   # Calculs d'itinéraires
│   ├── services/           # Logique métier
│   │   ├── dijkstra.py     # Algorithme Dijkstra
│   │   ├── temporal_path.py # Algorithmes temporels
│   │   ├── gtfs_temporal.py # Service GTFS
│   │   ├── kruskal.py      # Algorithme Kruskal
│   │   ├── connexite.py    # Vérification connexité
│   │   ├── graph_service.py # Service de graphe
│   │   └── transfer_service.py # Gestion correspondances
│   ├── utils/              # Utilitaires et parseurs
│   │   ├── parser.py       # Parser de données
│   │   ├── gtfs_parser.py  # Parser GTFS
│   │   ├── co2.py          # Calculs CO₂
│   │   ├── data_manager.py # Gestion des données
│   │   └── error_handler.py # Gestion d'erreurs
│   ├── tests/              # Suite de tests complète
│   │   ├── test_temporal_path.py
│   │   ├── test_connexite_service.py
│   │   ├── test_api_endpoints.py
│   │   └── test_arrival_path.py
│   └── data/gtfs/          # Données transport IDFM
│       ├── routes.txt      # Lignes de transport
│       ├── stops.txt       # Stations et arrêts
│       ├── trips.txt       # Voyages
│       ├── stop_times.txt  # Horaires détaillés
│       └── transfers.txt   # Correspondances
├── frontend/               # Interface Vue.js
│   ├── src/
│   │   ├── App.vue         # Composant principal
│   │   ├── main.js         # Point d'entrée
│   │   ├── components/     # Composants réutilisables
│   │   │   ├── MetroMapLeaflet.vue # Carte interactive
│   │   │   ├── UserControlPanel.vue # Panneau de contrôle
│   │   │   ├── ItineraryDisplay.vue # Affichage itinéraires
│   │   │   ├── AlternativePathsSelector.vue # Sélection alternatives
│   │   │   ├── LoadingScreen.vue # Écran de chargement
│   │   │   └── ServerStatus.vue # Statut serveur
│   │   ├── hooks/          # Hooks de logique métier
│   │   │   ├── useItinerary.js # Logique itinéraires
│   │   │   ├── useStations.js # Gestion stations
│   │   │   ├── useAdvancedTools.js # Outils avancés
│   │   │   ├── usePathAnalysis.js # Analyse chemins
│   │   │   └── useTemporalData.js # Données temporelles
│   │   ├── services/       # Services API
│   │   │   ├── api.js      # Client API
│   │   │   └── notificationService.js # Notifications
│   │   ├── constants/      # Constantes métro/RER
│   │   │   └── metro.js    # Couleurs et données lignes
│   │   ├── views/          # Pages de l'application
│   │   │   └── HomeView.vue # Vue principale
│   │   └── assets/         # Ressources statiques
│   │       ├── base.css    # Styles de base
│   │       ├── glass.css   # Design glassmorphism
│   │       └── global.css  # Styles globaux
│   ├── package.json        # Dépendances Node.js
│   └── vite.config.js      # Configuration Vite
├── RAPPORT_TECHNIQUE_METRO_PARIS.md # Documentation technique
└── README.md               # Ce fichier
```

### 🐍 Backend Flask
- **API RESTful** : Endpoints optimisés avec cache intelligent
- **Données GTFS** : Parser optimisé pour les données IDFM
- **Algorithmes de graphe** : Dijkstra temporel, DFS, Kruskal
- **Tests automatisés** : Couverture complète avec pytest
- **Gestion d'erreurs** : Système centralisé d'erreurs
- **Cache intelligent** : Optimisation des performances

### 🎨 Frontend Vue.js
- **Composition API** : Architecture moderne et réactive
- **Hooks personnalisés** : Réutilisabilité et séparation des responsabilités
- **Design responsive** : Adaptation mobile et desktop
- **Performance optimisée** : Lazy loading et cache intelligent
- **Interface glassmorphism** : Design moderne avec effets de transparence
- **Cartographie Leaflet** : Visualisation interactive du réseau

## 🚀 Installation et démarrage

### Prérequis
- Python 3.8+ avec pip
- Node.js 16+ avec npm
- Git

### 1. Clonage du projet
```bash
git clone <repository-url>
cd projet-metro
```

### 2. Configuration Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configuration Frontend
```bash
cd frontend
npm install
```

### 4. Variables d'environnement (Optionnel)
Créer un fichier `.env` dans le dossier backend :
```env
# Développement
DEBUG=true
SECRET_KEY=your-secret-key-here
HOST=127.0.0.1
PORT=5050

# Production
ENV=production
SECRET_KEY=secure-production-key
CORS_ORIGINS=https://your-domain.com
```

### 5. Démarrage des services

**Backend** (Terminal 1) :
```bash
cd backend
python app.py
# → API accessible sur http://localhost:5050
```

**Frontend** (Terminal 2) :
```bash
cd frontend
npm run dev
# → Interface sur http://localhost:5173
```

## 📊 Utilisation

### Interface utilisateur
1. **Sélection des stations** : Tapez ou cliquez sur la carte
2. **Choix du mode** : Classique ou temporel avec horaires
3. **Paramétrage** : Heure de départ, critère de tri
4. **Résultats** : Itinéraires alternatifs avec détails

### API Endpoints principaux
```bash
# Santé de l'API
GET /health

# Liste des stations
GET /stations?include_rer=true

# Recherche d'itinéraire classique
POST /shortest_path
{
  "start": "Châtelet",
  "end": "République"
}

# Recherche temporelle
POST /temporal_path
{
  "start": "Châtelet",
  "end": "République",
  "departure_time": "08:30",
  "departure_date": "2024-01-15"
}

# Test de connexité
GET /connexity?station=Châtelet

# ACPM du réseau
GET /acpm

# Informations sur le cache
GET /cache/info

# Rechargement des données
POST /cache/reload
```

## 🧪 Tests et qualité

### Suite de tests Backend
```bash
cd backend
python -m pytest tests/ -v

# Tests spécifiques
python -m pytest tests/test_temporal_path.py -v
python -m pytest tests/test_connexite_service.py -v
python -m pytest tests/test_api_endpoints.py -v
```

### Linting Frontend
```bash
cd frontend
npm run lint
npm run format
```

### Couverture des tests
- **Backend** : >90% de couverture
- **Tests unitaires** : Services et utilitaires
- **Tests d'intégration** : Endpoints API
- **Tests de performance** : Algorithmes temporels

## 📈 Performance et optimisations

### Backend
- **Cache intelligent** : Données GTFS mises en cache
- **Parsing optimisé** : Chunks pour stop_times.txt
- **Barres de progression** : tqdm pour retour utilisateur
- **Index mémoire** : Recherches O(1) sur les données critiques
- **Compression** : Réponses compressées avec Flask-Compress
- **Gestion d'erreurs** : Système centralisé et robuste

### Frontend
- **Lazy loading** : Composants chargés à la demande
- **Debouncing** : Optimisation des recherches
- **Memoization** : Cache des calculs coûteux
- **Bundle splitting** : Réduction de la taille
- **Design glassmorphism** : Interface moderne et performante

## 🌍 Données et sources

### GTFS (General Transit Feed Specification)
- **Source** : Île-de-France Mobilités (IDFM)
- **Mise à jour** : Données quotidiennes
- **Couverture** : Métro, RER, Bus (filtrés métro/RER uniquement)
- **Format** : Standard international GTFS

### Données incluses
- **Routes** : 19 lignes (14 métro + 5 RER)
- **Stations** : ~540 stations et arrêts
- **Horaires** : Planning complet semaine/weekend
- **Correspondances** : Transferts physiques et temps de marche

### Structure des données GTFS
- **routes.txt** : Définition des lignes de transport
- **stops.txt** : Stations et arrêts avec coordonnées
- **trips.txt** : Voyages spécifiques sur les lignes
- **stop_times.txt** : Horaires détaillés de passage
- **transfers.txt** : Correspondances entre lignes
- **calendar.txt** : Calendrier de service

## 👥 Équipe et contributions

| Nom | Rôle | Contributions principales |
| --- | --- | --- |
| Laura Donato | Dev | Vérification automatique de la climatisation des stations sur un itinéraire, affichage des lignes et de l'ACPM, création et application des tests unitaires |
| Alexandre Borny | Scrum Master / Dev | Récupération des données des fichiers GTFS, création du graphe des stations, établissement d'un système de cache intelligent |
| Gabriel Langlois | Dev | Gestion de la carte interactive, ergonomie de l'interface utilisateur, calcul du CO2 émis par chaque trajet |
| Rémi Desjardins | Product Owner / Dev | Code d'algorithmes de graphes (Dijksa, Kruskal, parcours...) dans le back, calcul du meilleur itinéraire en prenant en compte les correspondances, gestion des endpoints API |

### Méthodologie de développement
- **Approche agile SCRUM** avec 5 phases de développement
- **82 tâches** décomposées et suivies via Jira
- **Sprints de 2 semaines** avec daily standups
- **Tests automatisés** et qualité continue
- **Documentation technique** complète

## 🤝 Contribuer

### Standards de code
- **Python** : PEP 8, docstrings, type hints
- **JavaScript** : ESLint, Prettier, Vue.js Style Guide
- **Tests** : Couverture minimale 80%
- **Commits** : Messages descriptifs en français
