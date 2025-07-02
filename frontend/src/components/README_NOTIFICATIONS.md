# Système de Notifications Glassmorphism

Ce système de notifications offre une expérience utilisateur moderne avec des animations fluides et un design glassmorphism cohérent avec l'interface de l'application.

## Composants

### 1. ErrorNotification.vue
Affiche les erreurs avec un design rouge et des options avancées.

**Props :**
- `show` (Boolean) : Affiche/masque la notification
- `title` (String) : Titre de l'erreur (défaut: "Erreur")
- `message` (String) : Message d'erreur (requis)
- `details` (String) : Détails techniques optionnels
- `retryAction` (Function) : Fonction de retry optionnelle
- `autoClose` (Boolean) : Auto-fermeture (défaut: false)
- `autoCloseDelay` (Number) : Délai d'auto-fermeture en ms (défaut: 5000)

**Événements :**
- `@close` : Fermeture de la notification
- `@retry` : Action de retry

**Fonctionnalités :**
- Icône d'erreur animée avec effet de pulsation
- Section détails techniques pliable
- Bouton de retry conditionnel
- Barre de progression pour l'auto-fermeture
- Animations d'entrée/sortie fluides

### 2. SuccessNotification.vue
Affiche les succès avec un design vert.

**Props :**
- `show` (Boolean) : Affiche/masque la notification
- `title` (String) : Titre du succès (défaut: "Succès")
- `message` (String) : Message de succès (requis)
- `autoClose` (Boolean) : Auto-fermeture (défaut: true)
- `autoCloseDelay` (Number) : Délai d'auto-fermeture en ms (défaut: 3000)

**Événements :**
- `@close` : Fermeture de la notification

**Fonctionnalités :**
- Icône de succès animée avec effet de pulsation
- Auto-fermeture par défaut
- Barre de progression pour l'auto-fermeture
- Animations d'entrée/sortie fluides

### 3. LoadingNotification.vue
Affiche les états de chargement avec un design bleu.

**Props :**
- `show` (Boolean) : Affiche/masque la notification
- `title` (String) : Titre du chargement (défaut: "Chargement en cours")
- `message` (String) : Message de chargement (défaut: "Veuillez patienter...")
- `progress` (Number) : Pourcentage de progression (0-100)
- `currentStep` (Number) : Étape actuelle
- `totalSteps` (Number) : Nombre total d'étapes
- `canCancel` (Boolean) : Affiche le bouton d'annulation (défaut: false)

**Événements :**
- `@cancel` : Annulation du chargement

**Fonctionnalités :**
- Spinner animé avec 3 anneaux rotatifs
- Barre de progression avec effet de brillance
- Indicateur d'étapes
- Bouton d'annulation optionnel
- Animations d'entrée/sortie fluides

## Service de Notifications

### notificationService.js

Le service centralise la gestion des notifications avec des méthodes spécialisées :

#### Méthodes d'erreur :
- `showError(message, title, options)` : Erreur simple
- `showErrorWithDetails(message, details, title, options)` : Erreur avec détails
- `showErrorWithRetry(message, retryAction, title, options)` : Erreur avec retry
- `showNetworkError(retryAction)` : Erreur de réseau
- `showValidationError(message)` : Erreur de validation
- `showServerError(details)` : Erreur serveur
- `showPathNotFoundError()` : Chemin introuvable
- `showServiceUnavailableError(suggestedTime)` : Service indisponible

#### Méthodes de succès :
- `showSuccess(message, title, options)` : Succès simple
- `showPathFoundSuccess(duration, stationsCount)` : Itinéraire trouvé
- `showLoadSuccess(message)` : Chargement réussi
- `showSaveSuccess(message)` : Sauvegarde réussie

#### Méthodes utilitaires :
- `handleApiError(error, context)` : Gestion automatique des erreurs API
- `handleValidationError(field, message)` : Gestion des erreurs de validation
- `hideAll()` : Ferme toutes les notifications

## Utilisation

### Dans un composant Vue :

```javascript
import { notificationService } from '../services/notificationService'

// Afficher une erreur
notificationService.showError('Message d\'erreur')

// Afficher un succès
notificationService.showSuccess('Opération réussie')

// Gérer une erreur API
try {
  await api.call()
} catch (error) {
  notificationService.handleApiError(error, 'context')
}
```

### Dans le template :

```vue
<template>
  <ErrorNotification
    :show="errorState.show"
    :title="errorState.title"
    :message="errorState.message"
    :details="errorState.details"
    :retry-action="errorState.retryAction"
    :auto-close="errorState.autoClose"
    :auto-close-delay="errorState.autoCloseDelay"
    @close="notificationService.hideError()"
    @retry="notificationService.hideError()"
  />

  <SuccessNotification
    :show="successState.show"
    :title="successState.title"
    :message="successState.message"
    :auto-close="successState.autoClose"
    :auto-close-delay="successState.autoCloseDelay"
    @close="notificationService.hideSuccess()"
  />

  <LoadingNotification
    :show="loadingState.show"
    :title="loadingState.title"
    :message="loadingState.message"
    :progress="loadingState.progress"
    :current-step="loadingState.currentStep"
    :total-steps="loadingState.totalSteps"
    :can-cancel="loadingState.canCancel"
    @cancel="loadingState.show = false"
  />
</template>
```

## Design Glassmorphism

### Caractéristiques :
- **Fond translucide** avec `backdrop-filter: blur(20px)`
- **Bordures subtiles** avec `rgba(255, 255, 255, 0.3)`
- **Effets de brillance** avec des gradients
- **Ombres douces** pour la profondeur
- **Animations fluides** avec `cubic-bezier(0.25, 0.46, 0.45, 0.94)`

### Couleurs :
- **Erreurs** : Rouge (`#ff6b6b`, `#ee5a52`)
- **Succès** : Vert (`#4CAF50`, `#45a049`)
- **Chargement** : Bleu (`#2196F3`, `#1976D2`)

### Animations :
- **Entrée/Sortie** : Scale + translateY avec fade
- **Pulsation** : Scale sur les icônes
- **Rotation** : Spinner à 3 anneaux
- **Brillance** : Effet de shine sur les barres de progression

## Responsive

Tous les composants sont responsifs avec :
- Adaptation de la taille sur mobile
- Boutons pleine largeur sur petit écran
- Marges et paddings ajustés
- Texte redimensionné

## Accessibilité

- **Contraste** : Textes avec ombres pour la lisibilité
- **Focus** : États hover et focus visibles
- **Clavier** : Navigation au clavier supportée
- **Écrans de lecture** : Structure sémantique appropriée 