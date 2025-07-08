/*
 * MetroCity - Mastercamp 2025
 * Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
 * Fichier: useStationSwap.js
 * Description: Hook Vue pour l'inversion des stations de départ et d'arrivée
 */

/**
 * Hook pour gérer l'inversion des stations (départ ↔ arrivée)
 */
export function useStationSwap(stations, suggestions) {
  const {
    startStation,
    endStation,
    startStationId,
    endStationId,
    startStationSuggestions,
    endStationSuggestions
  } = stations;

  /**
   * Inverse les stations de départ et d'arrivée
   */
  function swapStations() {
    // Inverser les valeurs des stations
    const tmp = startStation.value;
    startStation.value = endStation.value;
    endStation.value = tmp;
    
    // Inverser les IDs des stations
    const tmpId = startStationId.value;
    startStationId.value = endStationId.value;
    endStationId.value = tmpId;
    
    // Inverser les suggestions
    const tmpSug = startStationSuggestions.value;
    startStationSuggestions.value = endStationSuggestions.value;
    endStationSuggestions.value = tmpSug;
  }

  return {
    swapStations
  };
} 