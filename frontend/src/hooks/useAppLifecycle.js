/*
 * MetroCity - Mastercamp 2025
 * Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
 * Fichier: useAppLifecycle.js
 * Description: Hook Vue pour la gestion du cycle de vie de l'application
 */

import { onMounted } from 'vue'

/**
 * Hook pour gérer le cycle de vie de l'application
 */
export function useAppLifecycle(loadStations) {
  
  /**
   * Initialise l'application au montage du composant
   */
  function initializeApp() {
    // Force le rendu initial et un redimensionnement après le montage
    setTimeout(() => {
      window.dispatchEvent(new Event('resize'));
    }, 100);
    
    // Charger les stations
    loadStations();
  }

  /**
   * Force un redimensionnement de la fenêtre
   * Utile pour les composants comme Leaflet qui ont besoin d'un refresh
   */
  function forceResize() {
    window.dispatchEvent(new Event('resize'));
  }

  // Configuration du cycle de vie
  onMounted(() => {
    initializeApp();
  });

  return {
    initializeApp,
    forceResize
  };
} 