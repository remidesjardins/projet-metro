# 🚇 Audit de Performance & Impact Écologique - MetroCity
_Date de l'audit : 2025-07-08T18:38:51.671898_

## 🖥️ Informations Système
- **platform** : posix.uname_result(sysname='Darwin', nodename='MacBook-Air-de-Remi-3.local', release='24.5.0', version='Darwin Kernel Version 24.5.0: Tue Apr 22 19:54:33 PDT 2025; root:xnu-11417.121.6~2/RELEASE_ARM64_T8122', machine='arm64')
- **python_version** : 3.13.5 (main, Jun 11 2025, 15:36:57) [Clang 17.0.0 (clang-1700.0.13.3)]
- **cpu_count** : 8
- **memory_total** : 17179869184
- **disk_usage** : 494384795648
- **python_executable** : /Users/remidesjardins/WebstormProjects/projet-metro/audit_venv/bin/python3

## 🚦 Chargement des stations
- Temps de chargement : 0.000s
- Mémoire pic : 0.0MB
- Empreinte carbone : 0.000g CO₂

## 🚇 Itinéraires classiques (simulation réaliste)
- Nombre de tests : 33
- Temps moyen : 0.004s
- Temps médian : 0.004s
- P95 : 0.007s
- Longueur moyenne des routes : 12.4
- Distribution : {'short_routes': 0, 'medium_routes': 14, 'long_routes': 19}
- Mémoire pic max : 0.1MB

## 🕘 Itinéraires temporels (simulation réaliste)
- Nombre de tests : 120
- Temps moyen : 0.202s
- Taux de succès global : 91.7%
  - heure_pointe_matin : 0.502s sur 20 tests
  - heure_pointe_soir : 0.125s sur 20 tests
  - heure_creuse_midi : 0.128s sur 20 tests
  - heure_creuse_soir : 0.096s sur 20 tests
  - weekend_matin : 0.235s sur 20 tests
  - weekend_soir : 0.129s sur 20 tests

## 👥 Tests de charge (utilisateurs concurrents)
- 10_users : 10/10 succès, temps moyen 0.013s, débit 611.8 req/s
- 25_users : 25/25 succès, temps moyen 0.019s, débit 679.3 req/s
- 50_users : 50/50 succès, temps moyen 0.026s, débit 686.4 req/s
- 100_users : 100/100 succès, temps moyen 0.024s, débit 740.0 req/s

## 🌱 Impact environnemental
- Énergie totale : 687.76 J
- Carbone total : 0.01 g CO₂
- Énergie moyenne par requête : 4.495 J
- Estimation carbone/jour : 38.52 g CO₂

## 💡 Recommandations
- ⏰ **Taux de succès temporel faible**: 91.7%. Améliorer la robustesse du service temporel.
- 🌱 **Impact carbone significatif**: Estimation 38.5g CO₂/jour. Optimiser les algorithmes pour réduire la consommation.
- ⚡ **Consommation énergétique élevée**: 4.50J par requête. Implémenter des stratégies de mise en cache.
- 🚀 **Scalabilité**: Implémenter un load balancer pour distribuer la charge.
- 📊 **Monitoring**: Ajouter des métriques temps réel (Prometheus/Grafana).
- 🔄 **Cache distribué**: Utiliser Redis pour partager les caches entre instances.
- ⚡ **Optimisations**: Considérer l'utilisation de WebSockets pour les mises à jour temps réel.
- 🛡️ **Robustesse**: Implémenter des circuit breakers pour les services externes.

## 📊 RÉSUMÉ COMPLET DES PERFORMANCES
### ⏱️ Temps de chargement des stations
- **Temps moyen** : 0.000 secondes
- **Complexité** : O(n) où n=543 stations
- **Mémoire utilisée** : 0.0 MB
- **Consommation énergétique** : 4.28 J
- **Empreinte carbone** : 0.000 g CO₂

### 🗺️ Calcul d'itinéraire classique (Dijkstra)
### 🕘 Calcul d'itinéraire temporel
### 🌳 Calcul de l'ACPM (Kruskal)
- **Temps de calcul** : 0.003 secondes
- **Complexité** : O(E log E) où E=662 arêtes
- **Mémoire utilisée** : 0.2 MB
- **Consommation énergétique** : 0.69 J
- **Empreinte carbone** : 0.000 g CO₂

### 🔗 Analyse de connexité (DFS)
- **Temps de calcul** : 0.003 secondes
- **Complexité** : O(V + E) où V=543, E=662
- **Mémoire utilisée** : 0.0 MB
- **Consommation énergétique** : 0.70 J
- **Empreinte carbone** : 0.000 g CO₂

### ⚡ Consommation énergétique par fonctionnalité
### 🌍 Impact environnemental global
### 📈 Métriques de performance globales
- **Requêtes simultanées testées** : 50
- **Taux de succès** : 100.0%
- **Temps de réponse moyen** : 0.042 secondes
- **Débit** : 200.2 requêtes/seconde
- **Temps total de test** : 0.25 secondes

### 🔍 Analyse de complexité algorithmique
| Algorithme | Complexité | Description |
|------------|------------|-------------|
| Chargement stations | O(n) | n = nombre de stations |
| Dijkstra (classique) | O((V+E) log V) | V=sommets, E=arêtes |
| Routage temporel | O(P×S×T) | P=chemins, S=segments, T=horaires |
| Kruskal (ACPM) | O(E log E) | E = nombre d'arêtes |
| DFS (connexité) | O(V+E) | V=sommets, E=arêtes |

---
_Rapport généré automatiquement par l'audit MetroCity._
