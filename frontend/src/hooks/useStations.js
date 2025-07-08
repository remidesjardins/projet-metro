/*
 * MetroCity - Mastercamp 2025
 * Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
 * Fichier: useStations.js
 * Description: Hook Vue pour la gestion des stations (recherche, sélection, suggestions)
 */

import { ref, computed } from 'vue'
import { api } from '../services/api'
import { notificationService } from '../services/notificationService'

export function useStations() {
  const allStations = ref([])
  const stationLinesMap = ref({})
  const startStation = ref('')
  const endStation = ref('')
  const startStationId = ref('')
  const endStationId = ref('')
  const startStationSuggestions = ref([])
  const endStationSuggestions = ref([])
  let startStationDebounce = null
  let endStationDebounce = null

  async function loadStations() {
    try {
      const res = await api.getStationsList()
      allStations.value = res.stations
        .map(station => {
          let id = undefined;
          if (station.ids && station.ids.length > 0) id = station.ids[0];
          else if (station.id) id = station.id;
          if (!id) {
            // Station sans id ignorée
          }
          return id ? { ...station, id } : null;
        })
        .filter(station => station !== null);
      stationLinesMap.value = Object.fromEntries(
        allStations.value.map(s => [s.name, s.lines])
      )
      // Stations chargées avec succès
      notificationService.showLoadSuccess(`${allStations.value.length} stations chargées avec succès`)
    } catch (e) {
      // Erreur lors du chargement des stations
      notificationService.handleApiError(e, 'loadStations')
      allStations.value = []
      stationLinesMap.value = {}
    }
  }

  function handleStartStationInput() {
    // Gestion de la saisie de station de départ
    if (startStationDebounce) {
      clearTimeout(startStationDebounce)
    }
    startStationDebounce = setTimeout(() => {
      if (startStation.value.length < 2) {
        startStationSuggestions.value = [];
        return;
      }
      const searchTerm = startStation.value.toLowerCase();
      const filtered = allStations.value.filter(station => 
        station.name.toLowerCase().includes(searchTerm)
      )
      startStationSuggestions.value = filtered
        .slice(0, 5)
        .map(station => station.name);
    }, 300);
  }

  function handleEndStationInput() {
    if (endStationDebounce) {
      clearTimeout(endStationDebounce)
    }
    endStationDebounce = setTimeout(() => {
      if (endStation.value.length < 2) {
        endStationSuggestions.value = [];
        return;
      }
      const searchTerm = endStation.value.toLowerCase();
      endStationSuggestions.value = allStations.value
        .filter(station => station.name.toLowerCase().includes(searchTerm))
        .slice(0, 5)
        .map(station => station.name);
    }, 300);
  }

  function selectStartStation(stationName) {
    startStation.value = stationName;
    startStationSuggestions.value = [];
    const stationObj = allStations.value.find(s => s.name === stationName);
    if (stationObj) {
      startStationId.value = stationObj.ids && stationObj.ids.length > 0 ? stationObj.ids[0] : stationObj.id;
    }
  }

  function selectEndStation(stationName) {
    endStation.value = stationName;
    endStationSuggestions.value = [];
    const stationObj = allStations.value.find(s => s.name === stationName);
    if (stationObj) {
      endStationId.value = stationObj.ids && stationObj.ids.length > 0 ? stationObj.ids[0] : stationObj.id;
    }
  }

  function selectStationFromMap(station) {
    const stationId = station.ids && station.ids.length > 0 ? station.ids[0] : station.id;
    if (!startStation.value) {
      startStation.value = station.name;
      startStationId.value = stationId;
    } else if (!endStation.value && stationId !== startStationId.value) {
      endStation.value = station.name;
      endStationId.value = stationId;
    } else {
      startStation.value = station.name;
      startStationId.value = stationId;
      endStation.value = '';
      endStationId.value = '';
    }
  }

  function clearResults() {
    startStation.value = '';
    endStation.value = '';
    startStationId.value = '';
    endStationId.value = '';
    startStationSuggestions.value = [];
    endStationSuggestions.value = [];
  }

  return {
    allStations,
    stationLinesMap,
    startStation,
    endStation,
    startStationId,
    endStationId,
    startStationSuggestions,
    endStationSuggestions,
    loadStations,
    handleStartStationInput,
    handleEndStationInput,
    selectStartStation,
    selectEndStation,
    selectStationFromMap,
    clearResults
  }
} 