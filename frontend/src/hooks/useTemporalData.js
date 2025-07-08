/*
 * MetroCity - Mastercamp 2025
 * Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
 * Fichier: useTemporalData.js
 * Description: Hook Vue pour la gestion des données temporelles des itinéraires
 */

import { computed } from 'vue'

export function useTemporalData() {
  
  // Fonctions pour les temps de transfert et d'attente
  function getTransferTime(segmentIndex, temporalData) {
    if (!temporalData?.segments || segmentIndex >= temporalData.segments.length - 1) {
      return null;
    }
    
    const currentSegment = temporalData.segments[segmentIndex];
    const nextSegment = temporalData.segments[segmentIndex + 1];
    
    // Vérifier si c'est un vrai changement de ligne
    if (currentSegment.line === nextSegment.line) {
      return null; // Pas de correspondance si même ligne
    }
    
    return currentSegment.transfer_time || 0;
  }

  function getWaitTime(segmentIndex, temporalData) {
    if (!temporalData?.segments || segmentIndex >= temporalData.segments.length) {
      return null;
    }
    
    const segment = temporalData.segments[segmentIndex];
    return segment.wait_time || 0;
  }

  function getTotalStopTime(segmentIndex, temporalData) {
    const transferTime = getTransferTime(segmentIndex, temporalData);
    const waitTime = getWaitTime(segmentIndex + 1, temporalData);
    
    if (transferTime === null && waitTime === null) {
      return null;
    }
    
    return (transferTime || 0) + (waitTime || 0);
  }

  function getTransferProgress(segmentIndex, temporalData) {
    const totalStopTime = getTotalStopTime(segmentIndex, temporalData);
    if (!totalStopTime) return 0;
    
    // Calculer le pourcentage basé sur le temps total d'arrêt
    // Plus le temps est long, plus le pourcentage est élevé (max 100%)
    const maxExpectedTime = 600; // 10 minutes max
    return Math.min((totalStopTime / maxExpectedTime) * 100, 100);
  }

  function getTransferProgressColor(segmentIndex, temporalData) {
    const progress = getTransferProgress(segmentIndex, temporalData);
    
    if (progress < 30) {
      return '#4CAF50'; // Vert pour les temps courts
    } else if (progress < 60) {
      return '#FF9800'; // Orange pour les temps moyens
    } else {
      return '#F44336'; // Rouge pour les temps longs
    }
  }

  function getTransferProgressText(segmentIndex, temporalData) {
    const totalStopTime = getTotalStopTime(segmentIndex, temporalData);
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
    getTransferTime,
    getWaitTime,
    getTotalStopTime,
    getTransferProgress,
    getTransferProgressColor,
    getTransferProgressText
  }
} 