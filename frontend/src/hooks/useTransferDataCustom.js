/*
 * MetroCity - Mastercamp 2025
 * Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
 * Fichier: useTransferDataCustom.js
 * Description: Hook Vue pour la gestion des données de correspondance personnalisées
 */

/**
 * Hook pour gérer les données de correspondance personnalisées
 * Utilise les données transformées pathDetails avec transferInfo
 */
export function useTransferDataCustom({ pathDetails }) {
  
  /**
   * Détermine si une station est une correspondance
   * @param {number} segmentIndex - Index du segment
   * @param {number} stationIndex - Index de la station dans le segment
   * @returns {boolean} - True si c'est une correspondance
   */
  function isInterchange(segmentIndex, stationIndex) {
    if (!pathDetails.value || segmentIndex >= pathDetails.value.length) {
      return false;
    }
    
    const segment = pathDetails.value[segmentIndex];
    const station = segment.stations[stationIndex];
    
    // Une station est une correspondance si :
    // 1. C'est la dernière station du segment ET il y a un segment suivant avec transferInfo
    // 2. OU c'est la première station du segment ET ce segment a des transferInfo
    
    const isLastStationOfSegment = stationIndex === segment.stations.length - 1;
    const isFirstStationOfSegment = stationIndex === 0;
    
    // Cas 1: Dernière station du segment et il y a un transfert vers le segment suivant
    if (isLastStationOfSegment && segmentIndex < pathDetails.value.length - 1) {
      const nextSegment = pathDetails.value[segmentIndex + 1];
      if (nextSegment?.transferInfo !== null) {
        // Vérifier que la station correspond bien à la station de transfert
        return station === nextSegment.transferInfo.transferStation;
      }
    }
    
    // Cas 2: Première station du segment et ce segment a des transferInfo
    if (isFirstStationOfSegment && segment.transferInfo !== null) {
      // Vérifier que la station correspond bien à la station de transfert
      return station === segment.transferInfo.transferStation;
    }
    
    return false;
  }

  /**
   * Récupère le temps de transfert pour une correspondance
   * @param {number} segmentIndex - Index du segment
   * @returns {number|null} - Temps de transfert en secondes ou null
   */
  function getTransferTime(segmentIndex) {
    if (!pathDetails.value || segmentIndex >= pathDetails.value.length - 1) {
      return null;
    }
    
    // Le temps de transfert se trouve dans le segment suivant (qui commence par un changement de ligne)
    const nextSegment = pathDetails.value[segmentIndex + 1];
    return nextSegment?.transferInfo?.transfer_time || null;
  }

  /**
   * Récupère le temps d'attente pour une correspondance
   * @param {number} segmentIndex - Index du segment
   * @returns {number|null} - Temps d'attente en secondes ou null
   */
  function getWaitTime(segmentIndex) {
    if (!pathDetails.value || segmentIndex >= pathDetails.value.length) {
      return null;
    }
    
    // Le temps d'attente se trouve dans le segment actuel
    const segment = pathDetails.value[segmentIndex];
    return segment?.transferInfo?.wait_time || null;
  }

  /**
   * Calcule le temps total d'arrêt (transfert + attente) pour une correspondance
   * @param {number} segmentIndex - Index du segment
   * @returns {number|null} - Temps total en secondes ou null
   */
  function getTotalStopTime(segmentIndex) {
    // Pour une correspondance, on veut le temps total (transfert + attente) du segment suivant
    if (!pathDetails.value || segmentIndex >= pathDetails.value.length - 1) {
      return null;
    }
    
    const nextSegment = pathDetails.value[segmentIndex + 1];
    const transferTime = nextSegment?.transferInfo?.transfer_time || 0;
    const waitTime = nextSegment?.transferInfo?.wait_time || 0;
    
    if (transferTime === 0 && waitTime === 0) {
      return null;
    }
    
    return transferTime + waitTime;
  }

  /**
   * Calcule le pourcentage de progression pour l'indicateur de transfert
   * @param {number} segmentIndex - Index du segment
   * @returns {number} - Pourcentage de progression (0-100)
   */
  function getTransferProgress(segmentIndex) {
    const totalStopTime = getTotalStopTime(segmentIndex);
    if (!totalStopTime) return 0;
    
    // Calculer le pourcentage basé sur le temps total d'arrêt
    const maxExpectedTime = 600; // 10 minutes max
    return Math.min((totalStopTime / maxExpectedTime) * 100, 100);
  }

  /**
   * Détermine la couleur de l'indicateur de progression du transfert
   * @param {number} segmentIndex - Index du segment
   * @returns {string} - Couleur HEX
   */
  function getTransferProgressColor(segmentIndex) {
    const progress = getTransferProgress(segmentIndex);
    
    if (progress < 30) {
      return '#4CAF50'; // Vert pour les temps courts
    } else if (progress < 60) {
      return '#FF9800'; // Orange pour les temps moyens
    } else {
      return '#F44336'; // Rouge pour les temps longs
    }
  }

  /**
   * Génère le texte descriptif pour le temps de transfert
   * @param {number} segmentIndex - Index du segment
   * @returns {string} - Texte descriptif
   */
  function getTransferProgressText(segmentIndex) {
    const totalStopTime = getTotalStopTime(segmentIndex);
    if (!totalStopTime) return '';
    
    if (totalStopTime < 120) {
      return 'Rapide';
    } else if (totalStopTime < 300) {
      return 'Normal';
    } else {
      return 'Long';
    }
  }

  return {
    isInterchange,
    getTransferTime,
    getWaitTime,
    getTotalStopTime,
    getTransferProgress,
    getTransferProgressColor,
    getTransferProgressText
  };
} 