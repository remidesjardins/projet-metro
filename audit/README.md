# 📊 Dossier Audit - MetroCity

Ce dossier contient tous les outils et documents liés à l'audit de performance et d'impact environnemental du système MetroCity.

## 📁 Contenu du dossier

### 🔧 Scripts d'audit
- **`audit_performance.py`** - Script principal d'audit complet avec monitoring énergétique
- **`demo_audit.py`** - Version de démonstration simplifiée de l'audit
- **`test_audit.py`** - Tests unitaires pour valider les fonctions d'audit
- **`run_audit.sh`** - Script shell pour lancer l'audit automatiquement

### 📋 Documentation
- **`README_AUDIT.md`** - Guide détaillé d'utilisation des outils d'audit
- **`AUDIT_PERFORMANCE_RAPPORT.md`** - Rapport généré automatiquement par l'audit

### ⚙️ Configuration
- **`requirements_audit.txt`** - Dépendances Python nécessaires pour l'audit

## 🚀 Utilisation rapide

### Installation des dépendances
```bash
cd audit
pip install -r requirements_audit.txt
```

### Lancement de l'audit complet
```bash
cd audit
python audit_performance.py
```

### Lancement avec le script shell (depuis la racine ou n'importe où)
```bash
./audit/run_audit.sh
```

## 📊 Métriques collectées

L'audit collecte et analyse les métriques suivantes :

### ⏱️ Performances temporelles
- Temps de chargement des stations
- Temps de calcul d'itinéraires classiques (Dijkstra)
- Temps de calcul d'itinéraires temporels
- Temps de calcul de l'ACPM (Kruskal)
- Temps d'analyse de connexité (DFS)

### 💾 Utilisation mémoire
- Pic de mémoire pour chaque opération
- Mémoire moyenne utilisée
- Analyse de la consommation mémoire

### ⚡ Impact environnemental
- Consommation énergétique en joules
- Empreinte carbone en grammes CO₂
- Projections annuelles d'impact
- Équivalences (km voiture, arbres nécessaires)

### 🔍 Complexité algorithmique
- Analyse de la complexité temporelle
- Comparaison des algorithmes
- Recommandations d'optimisation

### 📈 Tests de charge
- Tests avec utilisateurs concurrents
- Débit de requêtes par seconde
- Taux de succès des opérations

## 📋 Résumé des performances

Le rapport généré inclut un résumé complet avec :

1. **Temps de chargement des stations** - Complexité O(n)
2. **Calcul d'itinéraire classique** - Complexité O((V+E) log V)
3. **Calcul d'itinéraire temporel** - Complexité O(P×S×T)
4. **Calcul de l'ACPM** - Complexité O(E log E)
5. **Analyse de connexité** - Complexité O(V+E)
6. **Consommation énergétique** par fonctionnalité
7. **Métriques de performance** globales

## 🔧 Configuration

### Variables d'environnement
- `BACKEND_URL` - URL du backend (défaut: http://localhost:5000)
- `AUDIT_OUTPUT_DIR` - Dossier de sortie des rapports

### Paramètres d'audit
- Nombre d'itinéraires testés
- Créneaux horaires pour les tests temporels
- Nombre d'utilisateurs concurrents
- Durée des tests de charge

## 📊 Interprétation des résultats

### Seuils de performance
- **Excellent** : < 0.1s pour les opérations simples
- **Bon** : 0.1-0.5s pour les calculs d'itinéraires
- **Acceptable** : 0.5-1.0s pour les opérations complexes
- **À optimiser** : > 1.0s

### Impact environnemental
- **Faible** : < 1g CO₂ par opération
- **Modéré** : 1-10g CO₂ par opération
- **Élevé** : > 10g CO₂ par opération

## 🛠️ Dépannage

### Problèmes courants
1. **Backend non accessible** - Vérifier que le serveur backend est démarré
2. **Erreurs de dépendances** - Réinstaller les requirements
3. **Mémoire insuffisante** - Réduire le nombre de tests simultanés
4. **Timeout des requêtes** - Augmenter les timeouts dans la configuration

### Logs et débogage
- Les logs détaillés sont affichés dans la console
- Le rapport markdown contient toutes les métriques
- Les erreurs sont capturées et rapportées

## 📞 Support

Pour toute question ou problème avec l'audit :
1. Consulter les logs d'erreur
2. Vérifier la configuration
3. Tester avec un nombre réduit d'opérations
4. Consulter la documentation du backend 