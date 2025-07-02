import { ref } from 'vue'

// État global des notifications
const errorNotification = ref({
  show: false,
  title: '',
  message: '',
  details: null,
  retryAction: null,
  autoClose: false,
  autoCloseDelay: 5000
})

const successNotification = ref({
  show: false,
  title: '',
  message: '',
  autoClose: true,
  autoCloseDelay: 3000
})

// Service de gestion des erreurs
export const errorService = {
  // Afficher une erreur simple
  showError(message, title = 'Erreur', options = {}) {
    errorNotification.value = {
      show: true,
      title,
      message,
      details: null,
      retryAction: null,
      autoClose: false,
      autoCloseDelay: 5000,
      ...options
    }
  },

  // Afficher une erreur avec détails techniques
  showErrorWithDetails(message, details, title = 'Erreur technique', options = {}) {
    errorNotification.value = {
      show: true,
      title,
      message,
      details: typeof details === 'string' ? details : JSON.stringify(details, null, 2),
      retryAction: null,
      autoClose: false,
      autoCloseDelay: 5000,
      ...options
    }
  },

  // Afficher une erreur avec action de retry
  showErrorWithRetry(message, retryAction, title = 'Erreur', options = {}) {
    errorNotification.value = {
      show: true,
      title,
      message,
      details: null,
      retryAction,
      autoClose: false,
      autoCloseDelay: 5000,
      ...options
    }
  },

  // Afficher une erreur de réseau
  showNetworkError(retryAction = null) {
    this.showErrorWithRetry(
      'Impossible de se connecter au serveur. Vérifiez votre connexion internet.',
      retryAction,
      'Erreur de connexion',
      { autoClose: true, autoCloseDelay: 8000 }
    )
  },

  // Afficher une erreur de validation
  showValidationError(message) {
    this.showError(
      message,
      'Données invalides',
      { autoClose: true, autoCloseDelay: 4000 }
    )
  },

  // Afficher une erreur de serveur
  showServerError(details = null) {
    if (details) {
      this.showErrorWithDetails(
        'Le serveur a rencontré une erreur interne.',
        details,
        'Erreur serveur'
      )
    } else {
      this.showError(
        'Le serveur a rencontré une erreur interne. Veuillez réessayer plus tard.',
        'Erreur serveur',
        { autoClose: true, autoCloseDelay: 6000 }
      )
    }
  },

  // Afficher une erreur de chemin non trouvé
  showPathNotFoundError() {
    this.showError(
      'Aucun itinéraire trouvé entre les stations sélectionnées.',
      'Itinéraire introuvable',
      { autoClose: true, autoCloseDelay: 5000 }
    )
  },

  // Afficher une erreur de service indisponible
  showServiceUnavailableError(suggestedTime = null) {
    let message = 'Ce service n\'est pas disponible actuellement.'
    if (suggestedTime) {
      message += `\n\nVoulez-vous rechercher un itinéraire pour ${suggestedTime} ?`
    }
    
    this.showError(
      message,
      'Service indisponible',
      { autoClose: false }
    )
  },

  // Fermer l'erreur
  hideError() {
    errorNotification.value.show = false
  },

  // Obtenir l'état de l'erreur
  getErrorState() {
    return errorNotification
  }
}

// Service de gestion des succès
export const successService = {
  // Afficher un succès simple
  showSuccess(message, title = 'Succès', options = {}) {
    successNotification.value = {
      show: true,
      title,
      message,
      autoClose: true,
      autoCloseDelay: 3000,
      ...options
    }
  },

  // Afficher un succès de recherche d'itinéraire
  showPathFoundSuccess(duration, stationsCount, ms = null) {
    let msg = `Itinéraire trouvé en ${duration} avec ${stationsCount} stations.`;
    if (ms !== null && ms !== undefined) {
      msg += ` (calcul: ${ms} ms)`;
    }
    this.showSuccess(
      msg,
      'Itinéraire calculé'
    )
  },

  // Afficher un succès de chargement
  showLoadSuccess(message = 'Données chargées avec succès.') {
    this.showSuccess(message, 'Chargement réussi')
  },

  // Afficher un succès de sauvegarde
  showSaveSuccess(message = 'Données sauvegardées avec succès.') {
    this.showSuccess(message, 'Sauvegarde réussie')
  },

  // Fermer le succès
  hideSuccess() {
    successNotification.value.show = false
  },

  // Obtenir l'état du succès
  getSuccessState() {
    return successNotification
  }
}

// Service principal de notifications
export const notificationService = {
  // Méthodes d'erreur
  ...errorService,
  
  // Méthodes de succès
  ...successService,

  // Fermer toutes les notifications
  hideAll() {
    this.hideError()
    this.hideSuccess()
  },

  // Gérer automatiquement les erreurs d'API
  handleApiError(error, context = '') {
    console.error(`API Error in ${context}:`, error)
    
    if (error.responseData) {
      // Erreur avec données de réponse
      const { error: errorMessage, service_info } = error.responseData
      
      if (service_info) {
        // Erreur de service avec suggestions
        this.showServiceUnavailableError(service_info.suggested_departure)
        return
      }
      
      if (errorMessage) {
        this.showError(errorMessage, 'Erreur API')
        return
      }
    }
    
    // Erreur réseau ou générique
    if (error.message.includes('fetch') || error.message.includes('network')) {
      this.showNetworkError()
    } else {
      this.showError(error.message || 'Une erreur inattendue s\'est produite.')
    }
  },

  // Gérer les erreurs de validation
  handleValidationError(field, message) {
    this.showValidationError(`${field}: ${message}`)
  }
}

export default notificationService 