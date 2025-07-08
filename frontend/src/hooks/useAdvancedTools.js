/*
 * MetroCity - Mastercamp 2025
 * Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
 * Fichier: useAdvancedTools.js
 * Description: Hook Vue pour les outils avancés (ACPM, connexité, affichage des lignes)
 */

import { ref } from 'vue'
import { api } from '../services/api'
import { LINE_COLORS } from '../constants/metro'

export function useAdvancedTools(notificationService) {
  // États ACPM
  const showACPM = ref(false)
  const acpmPath = ref([])
  const acpmTotalWeight = ref(null)

  // États des lignes
  const showLines = ref(false)
  const linesPolylines = ref([])

  // États de connexité
  const connexityResult = ref(null)
  const showConnexityModal = ref(false)

  // État de chargement global
  const loadingState = ref({
    show: false,
    title: 'Chargement en cours',
    message: 'Veuillez patienter...',
    progress: 0,
    currentStep: null,
    totalSteps: null,
    canCancel: false
  })

  // Fonction pour basculer l'ACPM
  async function toggleACPM() {
    if (showACPM.value) {
      showACPM.value = false;
      acpmPath.value = [];
      acpmTotalWeight.value = null;
    } else {
      try {
        const response = await api.getACPM();
        if (response && response.status === 'success') {
          showACPM.value = true;
          acpmTotalWeight.value = response.total_weight || 0;
          
          // Transformer les données ACPM en polylines pour la carte
          const acpmEdges = response.acpm_edges || [];
          // Traitement des arêtes ACPM
          
          // Récupérer les stations pour les positions
          const stationsData = await api.getStationsList();
          const stationsMap = {};
          stationsData.stations.forEach(station => {
            if (station.ids && station.ids.length > 0) {
              station.ids.forEach(id => {
                stationsMap[id] = station;
              });
            }
          });
          
          // Créer les polylines ACPM
          const acpmPolylines = [];
          acpmEdges.forEach((edge) => {
            const fromStation = stationsMap[edge.from.id];
            const toStation = stationsMap[edge.to.id];
            
            if (fromStation && toStation && fromStation.position && toStation.position) {
              // Convertir les positions en coordonnées Leaflet [lat, lng]
              const fromLatLng = [fromStation.position[1], fromStation.position[0]];
              const toLatLng = [toStation.position[1], toStation.position[0]];
              
              acpmPolylines.push({
                path: [fromLatLng, toLatLng],
                color: '#000000', // Noir pour l'ACPM
                weight: 4,
                opacity: 0.8
              });
            } else {
              // Station manquante pour l'arête ACPM
            }
          });
          
          acpmPath.value = acpmPolylines;
          // Polylines ACPM créées
          notificationService.showSuccess('ACPM calculé avec succès');
        } else {
          notificationService.showError('Erreur lors du calcul de l\'ACPM');
        }
      } catch (error) {
        // Erreur lors du calcul de l'ACPM
        notificationService.showError('Erreur lors du calcul de l\'ACPM');
      }
    }
  }

  // Fonction pour basculer les lignes
  async function toggleLines() {
    if (showLines.value) {
      showLines.value = false;
      linesPolylines.value = [];
    } else {
      try {
        const response = await api.getLines();
        if (response && response.status === 'success') {
          showLines.value = true;
          
          // Transformer les données des lignes en polylines pour la carte
          const linesData = response.lines || {};
          // Traitement des données des lignes
          
          // Récupérer les stations pour les positions
          const stationsData = await api.getStationsList();
          const stationsMap = {};
          stationsData.stations.forEach(station => {
            stationsMap[station.name] = station;
          });
          
          // Créer les polylines pour chaque ligne
          const linePolylines = [];
          
          Object.entries(linesData).forEach(([lineNumber, branches]) => {
            const lineColor = LINE_COLORS[lineNumber] || '#1976d2';
            
            // Chaque ligne peut avoir plusieurs branches
            branches.forEach((branch) => {
              if (branch && branch.length >= 2) {
                const pathCoordinates = [];
                
                // Parcourir toutes les stations de cette branche
                branch.forEach(stationData => {
                  const stationName = stationData.name;
                  const station = stationsMap[stationName];
                  
                  if (station && station.position && station.position.length === 2) {
                    // Convertir en coordonnées Leaflet [lat, lng]
                    const latLng = [station.position[1], station.position[0]];
                    pathCoordinates.push(latLng);
                  } else {
                    // Station non trouvée pour cette ligne
                  }
                });
                
                if (pathCoordinates.length >= 2) {
                  linePolylines.push({
                    line: lineNumber,
                    path: pathCoordinates,
                    color: lineColor,
                    weight: 6,
                    opacity: 0.85
                  });
                }
              }
            });
          });
          
          linesPolylines.value = linePolylines;
          // Polylines des lignes créées
          notificationService.showSuccess('Lignes affichées');
        } else {
          notificationService.showError('Erreur lors du chargement des lignes');
        }
      } catch (error) {
        // Erreur lors du chargement des lignes
        notificationService.showError('Erreur lors du chargement des lignes');
      }
    }
  }

  // Fonction pour tester la connexité
  async function testConnexity(startStation) {
    try {
      loadingState.value = {
        show: true,
        title: 'Test de connexité',
        message: 'Analyse de la connectivité du réseau...',
        progress: 0,
        currentStep: null,
        totalSteps: null,
        canCancel: false
      }
      
      const url = startStation 
        ? `/connexity?station=${encodeURIComponent(startStation)}`
        : '/connexity'
      connexityResult.value = await api.get(url)
      showConnexityModal.value = true
    } catch (error) {
      // Erreur lors du test de connexité
      notificationService.handleApiError(error, 'testConnexity')
      connexityResult.value = { error: error.message }
      showConnexityModal.value = true
    } finally {
      loadingState.value.show = false
    }
  }

  // Fonction pour fermer la modal de connexité
  function closeConnexityModal() {
    showConnexityModal.value = false;
    connexityResult.value = null;
  }

  // Fonction pour effacer tous les outils
  function clearAllTools() {
    // Effacer l'ACPM
    showACPM.value = false;
    acpmPath.value = [];
    acpmTotalWeight.value = null;
    
    // Effacer les lignes
    showLines.value = false;
    linesPolylines.value = [];
    
    // Effacer la connexité
    connexityResult.value = null;
    showConnexityModal.value = false;
    
    notificationService.showSuccess('Affichage effacé');
  }

  return {
    showACPM,
    acpmPath,
    acpmTotalWeight,
    showLines,
    linesPolylines,
    connexityResult,
    showConnexityModal,
    loadingState,
    toggleACPM,
    toggleLines,
    testConnexity,
    closeConnexityModal,
    clearAllTools,
    LINE_COLORS
  }
} 