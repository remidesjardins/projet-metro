# Tests de Connexité - Documentation

## Vue d'ensemble

Ce document décrit les tests mis en place pour vérifier le bon fonctionnement de la fonctionnalité de connexité du graphe du métro de Paris.

## Fonctionnalité testée

La connexité vérifie si toutes les stations du réseau de métro sont accessibles depuis n'importe quelle autre station. Un graphe est dit "connexe" si on peut aller de n'importe quelle station à n'importe quelle autre station.

## Tests implémentés

### 1. Tests unitaires (`test_connexite_service.py`)

**Classe `TestConnexiteChecker`** :

- `test_initialization()` : Vérifie l'initialisation correcte du checker
- `test_dfs_algorithm()` : Teste l'algorithme DFS (Depth-First Search)
- `test_is_connected()` : Vérifie la méthode de test de connexité générale
- `test_get_unreachable_stations()` : Teste la récupération des stations inaccessibles
- `test_check_connexity_from_station_valid()` : Teste la connexité depuis une station spécifique
- `test_check_connexity_from_station_invalid()` : Teste la gestion d'erreur avec une station inexistante
- `test_connexity_consistency()` : Vérifie la cohérence entre les différentes méthodes
- `test_visited_stations_consistency()` : Vérifie la cohérence des stations visitées
- `test_performance()` : Teste les performances de l'algorithme

**Fonction utilitaire** :
- `test_connexite_function()` : Teste la fonction utilitaire `test_connexite()`

### 2. Tests d'intégration (`test_routes.py`)

**`test_get_connexity()`** :

- **Test 1** : Vérification de la connexité générale
  - Structure de la réponse
  - Types de données
  - Cohérence des compteurs
  - Gestion des stations inaccessibles

- **Test 2** : Vérification depuis une station spécifique
  - Test avec une station valide
  - Vérification de la cohérence avec le test général

- **Test 3** : Gestion d'erreur
  - Test avec une station inexistante
  - Vérification du code d'erreur 500

- **Test 4** : Performance
  - Vérification que la réponse arrive en moins de 5 secondes

- **Test 5** : Cohérence des données
  - Vérification que le nombre de stations correspond au graphe

### 3. Test manuel (`test_connexity_manual.py`)

Script de test manuel qui affiche des résultats détaillés :
- Chargement des données
- Test de connexité générale
- Test depuis une station spécifique
- Vérification de la cohérence
- Test de performance
- Test de la fonction utilitaire

## Résultats attendus

### Pour un graphe connexe (cas normal) :
```json
{
    "is_connected": true,
    "reachable_stations": 543,
    "total_stations": 543,
    "unreachable_count": 0,
    "unreachable_stations": []
}
```

### Pour un graphe non connexe (cas d'erreur) :
```json
{
    "is_connected": false,
    "reachable_stations": 500,
    "total_stations": 543,
    "unreachable_count": 43,
    "unreachable_stations": [
        {
            "id": "station_id",
            "name": "Nom de la station",
            "line": "ligne"
        }
    ]
}
```

## Performance attendue

- **Temps d'exécution** : < 1 seconde pour les tests unitaires
- **Temps de réponse API** : < 5 secondes
- **Mémoire** : Utilisation raisonnable (pas de fuite mémoire)

## Exécution des tests

### Tests unitaires uniquement :
```bash
python -m pytest tests/test_connexite_service.py -v
```

### Test d'intégration uniquement :
```bash
python -m pytest tests/test_routes.py::test_get_connexity -v
```

### Tous les tests :
```bash
python -m pytest tests/ -v
```

### Test manuel :
```bash
python test_connexity_manual.py
```

### Test via l'API :
```bash
# Test général
curl http://localhost:5050/connexity

# Test depuis une station spécifique
curl "http://localhost:5050/connexity?station=Campo-Formio"
```

## Validation des résultats

### Critères de succès :
1. ✅ Tous les tests unitaires passent
2. ✅ Le test d'intégration passe
3. ✅ Le test manuel s'exécute sans erreur
4. ✅ L'API retourne des résultats cohérents
5. ✅ Les performances sont acceptables
6. ✅ La gestion d'erreur fonctionne correctement

### Résultats actuels (2024) :
- **Graphe connexe** : ✅ OUI
- **Stations totales** : 543
- **Stations accessibles** : 543
- **Stations inaccessibles** : 0
- **Performance** : Excellent (< 0.001s)
- **Tests** : 55/55 passés

## Maintenance

### Ajout de nouveaux tests :
1. Ajouter les tests unitaires dans `test_connexite_service.py`
2. Ajouter les tests d'intégration dans `test_routes.py`
3. Mettre à jour cette documentation
4. Vérifier que tous les tests passent

### Mise à jour des données :
Si les données GTFS changent, les tests continueront de fonctionner car ils vérifient la logique, pas les valeurs absolues.

## Dépannage

### Problèmes courants :
1. **Station non trouvée** : Vérifier l'encodage des caractères accentués
2. **Performance lente** : Vérifier le cache des données
3. **Tests qui échouent** : Vérifier que les données sont chargées correctement

### Logs utiles :
- Vérifier les logs de chargement des données
- Vérifier les temps d'exécution
- Vérifier la cohérence des compteurs 