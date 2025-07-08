# 📊 Audit de Performance et Impact Écologique - MetroCity

## 🎯 Objectif

Cet outil d'audit permet d'analyser en profondeur les performances de l'application MetroCity et d'évaluer son impact environnemental. Il mesure :

- ⏱️ **Temps d'exécution** des différentes opérations
- 💾 **Consommation mémoire** des algorithmes
- 🧮 **Complexité algorithmique** théorique et pratique
- ⚡ **Consommation énergétique** estimée
- 🌱 **Empreinte carbone** des calculs
- 📈 **Performance sous charge** avec tests de stress

## 🚀 Installation et Lancement

### Méthode Automatique (Recommandée)

```bash
# Rendre le script exécutable
chmod +x run_audit.sh

# Lancer l'audit complet
./run_audit.sh
```

Le script automatique va :
1. ✅ Vérifier les prérequis
2. 📦 Créer un environnement virtuel dédié
3. 📥 Installer les dépendances
4. 🚀 Démarrer le serveur backend si nécessaire
5. 🔬 Exécuter l'audit complet
6. 📄 Générer le rapport markdown

### Méthode Manuelle

```bash
# 1. Créer un environnement virtuel
python3 -m venv audit_venv
source audit_venv/bin/activate

# 2. Installer les dépendances
pip install -r requirements_audit.txt
pip install -r backend/requirements.txt

# 3. Démarrer le serveur backend
cd backend
python app.py &
cd ..

# 4. Exécuter l'audit
python audit_performance.py
```

### Test Rapide

Avant de lancer l'audit complet, vous pouvez tester que tout fonctionne :

```bash
python test_audit.py
```

## 📋 Prérequis

- **Python 3.8+**
- **Système Unix** (Linux/macOS) ou Windows avec WSL
- **8 GB RAM minimum** recommandé
- **Serveur backend MetroCity** accessible

### Dépendances Principales

- `psutil` - Monitoring système
- `numpy` - Calculs numériques
- `pandas` - Analyse de données
- `matplotlib` - Visualisations
- `requests` - Tests HTTP

## 🔍 Tests Réalisés

### 1. 📊 Chargement des Stations
- **Mesure :** Temps de parsing des données GTFS
- **Complexité :** O(n) linéaire
- **Métrique :** Secondes et MB de RAM

### 2. 🚇 Calculs d'Itinéraires Classiques
- **Algorithme :** Dijkstra optimisé
- **Tests :** 5 trajets représentatifs
- **Complexité :** O((V + E) log V)
- **Métrique :** Temps par trajet, distance calculée

### 3. ⏰ Calculs d'Itinéraires Temporels
- **Algorithme :** Multi-critères avec horaires GTFS
- **Tests :** 3 trajets avec contraintes horaires
- **Complexité :** O(P × S × T)
- **Métrique :** Temps total, temps d'attente

### 4. 🌳 ACPM (Arbre Couvrant de Poids Minimum)
- **Algorithme :** Kruskal avec Union-Find
- **Mesure :** Construction de l'arbre optimal
- **Complexité :** O(E log E)
- **Métrique :** Nombre d'arêtes traitées, poids total

### 5. 🔗 Analyse de Connexité
- **Algorithme :** DFS (Depth-First Search)
- **Mesure :** Vérification connexité du graphe
- **Complexité :** O(V + E)
- **Métrique :** Stations accessibles/inaccessibles

### 6. ⚡ Tests de Performance Globale
- **Test de charge :** 50 requêtes simultanées
- **Métriques :** Taux de succès, débit, latence
- **Analyse :** Comportement sous stress

## 📄 Résultats et Interprétation

### Fichiers Générés

1. **`AUDIT_PERFORMANCE_RAPPORT.md`** 📋
   - Rapport complet en markdown
   - Analyses détaillées et recommandations
   - Graphiques en mode texte

2. **`audit_performance_data.json`** 📊
   - Données brutes au format JSON
   - Exploitable par d'autres outils
   - Historique des métriques

### Métriques Clés

#### Temps d'Exécution ⏱️
- **< 0.1s** : Excellent
- **0.1-0.5s** : Bon
- **0.5-2.0s** : Acceptable
- **> 2.0s** : À optimiser

#### Consommation Mémoire 💾
- **< 50 MB** : Léger
- **50-200 MB** : Modéré
- **200-500 MB** : Élevé
- **> 500 MB** : Très élevé

#### Empreinte Carbone 🌱
- **< 1g CO₂** : Très faible
- **1-10g CO₂** : Faible
- **10-100g CO₂** : Modérée
- **> 100g CO₂** : Élevée

### Interprétation des Complexités

| Algorithme | Complexité | Performance | Commentaire |
|------------|------------|-------------|-------------|
| Chargement | O(n) | Optimale | Lecture séquentielle |
| Dijkstra | O((V+E) log V) | Optimale | Meilleur algo chemin court |
| Temporel | O(P×S×T) | Complexe | Multi-critères |
| Kruskal | O(E log E) | Optimale | MST optimal |
| DFS | O(V+E) | Optimale | Parcours optimal |

## 🛠️ Troubleshooting

### Erreurs Courantes

#### "ModuleNotFoundError"
```bash
# Solution : Installer les dépendances
pip install -r requirements_audit.txt
```

#### "Connection refused"
```bash
# Solution : Démarrer le serveur backend
cd backend && python app.py
```

#### "Permission denied"
```bash
# Solution : Rendre le script exécutable
chmod +x run_audit.sh
```

#### "Memory Error"
```bash
# Solution : Fermer les autres applications
# L'audit peut utiliser jusqu'à 1GB de RAM
```

### Optimisations Possibles

#### Si l'audit est lent :
1. Réduire le nombre de tests dans `test_stations`
2. Diminuer `concurrent_requests` dans les tests de charge
3. Utiliser `max_structural_paths = 5` au lieu de 10

#### Si la mémoire est insuffisante :
1. Fermer les autres applications
2. Utiliser un système avec plus de RAM
3. Modifier les paramètres de test

## 📈 Exploitation des Résultats

### Benchmark et Comparaisons

Les résultats peuvent être comparés :
- **Entre versions** de l'application
- **Entre environnements** (dev/prod)
- **Entre configurations** système
- **Avec d'autres projets** similaires

### Recommandations Types

L'audit génère automatiquement des recommandations :

#### Performance 🚀
- Cache intelligent pour les requêtes fréquentes
- Optimisation des algorithmes critiques
- Parallélisation des calculs

#### Mémoire 💾
- Optimisation des structures de données
- Garbage collection amélioré
- Streaming pour les gros datasets

#### Énergie 🌱
- Algorithmes moins gourmands
- Hébergement vert
- Optimisation des requêtes réseau

### Monitoring Continu

Pour un suivi régulier :

```bash
# Audit quotidien
crontab -e
# Ajouter : 0 2 * * * /path/to/run_audit.sh

# Audit avant déploiement
git hook pre-push
```

## 🔬 Méthodologie Scientifique

### Précision des Mesures

- **Temps :** Précision microseconde
- **Mémoire :** Monitoring en temps réel
- **Énergie :** Estimation basée CPU/RAM
- **Carbone :** Facteur France (57g CO₂/kWh)

### Limitations

1. **Énergie :** Estimation théorique, pas de mesure hardware
2. **Réseau :** Tests en local uniquement
3. **Données :** Basé sur dataset statique
4. **Système :** Résultats dépendants de la machine

### Reproductibilité

Pour des résultats reproductibles :
- Utiliser le même système d'exploitation
- Fermer les autres applications
- Exécuter plusieurs fois et moyenner
- Documenter l'environnement de test

## 📞 Support

### En cas de problème :

1. **Vérifier les logs** dans la console
2. **Consulter les prérequis** système
3. **Tester avec** `python test_audit.py`
4. **Consulter la documentation** backend

### Contribution

Pour améliorer l'audit :
- Ajouter de nouveaux tests
- Optimiser les algorithmes de mesure
- Améliorer la précision énergétique
- Étendre les métriques

---

*Développé par l'équipe MetroCity - Mastercamp 2025*  
*Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins* 