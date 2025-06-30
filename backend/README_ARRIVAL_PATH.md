# Itinéraire avec Horaire d'Arrivée - Documentation

## Vue d'ensemble

Cette nouvelle fonctionnalité permet de calculer un itinéraire optimal en partant de l'heure d'arrivée souhaitée plutôt que de l'heure de départ. Elle utilise une logique rétrograde pour déterminer le meilleur moment de départ pour arriver à l'heure demandée.

## Fonctionnalités

### 🎯 Objectif principal
- Calculer un itinéraire qui arrive le plus proche possible de l'heure d'arrivée souhaitée
- Optimiser le moment de départ pour minimiser l'écart avec l'heure d'arrivée demandée
- Réutiliser la logique temporelle existante en l'inversant

### 🔄 Logique rétrograde
1. **Inversion du chemin** : Le chemin structurel est parcouru de la fin vers le début
2. **Calcul des départs** : Pour chaque segment, on détermine le dernier départ possible qui permet d'arriver à l'heure souhaitée
3. **Optimisation** : Le système choisit l'itinéraire qui arrive le plus proche de l'heure demandée

## API Endpoint

### POST `/temporal/path-arrival`

Calcule un itinéraire optimal en partant de l'heure d'arrivée souhaitée.

#### Paramètres d'entrée (JSON)

```json
{
    "start_station": "Châtelet",
    "end_station": "Bastille",
    "arrival_time": "09:00",
    "date": "2024-01-15",        // optionnel (date actuelle par défaut)
    "max_wait_time": 1800        // optionnel (30 minutes par défaut)
}
```

#### Réponse

```json
{
    "departure_time": "08:45",
    "arrival_time": "09:02",
    "total_duration": 1020,
    "total_wait_time": 300,
    "segments": [
        {
            "from_station": "Châtelet",
            "to_station": "Bastille",
            "line": "1",
            "departure_time": "08:45",
            "arrival_time": "09:02",
            "wait_time": 300,
            "travel_time": 720,
            "transfer_time": 0
        }
    ],
    "arrival_info": {
        "requested_arrival_time": "09:00",
        "actual_arrival_time": "09:02",
        "arrival_difference_minutes": 2,
        "departure_time": "08:45"
    }
}
```

#### Informations spécifiques à l'arrivée

Le champ `arrival_info` contient des informations détaillées sur la précision de l'arrivée :

- `requested_arrival_time` : Heure d'arrivée demandée
- `actual_arrival_time` : Heure d'arrivée réelle calculée
- `arrival_difference_minutes` : Écart en minutes (positif = en retard, négatif = en avance)
- `departure_time` : Heure de départ calculée

## Implémentation technique

### Services modifiés

#### `TemporalPathService`

Nouvelles méthodes ajoutées :

1. **`find_optimal_temporal_path_with_arrival_time()`**
   - Point d'entrée principal pour la logique rétrograde
   - Évalue plusieurs chemins structurels en sens inverse
   - Optimise pour minimiser l'écart avec l'heure d'arrivée souhaitée

2. **`_evaluate_temporal_path_reverse()`**
   - Évalue un chemin structurel en partant de la fin
   - Inverse la logique de calcul des horaires
   - Gère les correspondances dans le sens inverse

3. **`_get_last_departure_for_arrival()`**
   - Trouve le dernier départ possible pour arriver à une heure donnée
   - Utilise les données GTFS réelles pour des calculs précis

### Logique de scoring

Le système utilise un score pondéré qui prend en compte :

1. **Écart d'arrivée** : Différence absolue avec l'heure d'arrivée souhaitée
2. **Pénalité des correspondances** : Temps de transfert + temps d'attente
3. **Durée totale** : Temps total du trajet

### Optimisations

- **Cache GTFS** : Réutilisation du cache existant pour les horaires
- **Calculs inversés** : Optimisation des calculs de temps de trajet en sens inverse
- **Validation des horaires** : Vérification de la disponibilité du service

## Tests

### Scripts de test disponibles

1. **`test_arrival_path.py`** : Test direct de la fonctionnalité
2. **`tests/test_arrival_path.py`** : Tests unitaires complets
3. **`example_arrival_api.py`** : Exemples d'utilisation de l'API

### Exécution des tests

```bash
# Test direct
cd backend
python test_arrival_path.py

# Tests unitaires
python -m pytest tests/test_arrival_path.py -v

# Test API (serveur doit être démarré)
python example_arrival_api.py
```

## Comparaison avec l'itinéraire normal

| Aspect | Itinéraire normal | Itinéraire avec arrivée |
|--------|-------------------|-------------------------|
| **Point de départ** | Heure de départ | Heure d'arrivée |
| **Optimisation** | Durée totale minimale | Précision d'arrivée maximale |
| **Logique** | Forward (avant → arrière) | Backward (arrière → avant) |
| **Cas d'usage** | "Je veux partir à 8h" | "Je dois arriver à 9h" |

## Cas d'usage typiques

1. **Rendez-vous professionnel** : "Je dois être à la réunion à 14h"
2. **Transport aérien** : "Mon avion décolle à 10h, je dois arriver à 8h"
3. **Événement culturel** : "Le spectacle commence à 20h"
4. **Rendez-vous médical** : "Mon RDV est à 15h30"

## Limitations

1. **Horaires de service** : Dépend des horaires réels du métro
2. **Précision** : L'arrivée exacte dépend de la fréquence des trains
3. **Complexité** : Calculs plus complexes que l'itinéraire normal
4. **Performance** : Légèrement plus lent que l'itinéraire normal

## Évolutions futures

- [ ] Support des correspondances avec d'autres modes de transport
- [ ] Prise en compte des perturbations en temps réel
- [ ] Optimisation multi-critères (prix, CO2, confort)
- [ ] Interface utilisateur dédiée dans le frontend

## Support

Pour toute question ou problème avec cette fonctionnalité, consultez :
- Les logs du serveur pour les erreurs techniques
- Les tests unitaires pour les exemples d'utilisation
- La documentation de l'API pour les détails d'implémentation 