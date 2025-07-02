# Intégration des RER dans le projet Métro

## 🚆 Vue d'ensemble

Ce document décrit l'intégration des lignes RER (A, B, C, D, E) dans le système de calcul d'itinéraires du métro parisien.

## 📋 Modifications apportées

### 1. Backend - Services GTFS

#### `services/gtfs_temporal.py`
- **Modification** : Filtrage des routes pour inclure les RER
- **Avant** : `route_type == 1` (métro uniquement)
- **Après** : `route_type == 1 OR route_type == 2` (métro + RER)
- **Lignes ajoutées** : A, B, C, D, E

```python
# Filtrer pour le métro parisien ET les RER
metro_routes = routes_df[
    (routes_df['route_type'] == 1) & 
    (routes_df['route_short_name'].isin([str(i) for i in range(1, 15)] + ['3B', '7B']))
]

# Ajouter les lignes RER (route_type 2 pour les trains de banlieue)
rer_routes = routes_df[
    (routes_df['route_type'] == 2) & 
    (routes_df['route_short_name'].isin(['A', 'B', 'C', 'D', 'E']))
]

# Combiner métro et RER
all_routes = pd.concat([metro_routes, rer_routes], ignore_index=True)
```

#### `utils/gtfs_parser.py`
- **Modification** : Constante `PARIS_METRO_LINES` étendue
- **Avant** : `[str(i) for i in range(1, 15)] + ['3B', '7B']`
- **Après** : `[str(i) for i in range(1, 15)] + ['3B', '7B'] + ['A', 'B', 'C', 'D', 'E']`

```python
# Lignes de métro parisien ET RER
PARIS_METRO_LINES = [str(i) for i in range(1, 15)] + ['3B', '7B'] + ['A', 'B', 'C', 'D', 'E']
```

- **Modification** : Filtrage des routes pour inclure `route_type == 2`

### 2. Frontend - Affichage

#### `views/HomeView.vue`
- **Ajout** : Couleurs des lignes RER dans `LINE_COLORS`

```javascript
const LINE_COLORS = {
  // ... lignes de métro existantes ...
  'A': '#EB2132',  // Rouge - RER A
  'B': '#5091CB',  // Bleu - RER B
  'C': '#FFCC30',  // Jaune - RER C
  'D': '#008B5B',  // Vert - RER D
  'E': '#B94E9A'   // Violet - RER E
}
```

## 🛠️ Installation et configuration

### 1. Effacer le cache existant

```bash
cd backend
python reload_with_rer.py
```

### 2. Tester l'intégration

```bash
cd backend
python test_rer_integration.py
```

### 3. Redémarrer le serveur

```bash
cd backend
python app.py
```

## 🧪 Tests et validation

### Script de test automatique

Le script `test_rer_integration.py` vérifie :

1. **Chargement des données** : Vérifie que les RER sont inclus dans les données
2. **Service GTFS** : Confirme que les routes RER sont disponibles
3. **Recherche de chemins** : Teste des itinéraires utilisant des RER

### Tests manuels recommandés

1. **Recherche d'itinéraires** :
   - Châtelet → Gare du Nord (RER B)
   - Châtelet → Gare de Lyon (RER A)
   - Gare du Nord → Gare de Lyon (RER B + RER A)

2. **Affichage sur la carte** :
   - Vérifier que les lignes RER s'affichent avec les bonnes couleurs
   - Tester l'affichage des polylines pour les RER

3. **Calculs temporels** :
   - Tester les itinéraires temporels avec des RER
   - Vérifier les correspondances entre métro et RER

## 📊 Impact sur les performances

### Données supplémentaires
- **Routes** : +5 lignes RER
- **Stations** : +~200 stations RER
- **Connexions** : +~400 connexions RER

### Optimisations maintenues
- Cache intelligent des données GTFS
- Filtrage par chunks pour `stop_times.txt`
- Index optimisés pour les recherches

## 🔧 Dépannage

### Problèmes courants

1. **RER non trouvés dans les données**
   - Vérifier que les fichiers GTFS contiennent les données RER
   - S'assurer que `route_type == 2` est présent dans `routes.txt`

2. **Cache non mis à jour**
   - Exécuter `python reload_with_rer.py`
   - Vérifier que le dossier `data/cache` est vide

3. **Erreurs de parsing**
   - Vérifier les logs dans la console
   - S'assurer que les données GTFS sont valides

### Logs utiles

```bash
# Vérifier les routes chargées
grep "Routes filtrées" backend/logs/app.log

# Vérifier les stations par ligne
grep "Ligne.*stations" backend/logs/app.log
```

## 🎯 Fonctionnalités disponibles

### Calculs d'itinéraires
- ✅ Plus court chemin avec RER
- ✅ Itinéraires multiples avec RER
- ✅ Optimisation des correspondances métro-RER

### Affichage
- ✅ Polylines colorées pour les RER
- ✅ Stations RER sur la carte
- ✅ Correspondances métro-RER

### Calculs temporels
- ✅ Horaires RER intégrés
- ✅ Correspondances temporelles métro-RER
- ✅ Itinéraires avec heure d'arrivée incluant RER

## 🚀 Prochaines améliorations possibles

1. **Optimisations spécifiques RER**
   - Temps de correspondance adaptés aux RER
   - Gestion des branches RER (A1, A2, etc.)

2. **Interface utilisateur**
   - Filtres par type de transport (métro/RER)
   - Préférences utilisateur pour les RER

3. **Données temps réel**
   - Intégration des perturbations RER
   - Temps d'attente en temps réel

---

**✅ Intégration terminée** : Les RER sont maintenant pleinement intégrés dans le système de calcul d'itinéraires. 