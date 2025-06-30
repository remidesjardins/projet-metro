<script setup>
import MetroMapLeaflet from '../components/MetroMapLeaflet.vue'
import ServerStatus from '../components/ServerStatus.vue'
import { ref, provide, onMounted, computed, watch } from 'vue'
import { api } from '../services/api'

const pathDetails = ref([])
const pathLength = ref({
  duration: null,
  emissions: null,
  stationsCount: null
})
const startStation = ref('')
const endStation = ref('')
const startStationId = ref('')
const endStationId = ref('')
const startStationSuggestions = ref([])
const endStationSuggestions = ref([])
const connexityResult = ref(null)
const isLoading = ref(false)
const allStations = ref([])
const stationLinesMap = ref({})
const showConnexityModal = ref(false)

// Mode de recherche (classique ou temporel)
const searchMode = ref('classic') // 'classic' ou 'temporal'
const temporalData = ref(null) // Données temporelles

// Paramètres temporels
const departureTime = ref('08:30')
const departureDate = ref('2024-03-15')
// Ajout : type d'heure (départ/arrivée)
const timeType = ref('departure') // 'departure' ou 'arrival'

// Debouncing pour les suggestions
const startStationDebounce = ref(null)
const endStationDebounce = ref(null)

// Variables pour les outils avancés
const showACPM = ref(false)
const acpmPath = ref([])
const acpmTotalWeight = ref(null)
const showLines = ref(false)
const linesPolylines = ref([])

// Mapping des couleurs pour les lignes de métro avec saturation augmentée pour meilleur contraste
const LINE_COLORS = {
  '1': '#FFCE00',  // Jaune - ligne 1
  '2': '#0064B0',  // Bleu foncé - ligne 2
  '3': '#9F9825',  // Marron - ligne 3
  '3bis': '#98D4E2',  // Bleu clair - ligne 3bis
  '3B': '#6EC4E8',    // Bleu - ligne 3B
  '4': '#C902A0',  // Rose foncé - ligne 4
  '5': '#F28E42',  // Orange - ligne 5
  '6': '#6EC68D',  // Vert - ligne 6
  '7': '#FA9EBA',  // Rose - ligne 7
  '7bis': '#84C0D4',  // Bleu ciel - ligne 7bis
  '7B': '#6ECA97',    // Vert d'eau - ligne 7B
  '8': '#C5A3CA',  // Violet clair - ligne 8
  '9': '#CEC92B',  // Vert olive - ligne 9
  '10': '#E4B327',  // Orange foncé - ligne 10
  '11': '#8D5E2A',  // Marron clair - ligne 11
  '12': '#007E52',  // Vert foncé - ligne 12
  '13': '#73C0E9',  // Bleu clair - ligne 13
  '14': '#662483'   // Violet - ligne 14
}

// Fournir ces valeurs aux composants enfants
provide('pathDetails', pathDetails)
provide('pathLength', pathLength)
provide('showACPM', showACPM)
provide('acpmPath', acpmPath)
provide('showLines', showLines)
provide('linesPolylines', linesPolylines)
provide('selectStationFromMap', selectStationFromMap)

// Détecte si la station courante est une correspondance de changement de ligne
function isInterchange(segmentIndex, stationIndex) {
  if (
    segmentIndex < pathDetails.value.length - 1 &&
    stationIndex === pathDetails.value[segmentIndex].stations.length - 1
  ) {
    // Vérifier si les lignes sont différentes
    const currentLine = pathDetails.value[segmentIndex].line;
    const nextLine = pathDetails.value[segmentIndex + 1].line;
    return currentLine !== nextLine;
  }
  return false;
}

// Calcule le nombre réel de correspondances (changements de ligne)
function getTransferCount() {
  if (!pathDetails.value || pathDetails.value.length === 0) return 0;
  
  // Compter les segments qui ont des informations de transfert
  return pathDetails.value.filter(segment => segment.transferInfo).length;
}

function formatTime(pathLengthObj) {
    const seconds = pathLengthObj?.duration || pathLengthObj || 0;
    
    if (!seconds || isNaN(seconds)) {
        return '0 min';
    }

    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    
    if (minutes === 0) {
        return `${remainingSeconds}s`;
    } else if (remainingSeconds === 0) {
        return `${minutes}min`;
    } else {
        return `${minutes}min ${remainingSeconds}s`;
    }
}

function formatTimeDisplay(timeStr) {
    if (!timeStr) return '';
    // Supprimer les secondes si elles sont à 00
    return timeStr.replace(':00', '');
}

function formatACPMTime(totalWeight) {
    if (!totalWeight || isNaN(totalWeight)) {
        return '00:00';
    }
    
    // Convertir le poids total en temps (supposant que le poids représente des secondes)
    const totalMinutes = Math.floor(totalWeight / 60);
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;
    
    // Formater au format hh:mm
    const formattedHours = hours.toString().padStart(2, '0');
    const formattedMinutes = minutes.toString().padStart(2, '0');
    
    return `${formattedHours}:${formattedMinutes}`;
}

// Fonctions pour les temps de transfert et d'attente
function getTransferTime(segmentIndex) {
  if (!temporalData.value?.segments || segmentIndex >= temporalData.value.segments.length - 1) {
    return null;
  }
  
  const currentSegment = temporalData.value.segments[segmentIndex];
  const nextSegment = temporalData.value.segments[segmentIndex + 1];
  
  // Vérifier si c'est un vrai changement de ligne
  if (currentSegment.line === nextSegment.line) {
    return null; // Pas de correspondance si même ligne
  }
  
  return currentSegment.transfer_time || 0;
}

function getWaitTime(segmentIndex) {
  if (!temporalData.value?.segments || segmentIndex >= temporalData.value.segments.length) {
    return null;
  }
  
  const segment = temporalData.value.segments[segmentIndex];
  return segment.wait_time || 0;
}

function getTotalStopTime(segmentIndex) {
  const transferTime = getTransferTime(segmentIndex);
  const waitTime = getWaitTime(segmentIndex + 1);
  
  if (transferTime === null && waitTime === null) {
    return null;
  }
  
  return (transferTime || 0) + (waitTime || 0);
}

function getTransferProgress(segmentIndex) {
  const totalStopTime = getTotalStopTime(segmentIndex);
  if (!totalStopTime) return 0;
  
  // Calculer le pourcentage basé sur le temps total d'arrêt
  // Plus le temps est long, plus le pourcentage est élevé (max 100%)
  const maxExpectedTime = 600; // 10 minutes max
  return Math.min((totalStopTime / maxExpectedTime) * 100, 100);
}

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

function getTotalStations() {
  // Utiliser d'abord pathLength.stationsCount si disponible
  if (pathLength.value?.stationsCount) {
    return pathLength.value.stationsCount;
  }
  
  // Fallback sur l'ancien calcul si pathLength.stationsCount n'est pas disponible
  if (!pathDetails.value || pathDetails.value.length === 0) return 0;

  const allStations = pathDetails.value.flatMap(segment => segment.stations);
  const uniqueStations = [...new Set(allStations)];
  return uniqueStations.length;
}

// Forcer un redimensionnement une fois que le composant est monté
onMounted(() => {
  // Force le rendu initial et un redimensionnement après le montage
  setTimeout(() => {
    window.dispatchEvent(new Event('resize'));
  }, 100);
})

onMounted(async () => {
  try {
    // console.log('Chargement des stations...')
    const res = await api.getStationsList()
    // console.log('Résultat API:', res)
    allStations.value = res.stations
    // console.log('Stations chargées:', allStations.value.length)
    // Création d'une map nom -> lignes
    stationLinesMap.value = Object.fromEntries(
      res.stations.map(s => [s.name, s.lines])
    )
    // console.log('Map des lignes créée:', Object.keys(stationLinesMap.value).length)
  } catch (e) {
    console.error('Erreur lors du chargement des stations:', e)
    allStations.value = []
    stationLinesMap.value = {}
  }
})

function handleStartStationInput() {
  // console.log('handleStartStationInput appelé avec:', startStation.value)
  // console.log('allStations disponibles:', allStations.value.length)
  
  // Annuler le debounce précédent
  if (startStationDebounce.value) {
    clearTimeout(startStationDebounce.value)
  }
  
  // Débouncer la recherche
  startStationDebounce.value = setTimeout(() => {
    if (startStation.value.length < 2) {
      startStationSuggestions.value = [];
      // console.log('Texte trop court, suggestions vidées')
      return;
    }

    const searchTerm = startStation.value.toLowerCase();
    // console.log('Recherche pour:', searchTerm)
    
    const filtered = allStations.value.filter(station => 
      station.name.toLowerCase().includes(searchTerm)
    )
    // console.log('Stations filtrées:', filtered.length)
    
    startStationSuggestions.value = filtered
      .slice(0, 5)
      .map(station => station.name);
    
    // console.log('Suggestions finales:', startStationSuggestions.value)
  }, 300); // 300ms de délai
}

function handleEndStationInput() {
  // Annuler le debounce précédent
  if (endStationDebounce.value) {
    clearTimeout(endStationDebounce.value)
  }
  
  // Débouncer la recherche
  endStationDebounce.value = setTimeout(() => {
    if (endStation.value.length < 2) {
      endStationSuggestions.value = [];
      return;
    }

    const searchTerm = endStation.value.toLowerCase();
    endStationSuggestions.value = allStations.value
      .filter(station => station.name.toLowerCase().includes(searchTerm))
      .slice(0, 5)
      .map(station => station.name);
  }, 300); // 300ms de délai
}

function selectStartStation(stationName) {
  startStation.value = stationName;
  startStationSuggestions.value = [];
  
  // Trouver l'ID de la station
  const stationObj = allStations.value.find(s => s.name === stationName);
  if (stationObj) {
    // L'API retourne un tableau d'IDs, prendre le premier
    startStationId.value = stationObj.ids && stationObj.ids.length > 0 ? stationObj.ids[0] : stationObj.id;
    // console.log('Station de départ sélectionnée:', stationName, 'ID:', startStationId.value, 'Station obj:', stationObj);
  }
}

function selectEndStation(stationName) {
  endStation.value = stationName;
  endStationSuggestions.value = [];
  
  // Trouver l'ID de la station
  const stationObj = allStations.value.find(s => s.name === stationName);
  if (stationObj) {
    // L'API retourne un tableau d'IDs, prendre le premier
    endStationId.value = stationObj.ids && stationObj.ids.length > 0 ? stationObj.ids[0] : stationObj.id;
    // console.log('Station d\'arrivée sélectionnée:', stationName, 'ID:', endStationId.value, 'Station obj:', stationObj);
  }
}

// Fonction pour sélectionner une station depuis la carte
function selectStationFromMap(station) {
  // Pour les stations de la carte, utiliser le bon format d'ID
  const stationId = station.ids && station.ids.length > 0 ? station.ids[0] : station.id;
  
  if (!startStation.value) {
    // Sélectionner comme station de départ
    startStation.value = station.name;
    startStationId.value = stationId;
    // console.log('Station de départ sélectionnée depuis la carte:', station.name, 'ID:', stationId);
  } else if (!endStation.value && stationId !== startStationId.value) {
    // Sélectionner comme station d'arrivée
    endStation.value = station.name;
    endStationId.value = stationId;
    // console.log('Station d\'arrivée sélectionnée depuis la carte:', station.name, 'ID:', stationId);
  } else {
    // Redémarrer la sélection
    startStation.value = station.name;
    startStationId.value = stationId;
    endStation.value = '';
    endStationId.value = '';
    // console.log('Nouvelle sélection depuis la carte:', station.name, 'ID:', stationId);
  }
}

function clearResults() {
  pathDetails.value = [];
  pathLength.value = { duration: null, emissions: null, stationsCount: null };
  temporalData.value = null;
  startStationSuggestions.value = [];
  endStationSuggestions.value = [];
}

// Fonctions pour les outils avancés
async function toggleACPM() {
  console.log('toggleACPM appelé, showACPM actuel:', showACPM.value)
  showACPM.value = !showACPM.value
  console.log('showACPM changé à:', showACPM.value)
  if (showACPM.value) {
    console.log('Chargement de l\'ACPM...')
    await fetchACPM()
  } else {
    console.log('Masquage de l\'ACPM')
    acpmPath.value = []
  }
}

async function fetchACPM() {
  try {
    const data = await api.get('/acpm')
    acpmTotalWeight.value = data.total_weight
    
    // Traiter les données ACPM pour l'affichage sur la carte
    console.log('Données ACPM chargées:', data)
    
    // Charger les stations pour pouvoir traiter l'ACPM
    const stationsData = await api.getStationsList()
    const stations = stationsData.stations.filter(s => s.position && Array.isArray(s.position) && s.position.length === 2)
      .map(station => {
        const line = Array.isArray(station.lines) && station.lines.length > 0
          ? station.lines[0]
          : station.lines
        return {
          id: station.ids && station.ids.length > 0 ? station.ids[0] : station.id,
          name: station.name,
          lines: station.lines,
          position: station.position
        }
      })

    // Traiter les arêtes de l'ACPM
    acpmPath.value = data.mst.map(edge => {
      const fromStation = stations.find(s => s.id === edge.from.id)
      const toStation = stations.find(s => s.id === edge.to.id)
      
      if (fromStation && toStation && fromStation.position && toStation.position) {
        return {
          path: [
            [fromStation.position[0] / 1000, fromStation.position[1] / 1000],
            [toStation.position[0] / 1000, toStation.position[1] / 1000]
          ],
          color: '#000000', // Noir pour ACPM
          weight: 4,
          opacity: 0.8
        }
      }
      return null
    }).filter(Boolean)
    
    console.log('Chemins ACPM traités:', acpmPath.value.length)
  } catch (error) {
    console.error('Erreur lors du chargement de l\'ACPM:', error)
  }
}

async function toggleLines() {
  showLines.value = !showLines.value
  // console.log('Affichage des lignes:', showLines.value ? 'activé' : 'désactivé')
  
  if (showLines.value) {
    // console.log('Chargement des données de lignes en cours...')
    await fetchLines()
  } else {
    // console.log('Masquage des lignes')
    linesPolylines.value = []
  }
}

async function fetchLines() {
  try {
    console.log('Chargement des lignes depuis l\'API...')
    const data = await api.get('/stations/ordered_by_line')
    console.log('Données de lignes reçues:', data)
    
    // Traiter les données de lignes
    // data est un objet avec des clés de lignes (ex: "1", "2", etc.) et des valeurs qui sont des tableaux de branches
    linesPolylines.value = []
    
    Object.entries(data).forEach(([line, branches]) => {
      console.log(`Traitement de la ligne ${line} avec ${branches.length} branches`)
      
      // Traiter chaque branche de la ligne
      branches.forEach((branch, branchIndex) => {
        if (!branch || branch.length < 2) {
          console.log(`Branche ${branchIndex} de la ligne ${line} ignorée (pas assez de stations)`)
          return
        }
        
        const path = branch.map(station => {
          if (station.position && Array.isArray(station.position) && station.position.length === 2) {
            return [station.position[0] / 1000, station.position[1] / 1000]
          }
          console.log(`Station sans position valide:`, station)
          return null
        }).filter(Boolean)
        
        if (path.length < 2) {
          console.log(`Branche ${branchIndex} de la ligne ${line} ignorée (pas assez de positions valides)`)
          return
        }
        
        const polyline = {
          line: line,
          path: path,
          color: darkenColor(LINE_COLORS[line] || '#1976d2', 0.7), // Couleur plus foncée
          opacity: 1 // Opacité maximale
        }
        
        linesPolylines.value.push(polyline)
        console.log(`Branche ${branchIndex} de la ligne ${line} ajoutée avec ${path.length} points`)
      })
    })
    
    console.log('Lignes traitées:', linesPolylines.value.length, 'polylines créées')
    console.log('Détail des polylines:', linesPolylines.value)
  } catch (error) {
    console.error('Erreur lors du chargement des lignes:', error)
  }
}

function clearPath() {
  pathDetails.value = []
  pathLength.value = { duration: null, emissions: null, stationsCount: null }
  temporalData.value = null
  // console.log('Chemin effacé')
}

function validateTimeInput() {
  const timePattern = /^([0-2]?[0-9]|3[0-1]):([0-5][0-9])$/;
  
  if (!timePattern.test(departureTime.value)) {
    alert('Format d\'heure invalide. Utilisez HH:MM (ex: 08:30, 24:30 pour 00:30 du lendemain)');
    return false;
  }
  
  const [hours, minutes] = departureTime.value.split(':').map(Number);
  
  // Valider les heures (0-31 pour permettre les heures après minuit)
  if (hours < 0 || hours > 31) {
    alert('Heures invalides. Utilisez 0-23 pour le jour même, 24-31 pour le lendemain');
    return false;
  }
  
  // Valider les minutes (0-59)
  if (minutes < 0 || minutes > 59) {
    alert('Minutes invalides. Utilisez 0-59');
    return false;
  }
  
  console.log('Heure validée:', departureTime.value);
  return true;
}

async function findPath() {
  if (!startStation.value || !endStation.value) {
    alert('Veuillez sélectionner une station de départ et d\'arrivée');
    return;
  }

  isLoading.value = true;
  pathDetails.value = [];
  pathLength.value = { duration: null, emissions: null, stationsCount: null };
  temporalData.value = null;

  try {
    if (searchMode.value === 'temporal') {
      // Recherche temporelle
      let response;
      if (timeType.value === 'departure') {
        response = await api.post('/temporal/path', {
          start_station: startStation.value,
          end_station: endStation.value,
          departure_time: departureTime.value,
          date: departureDate.value,
          max_paths: 3,
          max_wait_time: 1800
        });
      } else {
        response = await api.post('/temporal/path-arrival', {
          start_station: startStation.value,
          end_station: endStation.value,
          arrival_time: departureTime.value,
          date: departureDate.value,
          max_paths: 3,
          max_wait_time: 1800
        });
      }
      temporalData.value = response;
      
      // OPTIMISATION : Traitement simplifié des données
      if (response.segments && response.segments.length > 0) {
        // S'assurer que temporalData.value contient les segments bruts pour les fonctions getTransferTime/getWaitTime
        temporalData.value = {
          ...response,
          segments: response.segments // Conserver les segments bruts
        };
        
        // Regrouper les segments par ligne pour créer des segments continus
        const segments = [];
        let currentLine = null;
        let currentStations = [];
        let currentDuration = 0;
        let currentStationTimes = {};
        let currentTransferInfo = null;
        let firstSegmentOfLine = null;
        let lastSegmentOfLine = null;
        
        // Utiliser le chemin structurel depuis la réponse API pour obtenir toutes les stations
        const structuralPath = response.structural_path || [];
        
        for (let i = 0; i < response.segments.length; i++) {
          const segment = response.segments[i];
          
          if (currentLine === null) {
            // Premier segment
            currentLine = segment.line;
            firstSegmentOfLine = segment;
            lastSegmentOfLine = segment;
            // Récupérer toutes les stations de cette ligne depuis le chemin structurel
            currentStations = getStationsForLine(structuralPath, segment.line, segment.from_station, segment.to_station);
            
            // Créer les horaires pour toutes les stations de ce segment
            currentStationTimes = createStationTimesForSegment(currentStations, segment);
            
          } else if (segment.line === currentLine) {
            // Même ligne, ajouter les stations intermédiaires
            const additionalStations = getStationsForLine(structuralPath, segment.line, segment.from_station, segment.to_station);
            
            // Fusionner les stations en évitant les doublons
            additionalStations.forEach(station => {
              if (!currentStations.includes(station)) {
                currentStations.push(station);
              }
            });
            
            // Mettre à jour le dernier segment de cette ligne
            lastSegmentOfLine = segment;
            
            // Mettre à jour les horaires pour les nouvelles stations
            currentStationTimes = updateStationTimes(currentStationTimes, segment);
            
          } else {
            // Changement de ligne, finaliser le segment précédent
            // Calculer la durée réelle basée sur les horaires
            if (firstSegmentOfLine && lastSegmentOfLine) {
              const departureTime = new Date(`2000-01-01T${firstSegmentOfLine.departure_time}`);
              const arrivalTime = new Date(`2000-01-01T${lastSegmentOfLine.arrival_time}`);
              currentDuration = Math.round((arrivalTime - departureTime) / 1000); // en secondes
            }
            
            segments.push({
              line: currentLine,
              stations: currentStations,
              duration: currentDuration,
              stationsCount: currentStations.length,
              stationTimes: currentStationTimes,
              transferInfo: currentTransferInfo
            });
            
            // Commencer un nouveau segment avec les informations de transfert
            currentLine = segment.line;
            firstSegmentOfLine = segment;
            lastSegmentOfLine = segment;
            currentStations = getStationsForLine(structuralPath, segment.line, segment.from_station, segment.to_station);
            currentTransferInfo = {
              transferTime: segment.transfer_time,
              waitTime: segment.wait_time,
              transferStation: segment.from_station,
              fromLine: segments[segments.length - 1]?.line,
              toLine: segment.line
            };
            
            // Créer les horaires pour le nouveau segment
            currentStationTimes = createStationTimesForSegment(currentStations, segment);
          }
        }
        
        // Ajouter le dernier segment
        if (currentStations.length > 0) {
          // Calculer la durée réelle pour le dernier segment
          if (firstSegmentOfLine && lastSegmentOfLine) {
            const departureTime = new Date(`2000-01-01T${firstSegmentOfLine.departure_time}`);
            const arrivalTime = new Date(`2000-01-01T${lastSegmentOfLine.arrival_time}`);
            currentDuration = Math.round((arrivalTime - departureTime) / 1000); // en secondes
          }
          
          segments.push({
            line: currentLine,
            stations: currentStations,
            duration: currentDuration,
            stationsCount: currentStations.length,
            stationTimes: currentStationTimes,
            transferInfo: currentTransferInfo
          });
        }
        
        pathDetails.value = segments;
        pathLength.value = {
          duration: response.total_duration,
          emissions: response.emissions || 0,
          stationsCount: segments.reduce((total, seg) => total + seg.stations.length, 0)
        };
      }
    } else {
      // Recherche classique
      if (!startStationId.value || !endStationId.value) {
        throw new Error('IDs de stations manquants. Veuillez sélectionner les stations depuis les suggestions.');
      }
      
      const response = await api.post('/shortest-path', {
        start: startStationId.value,
        end: endStationId.value
      });
      
      // Transformer les données de l'API shortest-path pour correspondre au format attendu
      const transformedSegments = response.chemin.map(segment => ({
        line: segment.Ligne,
        stations: segment.Stations.map(station => station["Nom Station"]),
        duration: segment.Duration || 0,
        stationsCount: segment.Stations.length,
        stationTimes: null, // Pas d'horaires pour le mode classique
        transferInfo: null,
        // Conserver les données originales pour l'affichage sur la carte
        originalStations: segment.Stations
      }));
      
      pathDetails.value = transformedSegments;
      pathLength.value = {
        duration: response.duration,
        emissions: response.emissions,
        stationsCount: response.stations_count
      };
    }
  } catch (error) {
    console.error('Erreur lors de la recherche:', error);
    
    // Vérifier si c'est une erreur de service indisponible avec des informations détaillées
    if (error.responseData && error.responseData.service_info) {
      const serviceInfo = error.responseData.service_info;
      let message = serviceInfo.message;
      
      if (serviceInfo.suggested_departure) {
        message += `\n\nVoulez-vous rechercher un itinéraire pour ${serviceInfo.suggested_departure} ?`;
        
        if (confirm(message)) {
          // Mettre à jour l'heure de départ avec l'heure suggérée
          departureTime.value = serviceInfo.suggested_departure;
          // Relancer la recherche
          findPath();
          return;
        }
      } else {
        alert(message);
      }
    } else {
    alert(error.message || 'Erreur lors de la recherche d\'itinéraire');
    }
  } finally {
    isLoading.value = false;
  }
}

async function testConnexity() {
  try {
    isLoading.value = true
    const url = startStation.value 
      ? `/connexity?station=${encodeURIComponent(startStation.value)}`
      : '/connexity'
    connexityResult.value = await api.get(url)
    showConnexityModal.value = true
  } catch (error) {
    console.error('Erreur lors du test de connexité:', error)
    connexityResult.value = { error: error.message }
    showConnexityModal.value = true
  } finally {
    isLoading.value = false
  }
}

function closeConnexityModal() {
  showConnexityModal.value = false;
  startStation.value = '';
  startStationSuggestions.value = [];
  connexityResult.value = null;
}

function getStationsForLine(structuralPath, line, fromStation, toStation) {
  if (!structuralPath || structuralPath.length === 0) {
    return [fromStation, toStation];
  }
  
  // Filtrer les segments de la ligne spécifiée
  const lineSegments = structuralPath.filter(segment => segment.line === line);
  
  if (lineSegments.length === 0) {
    return [fromStation, toStation];
  }
  
  // Extraire toutes les stations de cette ligne dans l'ordre
  const stations = [];
  const seenStations = new Set();
  
  for (const segment of lineSegments) {
    // Ajouter la station de départ si pas déjà vue
    if (!seenStations.has(segment.from_station)) {
      stations.push(segment.from_station);
      seenStations.add(segment.from_station);
    }
    
    // Ajouter la station d'arrivée si pas déjà vue
    if (!seenStations.has(segment.to_station)) {
      stations.push(segment.to_station);
      seenStations.add(segment.to_station);
    }
  }
  
  // Si les stations de départ et d'arrivée ne sont pas dans la liste,
  // les ajouter aux bonnes positions
  if (!stations.includes(fromStation)) {
    // Trouver la position appropriée pour fromStation
    const fromIndex = lineSegments.findIndex(seg => 
      seg.from_station === fromStation || seg.to_station === fromStation
    );
    if (fromIndex >= 0) {
      stations.splice(fromIndex, 0, fromStation);
    } else {
      stations.unshift(fromStation);
    }
  }
  
  if (!stations.includes(toStation)) {
    // Trouver la position appropriée pour toStation
    const toIndex = lineSegments.findIndex(seg => 
      seg.from_station === toStation || seg.to_station === toStation
    );
    if (toIndex >= 0) {
      stations.splice(toIndex + 1, 0, toStation);
    } else {
      stations.push(toStation);
    }
  }
  
  return stations;
}

function calculateStationTimes(stations, segment) {
  if (!stations || stations.length === 0) {
    return [];
  }
  
  const stationTimes = [];
  const departureTime = new Date(`2000-01-01T${segment.departure_time}`);
  const arrivalTime = new Date(`2000-01-01T${segment.arrival_time}`);
  const totalTravelTime = (arrivalTime - departureTime) / 1000; // en secondes
  
  // Calculer le temps de trajet par station (approximation linéaire)
  const timePerStation = totalTravelTime / (stations.length - 1);
  
  for (let i = 0; i < stations.length; i++) {
    const station = stations[i];
    const stationTime = new Date(departureTime.getTime() + (i * timePerStation * 1000));
    
    stationTimes.push({
      station: station,
      departure_time: i === 0 ? segment.departure_time : null, // Seule la première station a un départ
      arrival_time: stationTime.toTimeString().slice(0, 8), // Format HH:MM:SS
      wait_time: i === 0 ? segment.wait_time : 0 // Seule la première station a un temps d'attente
    });
  }
  
  return stationTimes;
}

function createStationTimesForSegment(stations, segment) {
  if (!stations || stations.length === 0) {
    return {};
  }
  
  const stationTimes = {};
  
  for (let i = 0; i < stations.length; i++) {
    const station = stations[i];
    
    // Calculer les horaires basés sur les données GTFS du segment
    let departureTime = null;
    let arrivalTime = null;
    
    if (i === 0) {
      // Première station : heure de départ du segment
      departureTime = segment.departure_time;
    }
    
    if (i === stations.length - 1) {
      // Dernière station : heure d'arrivée du segment
      arrivalTime = segment.arrival_time;
    } else {
      // Stations intermédiaires : calculer l'heure d'arrivée approximative
      if (segment.departure_time && segment.arrival_time) {
        const departure = new Date(`2000-01-01T${segment.departure_time}`);
        const arrival = new Date(`2000-01-01T${segment.arrival_time}`);
        const totalTime = arrival - departure;
        const timePerStation = totalTime / (stations.length - 1);
        const stationArrival = new Date(departure.getTime() + (i * timePerStation));
        arrivalTime = stationArrival.toTimeString().slice(0, 8);
      }
    }
    
    stationTimes[station] = {
      departure: departureTime,
      arrival: arrivalTime
    };
  }
  
  return stationTimes;
}

function updateStationTimes(existingTimes, newSegment) {
  if (!existingTimes || Object.keys(existingTimes).length === 0) {
    return createStationTimesForSegment([newSegment.from_station, newSegment.to_station], newSegment);
  }
  
  // Mettre à jour l'heure d'arrivée de la station de correspondance
  if (existingTimes[newSegment.from_station]) {
    existingTimes[newSegment.from_station].arrival = newSegment.departure_time;
  }
  
  // Ajouter la nouvelle station d'arrivée
  existingTimes[newSegment.to_station] = {
    departure: null,
    arrival: newSegment.arrival_time
  };
  
  return existingTimes;
}

// Ajoute cette fonction utilitaire en haut du script (avant fetchLines) :
function darkenColor(hex, factor = 0.7) {
  // hex: #RRGGBB, factor < 1 pour foncer
  if (!hex || typeof hex !== 'string' || !hex.startsWith('#')) return hex;
  let r = parseInt(hex.slice(1, 3), 16);
  let g = parseInt(hex.slice(3, 5), 16);
  let b = parseInt(hex.slice(5, 7), 16);
  r = Math.floor(r * factor);
  g = Math.floor(g * factor);
  b = Math.floor(b * factor);
  return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
}
</script>

<template>
  <main class="app-container">
    <!-- Carte en arrière-plan qui prend tout l'écran -->
    <div class="map-container">
    <MetroMapLeaflet />
    <ServerStatus />

      <!-- Panneau de contrôle unifié -->
      <div class="unified-control-panel" style="font-family: -apple-system, BlinkMacSystemFont, 'San Francisco', 'Helvetica Neue', Arial, sans-serif;">
        <div class="panel-container">
          <!-- En-tête avec titre et mode toggle -->
          <div class="panel-header">
            <h2>Navigation Métro</h2>
        <div class="mode-toggle">
          <button 
            :class="['toggle-btn', { active: searchMode === 'classic' }]"
            @click="searchMode = 'classic'; clearResults()"
          >
              <span class="toggle-text">Classique</span>
          </button>
          <button 
            :class="['toggle-btn', { active: searchMode === 'temporal' }]"
            @click="searchMode = 'temporal'; clearResults()"
          >
              <span class="toggle-text">Temporel</span>
          </button>
        </div>
      </div>

          <!-- Section de recherche d'itinéraire -->
          <div class="search-section">
            <div class="section-title">
              <span>Planification d'itinéraire</span>
            </div>
            
          <!-- Stations -->
            <div class="stations-inputs">
        <div class="input-group">
              <label for="startStation">
                  <span class="station-indicator departure"></span>
                  <span class="label-text">De</span>
              </label>
          <input
            id="startStation"
            v-model="startStation"
            type="text"
                  placeholder="Entrez la station de départ"
            @input="handleStartStationInput"
                  class="station-input"
          />
          <div v-if="startStationSuggestions.length > 0" class="suggestions-list">
            <div
              v-for="suggestion in startStationSuggestions"
              :key="suggestion"
              class="suggestion-item"
              @click="selectStartStation(suggestion)"
            >
              {{ suggestion }}
            </div>
          </div>
        </div>
              
        <div class="input-group">
              <label for="endStation">
                  <span class="station-indicator arrival"></span>
                  <span class="label-text">À</span>
              </label>
          <input
            id="endStation"
            v-model="endStation"
            type="text"
                  placeholder="Entrez la station de destination"
            @input="handleEndStationInput"
                  class="station-input"
          />
          <div v-if="endStationSuggestions.length > 0" class="suggestions-list">
            <div
              v-for="suggestion in endStationSuggestions"
              :key="suggestion"
              class="suggestion-item"
              @click="selectEndStation(suggestion)"
            >
              {{ suggestion }}
            </div>
          </div>
        </div>
          </div>

          <!-- Paramètres temporels -->
          <div v-if="searchMode === 'temporal'" class="temporal-section">
            <div class="temporal-header">
              <span class="temporal-title">
                <span v-if="timeType === 'departure'">Heure de départ</span>
                <span v-else>Heure d'arrivée</span>
              </span>
              <div class="mode-toggle" style="margin-left: 1rem; display: inline-block;">
                <button 
                  :class="['toggle-btn', { active: timeType === 'departure' }]"
                  @click="timeType = 'departure'"
                  style="min-width: 90px;"
                >
                  Départ
                </button>
                <button 
                  :class="['toggle-btn', { active: timeType === 'arrival' }]"
                  @click="timeType = 'arrival'"
                  style="min-width: 90px;"
                >
                  Arrivée
                </button>
              </div>
            </div>
            <div class="temporal-inputs">
              <div class="input-group">
                <label :for="timeType === 'departure' ? 'departureTime' : 'arrivalTime'">
                  <span class="label-text">
                    {{ timeType === 'departure' ? 'Heure de départ' : 'Heure d\'arrivée' }}
                  </span>
                </label>
                <input
                  :id="timeType === 'departure' ? 'departureTime' : 'arrivalTime'"
                  v-model="departureTime"
                  type="text"
                  :placeholder="timeType === 'departure' ? '08:30 ou 24:30 (00:30 lendemain)' : '09:00 ou 24:30'"
                  pattern="^([0-2]?[0-9]|3[0-1]):[0-5][0-9]$"
                  class="time-input"
                  @blur="validateTimeInput"
                />
              </div>
              <div class="input-group">
                <label for="departureDate">
                  <span class="label-text">Date</span>
                </label>
                <input
                  id="departureDate"
                  v-model="departureDate"
                  type="date"
                  min="2024-03-01"
                  max="2024-03-31"
                  class="date-input"
                />
              </div>
            </div>
          </div>

            <!-- Bouton de recherche principal -->
        <button
              class="primary-search-button"
          @click="findPath"
          :disabled="isLoading || !startStation || !endStation"
        >
            <span class="button-text">
                {{ isLoading ? 'Recherche...' : 'Rechercher un itinéraire' }}
            </span>
        </button>
        </div>

          <!-- Section des outils avancés -->
          <div class="tools-section">
            <div class="section-title">
              <span>Outils avancés</span>
            </div>
            
            <div class="tools-grid">
              <button class="tool-button" @click="toggleACPM">
                <span class="tool-text">ACPM</span>
              </button>
              
              <button class="tool-button" @click="showConnexityModal = true">
                <span class="tool-text">Connexité</span>
              </button>
              
              <button class="tool-button" @click="toggleLines">
                <span class="tool-text">Lignes</span>
              </button>
              
              <button class="tool-button" @click="clearPath">
                <span class="tool-text">Effacer</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Panneau d'affichage des résultats superposé -->
    <div v-if="pathDetails && pathDetails.length > 0" class="floating-panel fade-in">
      <div class="content-wrapper">
        <div class="path-panel-header">
          <h2>Itinéraire {{ searchMode === 'temporal' ? 'temporel' : '' }}</h2>
          <div class="total-time-badge">
            <span class="time-icon"></span>
            {{ formatTime(pathLength) }}
          </div>
        </div>

        <!-- Informations temporelles spécifiques -->
        <div v-if="searchMode === 'temporal' && temporalData" class="temporal-info">
          <div class="temporal-details">
            <div class="detail-item">
              <span class="detail-icon clock-icon"></span>
              <span>Départ: {{ temporalData.departure_time }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-icon clock-icon"></span>
              <span>Arrivée: {{ temporalData.arrival_time }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-icon wait-icon"></span>
              <span>Temps d'attente: {{ formatTime(temporalData.total_wait_time) }}</span>
            </div>
          </div>
        </div>

        <div class="trip-info-panel">
          <div class="info-item">
            <span class="info-icon time-icon"></span>
            <span class="info-label">Durée</span>
            <span class="info-value">{{ formatTime(pathLength) }}</span>
          </div>
          <div class="info-item">
            <span class="info-icon emissions-icon"></span>
            <span class="info-label">Émissions</span>
            <span class="info-value">{{ pathLength?.emissions || 0 }}g CO₂</span>
          </div>
          <div class="info-item">
            <span class="info-icon stations-icon"></span>
            <span class="info-label">Stations</span>
            <span class="info-value">{{ getTotalStations() }}</span>
          </div>
          <!-- Affichage du temps total ACPM quand activé -->
          <div v-if="showACPM && acpmTotalWeight" class="info-item acpm-info">
            <span class="info-icon acpm-icon"></span>
            <span class="info-label">ACPM Total</span>
            <span class="info-value">{{ formatACPMTime(acpmTotalWeight) }}</span>
          </div>
        </div>

        <div class="timeline">
          <div
            v-for="(segment, index) in pathDetails"
            :key="index"
            class="timeline-segment"
          >
            <!-- Indicateur de ligne -->
            <div class="line-indicator" :style="{ backgroundColor: LINE_COLORS[segment.line] || '#000000' }">
              {{ segment.line }}
            </div>

            <!-- Contenu du segment -->
            <div class="segment-content">
              <div class="segment-header">
                <span class="segment-title">Ligne {{ segment.line }}</span>
                <span class="segment-duration">{{ formatTime(segment.duration) }}</span>
                <!-- Informations temporelles pour le mode temporel -->
                <div v-if="searchMode === 'temporal' && segment.departure_time" class="segment-times">
                  <span class="departure-time">{{ segment.departure_time }}</span>
                  <span class="arrow">→</span>
                  <span class="arrival-time">{{ segment.arrival_time }}</span>
                </div>
              </div>

              <!-- Informations de transfert -->
              <div v-if="searchMode === 'temporal' && segment.transferInfo" class="transfer-info">
                <div class="transfer-badge glassmorphism">
                  <div class="transfer-header-main">
                    <div class="transfer-icon-container">
                      <div class="transfer-icon">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                          <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                      </div>
                      <div class="transfer-title">
                        Correspondance
                      </div>
                    </div>
                    <div class="transfer-time">
                      {{ formatTime(segment.transferInfo.transferTime) }}
                    </div>
                  </div>
                  <div class="transfer-details">
                    <div class="transfer-item">
                      <span class="transfer-label">Ligne {{ segment.transferInfo.fromLine }}</span>
                      <span class="transfer-value">{{ segment.transferInfo.transferStation }}</span>
                      </div>
                    <div class="transfer-arrow">↓</div>
                    <div class="transfer-item">
                      <span class="transfer-label">Ligne {{ segment.transferInfo.toLine }}</span>
                      <span class="transfer-value">{{ segment.transferInfo.transferStation }}</span>
                      </div>
                    </div>
                    </div>
                  </div>
                  
              <!-- Stations avec horaires -->
              <div class="station-times">
                <div
                  v-for="(station, stationIndex) in segment.stations"
                  :key="stationIndex"
                  class="station-time-item"
                  :class="{ 'interchange': isInterchange(index, stationIndex) }"
                >
                  <div class="station-main-row">
                    <div class="station-info">
                  <span class="station-name">{{ station }}</span>
                      <span v-if="isInterchange(index, stationIndex)" class="interchange-badge">
                        Correspondance
                  </span>
                </div>
                    <div class="station-times-right">
                      <!-- Horaires temporels avec style glassmorphism -->
                      <div v-if="searchMode === 'temporal' && segment.stationTimes && segment.stationTimes[station]" class="station-times-container">
                        <!-- Heure de départ -->
                        <div v-if="segment.stationTimes[station].departure" 
                             class="time-badge glassmorphism departure">
                          <div class="time-content">
                            <span class="time-label">Départ</span>
                            <span class="time-value">{{ formatTimeDisplay(segment.stationTimes[station].departure) }}</span>
                          </div>
                        </div>
                        <!-- Heure d'arrivée -->
                        <div v-if="segment.stationTimes[station].arrival" 
                             class="time-badge glassmorphism arrival">
                          <div class="time-content">
                            <span class="time-label">Arrivée</span>
                            <span class="time-value">{{ formatTimeDisplay(segment.stationTimes[station].arrival) }}</span>
                          </div>
                        </div>
                    </div>
                      <!-- Indicateur de correspondance avec temps -->
                      <div v-if="searchMode === 'temporal' && isInterchange(index, stationIndex) && getTotalStopTime(index)" class="transfer-panel">
                        <div class="transfer-header">
                          <span class="transfer-title">Temps d'arrêt</span>
                  </div>
                        <div class="transfer-details">
                          <div v-if="getTransferTime(index)" class="transfer-item">
                            <span class="transfer-label">Correspondance:</span>
                            <span class="transfer-value">{{ formatTime(getTransferTime(index)) }}</span>
                </div>
                          <div v-if="getWaitTime(index + 1)" class="transfer-item">
                            <span class="transfer-label">Attente:</span>
                            <span class="transfer-value">{{ formatTime(getWaitTime(index + 1)) }}</span>
              </div>
            </div>
                        <div class="transfer-progress">
                          <div class="progress-bar">
                            <div 
                              class="progress-fill" 
                              :style="{ 
                                width: getTransferProgress(index) + '%',
                                backgroundColor: getTransferProgressColor(index)
                              }"
                            ></div>
          </div>
                          <span class="progress-text">{{ getTransferProgressText(index) }}</span>
        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Message quand aucun résultat -->
    <div v-else-if="!isLoading && (showACPM || startStation || endStation)" class="floating-panel fade-in">
      <div class="content-wrapper">
        <div v-if="!showACPM || (showACPM && !acpmTotalWeight)" class="no-results-content">
          <h3>🚇 Prêt à calculer votre itinéraire</h3>
          <p>Sélectionnez vos stations de départ et d'arrivée, puis cliquez sur "Rechercher un itinéraire" pour commencer.</p>
        </div>
        
        <!-- Affichage du temps ACPM même sans itinéraire -->
        <div v-if="showACPM && acpmTotalWeight" class="acpm-standalone-info">
          <div class="acpm-header">
            <h4>ACPM (Arbre Couvrant de Poids Minimum)</h4>
          </div>
          <div class="acpm-time-display">
            <span class="acpm-icon-standalone"></span>
            <span class="acpm-label">Temps total du réseau</span>
            <span class="acpm-value">{{ formatACPMTime(acpmTotalWeight) }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal de connexité -->
    <div v-if="showConnexityModal" class="modal-overlay" @click="closeConnexityModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Test de connexité</h3>
          <button class="close-button" @click="closeConnexityModal">×</button>
        </div>

        <div class="modal-body">
          <div class="input-group">
            <label for="connexityStation">Station (optionnel)</label>
            <input
              id="connexityStation"
              v-model="startStation"
              type="text"
              placeholder="Laisser vide pour tester tout le réseau"
              @input="handleStartStationInput"
              class="station-input"
            />
            <div v-if="startStationSuggestions.length > 0" class="suggestions-list">
              <div
                v-for="suggestion in startStationSuggestions"
                :key="suggestion"
                class="suggestion-item"
                @click="selectStartStation(suggestion)"
              >
                {{ suggestion }}
              </div>
            </div>
          </div>

          <button
            class="modal-button"
            @click="testConnexity"
            :disabled="isLoading"
          >
            {{ isLoading ? 'Test en cours...' : 'Tester la connexité' }}
          </button>

          <div v-if="connexityResult" class="connexity-results">
            <div class="result-item">
              <span class="result-label">Connexité:</span>
              <span class="result-value" :class="{ connected: connexityResult.connected }">
                {{ connexityResult.connected ? 'Connecté' : 'Non connecté' }}
              </span>
              </div>
            <div v-if="connexityResult.components" class="result-item">
              <span class="result-label">Composantes:</span>
              <span class="result-value">{{ connexityResult.components }}</span>
            </div>
              </div>
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
/* Styles globaux pour éliminer l'espace blanc */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  margin: 0;
  padding: 0;
  overflow: hidden;
  width: 100vw;
  height: 100vh;
}

.app-container {
  width: 100vw;
  height: 100vh;
  position: relative;
  overflow: hidden;
  background-color: var(--apple-ui-background);
  margin: 0;
  padding: 0;
}

.map-container {
  width: 100vw;
  height: 100vh;
  position: relative;
  margin: 0;
  padding: 0;
}

/* S'assurer que la carte Leaflet prend tout l'espace */
.map-container .metro-map {
  width: 100vw !important;
  height: 100vh !important;
  position: absolute !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  z-index: 1 !important;
}

/* Masquer le panneau de recherche intégré dans MetroMapLeaflet */
.map-container .liquid-glass-panel {
  display: none !important;
  visibility: hidden !important;
  opacity: 0 !important;
  pointer-events: none !important;
  z-index: -1 !important;
  transform: scale(0) !important;
}

/* Masquer la légende des lignes intégrée */
.map-container .legend-lines {
  display: none !important;
}

/* S'assurer que les éléments Leaflet prennent tout l'espace */
.map-container .leaflet-container {
  width: 100vw !important;
  height: 100vh !important;
  margin: 0 !important;
  padding: 0 !important;
}

.map-container .leaflet-pane {
  width: 100vw !important;
  height: 100vh !important;
}

.floating-panel {
  position: fixed;
  top: 20px;
  right: 20px;
  width: 33.33vw;
  min-width: 350px;
  max-width: 500px;
  max-height: calc(100vh - 40px);
  background: linear-gradient(135deg, rgba(89, 95, 207, 0.95), rgba(81, 171, 187, 0.95));
  border-radius: 20px;
  backdrop-filter: blur(30px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  z-index: 1000;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.floating-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0.05));
  border-radius: 20px;
  z-index: -1;
}

.content-wrapper {
  background: linear-gradient(145deg, rgba(61, 81, 181, 0.8), rgba(81, 162, 171, 0.8));
  backdrop-filter: blur(20px);
  border-radius: 18px;
  padding: 20px;
  position: relative;
  z-index: 1;
  max-height: calc(100vh - 80px);
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.4) transparent;
}

.content-wrapper::-webkit-scrollbar {
  width: 6px;
}

.content-wrapper::-webkit-scrollbar-track {
  background: transparent;
}

.content-wrapper::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.4);
  border-radius: 3px;
}

.content-wrapper::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.6);
}

/* Suppression du centered-pill inutilisé */

/* Suppression des anciens styles de layout */
.main-layout,
.left-column,
.right-column {
  display: none;
}

/* Masquer tous les anciens panneaux liquid-glass */
.liquid-glass-panel:not(.unified-control-panel) {
  display: none !important;
  visibility: hidden !important;
  opacity: 0 !important;
  pointer-events: none !important;
  z-index: -1 !important;
  transform: scale(0) !important;
}

/* Règle spécifique pour le panneau MetroMapLeaflet */
div[style*="top: var(--spacing-xl)"] {
  display: none !important;
  visibility: hidden !important;
  opacity: 0 !important;
}

.no-results-panel {
  display: none;
}

.no-results-content {
  display: none;
}

.path-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  flex-wrap: wrap;
  gap: 12px;
}

.path-panel-header h2 {
  font-size: 20px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  margin: 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  flex: 1;
  min-width: 0;
}

.timeline {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.timeline-segment {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}

.line-indicator {
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  font-weight: 700;
  font-size: 16px;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  flex-shrink: 0;
}

.segment-content {
  flex: 1;
  min-width: 0;
}

.segment-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.segment-title {
  font-size: 16px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
  flex: 1;
  min-width: 0;
}

.segment-duration {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
  background: rgba(255, 255, 255, 0.15);
  padding: 4px 10px;
  border-radius: 8px;
  flex-shrink: 0;
}

.segment-stations {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.station-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.25);
  transition: all 0.3s ease;
  position: relative;
}

.station-item:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.35);
  transform: translateY(-1px);
}

.station-main {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.station-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.station-name {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.98);
  flex: 1;
  min-width: 0;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.station-lines {
  display: flex;
  gap: 4px;
  flex-shrink: 0;
}

.station-line-pill {
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  min-width: 20px;
  text-align: center;
}

.station-label {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(255, 255, 255, 0.85);
  background: rgba(255, 255, 255, 0.2);
  padding: 4px 8px;
  border-radius: 6px;
  flex-shrink: 0;
}

.interchange-lines {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
  background: rgba(255, 255, 255, 0.25);
  padding: 6px 12px;
  border-radius: 8px;
  flex-shrink: 0;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.station-times {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
  font-size: 12px;
}

.station-time-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  width: 100%;
}

.station-time-item:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.station-time-item.interchange {
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.2), rgba(255, 193, 7, 0.1));
  border-color: rgba(255, 193, 7, 0.4);
}

.station-main-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  gap: 12px;
}

.station-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.station-name {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.98);
  flex: 1;
  min-width: 0;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.interchange-badge {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(255, 193, 7, 0.9);
  background: rgba(255, 193, 7, 0.2);
  padding: 2px 6px;
  border-radius: 4px;
  align-self: flex-start;
}

.station-times-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  min-width: 120px;
  flex-shrink: 0;
}

.station-times-container {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-end;
}

.time-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 12px;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  min-width: 0;
  background: rgba(255, 255, 255, 0.15);
}

.time-badge.glassmorphism {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.25), rgba(255, 255, 255, 0.15));
  backdrop-filter: blur(25px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  position: relative;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.time-badge.glassmorphism.departure {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.25), rgba(76, 175, 80, 0.15));
  border-color: rgba(76, 175, 80, 0.4);
}

.time-badge.glassmorphism.arrival {
  background: linear-gradient(135deg, rgba(255, 152, 0, 0.25), rgba(255, 152, 0, 0.15));
  border-color: rgba(255, 152, 0, 0.4);
}

.time-badge.glassmorphism::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), transparent 50%, rgba(255, 255, 255, 0.05));
  border-radius: 12px;
  z-index: -1;
}

.time-badge.glassmorphism.departure::before {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.1), transparent 50%, rgba(76, 175, 80, 0.05));
}

.time-badge.glassmorphism.arrival::before {
  background: linear-gradient(135deg, rgba(255, 152, 0, 0.1), transparent 50%, rgba(255, 152, 0, 0.05));
}

.time-badge.glassmorphism:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 12px 40px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.4);
}

.time-badge.glassmorphism.departure:hover {
  border-color: rgba(76, 175, 80, 0.5);
  box-shadow: 
    0 12px 40px rgba(76, 175, 80, 0.2),
    inset 0 1px 0 rgba(76, 175, 80, 0.3);
}

.time-badge.glassmorphism.arrival:hover {
  border-color: rgba(255, 152, 0, 0.5);
  box-shadow: 
    0 12px 40px rgba(255, 152, 0, 0.2),
    inset 0 1px 0 rgba(255, 152, 0, 0.3);
}

.time-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
  align-items: center;
}

.time-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  opacity: 0.9;
  color: rgba(255, 255, 255, 0.95);
  white-space: nowrap;
}

.time-value {
  font-size: 14px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.98);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  white-space: nowrap;
}

.trip-info-panel {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
  padding: 16px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1));
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(25px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

.info-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 12px 8px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  text-align: center;
}

.info-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  color: rgba(255, 255, 255, 0.9);
  text-align: center;
  white-space: nowrap;
}

.info-value {
  font-size: 14px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.98);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  text-align: center;
  white-space: nowrap;
}

.total-time-badge {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.3), rgba(76, 175, 80, 0.2));
  border-radius: 12px;
  border: 1px solid rgba(76, 175, 80, 0.4);
  backdrop-filter: blur(20px);
  font-weight: 600;
  color: rgba(255, 255, 255, 0.98);
  box-shadow: 0 4px 16px rgba(76, 175, 80, 0.3);
}

.emissions-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M7 13l3 3 7-7'%3E%3C/path%3E%3Cpath d='M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z'%3E%3C/path%3E%3C/svg%3E");
}

.stations-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='3'%3E%3C/circle%3E%3Cpath d='M12 1v6m0 6v6'%3E%3C/path%3E%3Cpath d='M23 12h-6m-6 0H1'%3E%3C/path%3E%3C/svg%3E");
}

.acpm-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z'%3E%3C/path%3E%3Cpolyline points='3.27,6.96 12,12.01 20.73,6.96'%3E%3C/polyline%3E%3Cline x1='12' y1='22.08' x2='12' y2='12'%3E%3C/line%3E%3C/svg%3E");
}

.acpm-info {
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.2), rgba(255, 193, 7, 0.1));
  border: 1px solid rgba(255, 193, 7, 0.3);
}

/* ...existing code... */

/* ✅ MODIFICATION : Responsive pour le nouveau panneau */
@media (max-width: 768px) {
  .trip-info-panel {
    grid-template-columns: 1fr;
    gap: var(--spacing-xs);
  }
  
  .info-item {
    flex-direction: row;
    justify-content: space-between;
    text-align: left;
  }
  
  .info-value {
    margin-left: auto;
  }
}

/* Styles pour le composant temporel */

@media (max-width: 768px) {
}

/* Styles pour le panneau de contrôle unifié - Style Apple Glassmorphism */
.unified-control-panel {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 1000;
  width: 400px;
  background: linear-gradient(135deg, rgba(89, 95, 207, 0.8), rgba(81, 171, 187, 0.8));
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border-radius: 40px;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.1),
    inset 0 0 0 1px rgba(255, 255, 255, 0.2);
  padding: 2px;
  overflow: hidden;
  max-height: calc(100vh - 40px);
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
}

.panel-container {
  background: linear-gradient(145deg, rgba(61, 81, 181, 0.8), rgba(81, 162, 171, 0.8));
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border-radius: 38px;
  padding: 0;
  overflow-y: auto;
  max-height: calc(100vh - 40px);
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 28px 24px 20px;
  border-bottom: 0.5px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.02);
}

.panel-header h2 {
  margin: 0 0 20px 0;
  font-size: 34px;
  font-weight: 700;
  letter-spacing: -0.8px;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: none;
}

.mode-toggle {
  display: flex;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 16px;
  padding: 3px;
  gap: 2px;
  backdrop-filter: blur(20px);
  border: 0.5px solid rgba(255, 255, 255, 0.1);
}

.toggle-btn {
  flex: 1;
  padding: 14px 20px;
  border: none;
  border-radius: 13px;
  background: transparent;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 700;
  font-size: 17px;
  letter-spacing: -0.3px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  position: relative;
}

.toggle-btn.active {
  background: rgba(255, 255, 255, 0.25);
  color: rgba(255, 255, 255, 0.95);
  box-shadow: 
    0 2px 12px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(20px);
}

.toggle-btn:hover:not(.active) {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.85);
}

/* Styles pour les suggestions - Apple Style */
.suggestions-list {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(40px);
  border-radius: 16px;
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.15),
    0 4px 12px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  border: 0.5px solid rgba(255, 255, 255, 0.6);
  z-index: 1001;
  max-height: 280px;
    overflow-y: auto;
  margin-top: 6px;
  animation: slideDown 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-8px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.suggestion-item {
  padding: 16px 20px;
  cursor: pointer;
  color: #1d1d1f;
  font-weight: 500;
  font-size: 16px;
  letter-spacing: -0.2px;
  transition: all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  border-bottom: 0.5px solid rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
}

.suggestion-item:last-child {
  border-bottom: none;
  border-bottom-left-radius: 16px;
  border-bottom-right-radius: 16px;
}

.suggestion-item:first-child {
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
}

.suggestion-item:hover {
  background: rgba(0, 0, 0, 0.04);
  color: #000;
  transform: translateX(2px);
}

.suggestion-item::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: linear-gradient(135deg, #007AFF, #5AC8FA);
  opacity: 0.8;
  flex-shrink: 0;
}

/* Styles pour la section temporelle */
.temporal-section {
  margin-top: 20px;
  padding: 20px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 18px;
  border: 0.5px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
}

.temporal-header {
  margin-bottom: 16px;
}

.temporal-title {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.4px;
  color: rgba(255, 255, 255, 0.95);
}

.temporal-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
  
.temporal-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
    gap: 12px;
  }
  
/* Styles pour les informations temporelles */
.temporal-info {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1));
  border-radius: 20px;
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  border: 1px solid rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(25px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  position: relative;
  overflow: hidden;
}

.temporal-info::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), transparent);
  border-radius: 20px;
  z-index: -1;
}

.temporal-details {
  display: flex;
    flex-direction: column;
  gap: var(--spacing-md);
}

.temporal-details .detail-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  font-size: 15px;
  color: rgba(255, 255, 255, 0.95);
  padding: var(--spacing-sm) var(--spacing-md);
  background: rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.temporal-details .detail-item:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

.clock-icon {
  width: 16px;
  height: 16px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cpolyline points='12 6 12 12 16 14'%3E%3C/polyline%3E%3C/svg%3E");
  background-size: contain;
  opacity: 0.8;
}

.wait-icon {
  width: 16px;
  height: 16px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 2v6m0 6v6'%3E%3C/path%3E%3Cpath d='M23 12h-6m-6 0H1'%3E%3C/path%3E%3C/svg%3E");
  background-size: contain;
  opacity: 0.8;
}

.segment-times {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 4px;
}

.departure-time, .arrival-time {
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 8px;
  border-radius: 8px;
  font-weight: 500;
}

.arrow {
  color: rgba(255, 255, 255, 0.6);
  font-weight: bold;
}

/* Styles pour les éléments d'affichage des stations */
.station-time-item {
  display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  width: 100%;
}

.station-time-item:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.station-time-item.interchange {
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.2), rgba(255, 193, 7, 0.1));
  border-color: rgba(255, 193, 7, 0.4);
}

.station-main-row {
  display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
  gap: 12px;
}

.station-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.station-name {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.98);
  flex: 1;
  min-width: 0;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.interchange-badge {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(255, 193, 7, 0.9);
  background: rgba(255, 193, 7, 0.2);
  padding: 2px 6px;
  border-radius: 4px;
    align-self: flex-start;
  }
  
.station-times-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  min-width: 120px;
  flex-shrink: 0;
}

.station-times-container {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-end;
}

.time-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 12px;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  min-width: 0;
  background: rgba(255, 255, 255, 0.15);
}

.time-badge.glassmorphism {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.25), rgba(255, 255, 255, 0.15));
  backdrop-filter: blur(25px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  position: relative;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.time-badge.glassmorphism.departure {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.25), rgba(76, 175, 80, 0.15));
  border-color: rgba(76, 175, 80, 0.4);
}

.time-badge.glassmorphism.arrival {
  background: linear-gradient(135deg, rgba(255, 152, 0, 0.25), rgba(255, 152, 0, 0.15));
  border-color: rgba(255, 152, 0, 0.4);
}

.time-badge.glassmorphism::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), transparent 50%, rgba(255, 255, 255, 0.05));
  border-radius: 12px;
  z-index: -1;
}

.time-badge.glassmorphism.departure::before {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.1), transparent 50%, rgba(76, 175, 80, 0.05));
}

.time-badge.glassmorphism.arrival::before {
  background: linear-gradient(135deg, rgba(255, 152, 0, 0.1), transparent 50%, rgba(255, 152, 0, 0.05));
}

.time-badge.glassmorphism:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 12px 40px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.4);
}

.time-badge.glassmorphism.departure:hover {
  border-color: rgba(76, 175, 80, 0.5);
  box-shadow: 
    0 12px 40px rgba(76, 175, 80, 0.2),
    inset 0 1px 0 rgba(76, 175, 80, 0.3);
}

.time-badge.glassmorphism.arrival:hover {
  border-color: rgba(255, 152, 0, 0.5);
  box-shadow: 
    0 12px 40px rgba(255, 152, 0, 0.2),
    inset 0 1px 0 rgba(255, 152, 0, 0.3);
}

.time-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
  align-items: center;
}

.time-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  opacity: 0.9;
  color: rgba(255, 255, 255, 0.95);
  white-space: nowrap;
}

.time-value {
  font-size: 14px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.98);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  white-space: nowrap;
}

.trip-info-panel {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
  padding: 16px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1));
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(25px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

.info-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 12px 8px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  text-align: center;
}

.info-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  color: rgba(255, 255, 255, 0.9);
  text-align: center;
  white-space: nowrap;
}

.info-value {
  font-size: 14px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.98);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  text-align: center;
  white-space: nowrap;
}

.total-time-badge {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.3), rgba(76, 175, 80, 0.2));
  border-radius: 12px;
  border: 1px solid rgba(76, 175, 80, 0.4);
  backdrop-filter: blur(20px);
  font-weight: 600;
  color: rgba(255, 255, 255, 0.98);
  box-shadow: 0 4px 16px rgba(76, 175, 80, 0.3);
}

.emissions-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M7 13l3 3 7-7'%3E%3C/path%3E%3Cpath d='M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z'%3E%3C/path%3E%3C/svg%3E");
}

.stations-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='3'%3E%3C/circle%3E%3Cpath d='M12 1v6m0 6v6'%3E%3C/path%3E%3Cpath d='M23 12h-6m-6 0H1'%3E%3C/path%3E%3C/svg%3E");
}

.acpm-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z'%3E%3C/path%3E%3Cpolyline points='3.27,6.96 12,12.01 20.73,6.96'%3E%3C/polyline%3E%3Cline x1='12' y1='22.08' x2='12' y2='12'%3E%3C/line%3E%3C/svg%3E");
}

.acpm-info {
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.2), rgba(255, 193, 7, 0.1));
  border: 1px solid rgba(255, 193, 7, 0.3);
}

/* ...existing code... */

/* ✅ MODIFICATION : Responsive pour le nouveau panneau */
@media (max-width: 768px) {
  .trip-info-panel {
    grid-template-columns: 1fr;
    gap: var(--spacing-xs);
  }
  
  .info-item {
    flex-direction: row;
    justify-content: space-between;
    text-align: left;
  }
  
  .info-value {
    margin-left: auto;
  }
}

/* Styles pour le composant temporel */

@media (max-width: 768px) {
}

/* Styles pour le panneau de contrôle unifié - Style Apple Glassmorphism */
.unified-control-panel {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 1000;
  width: 400px;
  background: linear-gradient(135deg, rgba(89, 95, 207, 0.8), rgba(81, 171, 187, 0.8));
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border-radius: 40px;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.1),
    inset 0 0 0 1px rgba(255, 255, 255, 0.2);
  padding: 2px;
  overflow: hidden;
  max-height: calc(100vh - 40px);
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
}

.panel-container {
  background: linear-gradient(145deg, rgba(61, 81, 181, 0.8), rgba(81, 162, 171, 0.8));
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border-radius: 38px;
  padding: 0;
  overflow-y: auto;
  max-height: calc(100vh - 40px);
  display: flex;
    flex-direction: column;
}

.panel-header {
  padding: 28px 24px 20px;
  border-bottom: 0.5px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.02);
}

.panel-header h2 {
  margin: 0 0 20px 0;
  font-size: 34px;
  font-weight: 700;
  letter-spacing: -0.8px;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: none;
}

.mode-toggle {
  display: flex;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 16px;
  padding: 3px;
  gap: 2px;
  backdrop-filter: blur(20px);
  border: 0.5px solid rgba(255, 255, 255, 0.1);
}

.toggle-btn {
  flex: 1;
  padding: 14px 20px;
  border: none;
  border-radius: 13px;
  background: transparent;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 700;
  font-size: 17px;
  letter-spacing: -0.3px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  position: relative;
}

.toggle-btn.active {
  background: rgba(255, 255, 255, 0.25);
  color: rgba(255, 255, 255, 0.95);
  box-shadow: 
    0 2px 12px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(20px);
}

.toggle-btn:hover:not(.active) {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.85);
}

/* Styles pour les suggestions - Apple Style */
.suggestions-list {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(40px);
  border-radius: 16px;
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.15),
    0 4px 12px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  border: 0.5px solid rgba(255, 255, 255, 0.6);
  z-index: 1001;
  max-height: 280px;
    overflow-y: auto;
  margin-top: 6px;
  animation: slideDown 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-8px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.suggestion-item {
  padding: 16px 20px;
  cursor: pointer;
  color: #1d1d1f;
  font-weight: 500;
  font-size: 16px;
  letter-spacing: -0.2px;
  transition: all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  border-bottom: 0.5px solid rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
}

.suggestion-item:last-child {
  border-bottom: none;
  border-bottom-left-radius: 16px;
  border-bottom-right-radius: 16px;
}

.suggestion-item:first-child {
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
}

.suggestion-item:hover {
  background: rgba(0, 0, 0, 0.04);
  color: #000;
  transform: translateX(2px);
}

.suggestion-item::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: linear-gradient(135deg, #007AFF, #5AC8FA);
  opacity: 0.8;
  flex-shrink: 0;
}

/* Styles pour la section temporelle */
.temporal-section {
  margin-top: 20px;
  padding: 20px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 18px;
  border: 0.5px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
}

.temporal-header {
  margin-bottom: 16px;
}

.temporal-title {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.4px;
  color: rgba(255, 255, 255, 0.95);
}

.temporal-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
  
.temporal-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
    gap: 12px;
  }
  
/* Styles pour les informations temporelles */
.temporal-info {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1));
  border-radius: 20px;
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  border: 1px solid rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(25px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  position: relative;
  overflow: hidden;
}

.temporal-info::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), transparent);
  border-radius: 20px;
  z-index: -1;
}

.temporal-details {
  display: flex;
    flex-direction: column;
  gap: var(--spacing-md);
}

.temporal-details .detail-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  font-size: 15px;
  color: rgba(255, 255, 255, 0.95);
  padding: var(--spacing-sm) var(--spacing-md);
  background: rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.temporal-details .detail-item:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

.clock-icon {
  width: 16px;
  height: 16px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cpolyline points='12 6 12 12 16 14'%3E%3C/polyline%3E%3C/svg%3E");
  background-size: contain;
  opacity: 0.8;
}

.wait-icon {
  width: 16px;
  height: 16px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 2v6m0 6v6'%3E%3C/path%3E%3Cpath d='M23 12h-6m-6 0H1'%3E%3C/path%3E%3C/svg%3E");
  background-size: contain;
  opacity: 0.8;
}

.segment-times {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 4px;
}

.departure-time, .arrival-time {
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 8px;
  border-radius: 8px;
  font-weight: 500;
}

.arrow {
  color: rgba(255, 255, 255, 0.6);
  font-weight: bold;
}

/* Styles pour les éléments d'affichage des stations */
.station-time-item {
  display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  width: 100%;
}

.station-time-item:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.station-time-item.interchange {
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.2), rgba(255, 193, 7, 0.1));
  border-color: rgba(255, 193, 7, 0.4);
}

.station-main-row {
  display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
  gap: 12px;
}

.station-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.station-name {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.98);
  flex: 1;
  min-width: 0;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.interchange-badge {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(255, 193, 7, 0.9);
  background: rgba(255, 193, 7, 0.2);
  padding: 2px 6px;
  border-radius: 4px;
    align-self: flex-start;
  }
  
.station-times-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  min-width: 120px;
  flex-shrink: 0;
}

.station-times-container {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-end;
}

.time-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 12px;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  min-width: 0;
  background: rgba(255, 255, 255, 0.15);
}

.time-badge.glassmorphism {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.25), rgba(255, 255, 255, 0.15));
  backdrop-filter: blur(25px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  position: relative;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.time-badge.glassmorphism.departure {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.25), rgba(76, 175, 80, 0.15));
  border-color: rgba(76, 175, 80, 0.4);
}

.time-badge.glassmorphism.arrival {
  background: linear-gradient(135deg, rgba(255, 152, 0, 0.25), rgba(255, 152, 0, 0.15));
  border-color: rgba(255, 152, 0, 0.4);
}

.time-badge.glassmorphism::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), transparent 50%, rgba(255, 255, 255, 0.05));
  border-radius: 12px;
  z-index: -1;
}

.time-badge.glassmorphism.departure::before {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.1), transparent 50%, rgba(76, 175, 80, 0.05));
}

.time-badge.glassmorphism.arrival::before {
  background: linear-gradient(135deg, rgba(255, 152, 0, 0.1), transparent 50%, rgba(255, 152, 0, 0.05));
}

.time-badge.glassmorphism:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 12px 40px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.4);
}

.time-badge.glassmorphism.departure:hover {
  border-color: rgba(76, 175, 80, 0.5);
  box-shadow: 
    0 12px 40px rgba(76, 175, 80, 0.2),
    inset 0 1px 0 rgba(76, 175, 80, 0.3);
}

.time-badge.glassmorphism.arrival:hover {
  border-color: rgba(255, 152, 0, 0.5);
  box-shadow: 
    0 12px 40px rgba(255, 152, 0, 0.2),
    inset 0 1px 0 rgba(255, 152, 0, 0.3);
}

.time-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
  align-items: center;
}

.time-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  opacity: 0.9;
  color: rgba(255, 255, 255, 0.95);
  white-space: nowrap;
}

.time-value {
  font-size: 14px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.98);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  white-space: nowrap;
}

.trip-info-panel {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
  padding: 16px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1));
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(25px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

.info-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 12px 8px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  text-align: center;
}

.info-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  color: rgba(255, 255, 255, 0.9);
  text-align: center;
  white-space: nowrap;
}

.info-value {
  font-size: 14px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.98);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  text-align: center;
  white-space: nowrap;
}

.total-time-badge {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm) var(--spacing-md);
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.3), rgba(76, 175, 80, 0.2));
  border-radius: 12px;
  border: 1px solid rgba(76, 175, 80, 0.4);
  backdrop-filter: blur(20px);
  font-weight: 600;
  color: rgba(255, 255, 255, 0.98);
  box-shadow: 0 4px 16px rgba(76, 175, 80, 0.3);
}

.emissions-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M7 13l3 3 7-7'%3E%3C/path%3E%3Cpath d='M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z'%3E%3C/path%3E%3C/svg%3E");
}

.stations-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='3'%3E%3C/circle%3E%3Cpath d='M12 1v6m0 6v6'%3E%3C/path%3E%3Cpath d='M23 12h-6m-6 0H1'%3E%3C/path%3E%3C/svg%3E");
}

.acpm-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z'%3E%3C/path%3E%3Cpolyline points='3.27,6.96 12,12.01 20.73,6.96'%3E%3C/polyline%3E%3Cline x1='12' y1='22.08' x2='12' y2='12'%3E%3C/line%3E%3C/svg%3E");
}

.acpm-info {
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.2), rgba(255, 193, 7, 0.1));
  border: 1px solid rgba(255, 193, 7, 0.3);
}

/* ...existing code... */

/* ✅ MODIFICATION : Responsive pour le nouveau panneau */
@media (max-width: 768px) {
  .trip-info-panel {
    grid-template-columns: 1fr;
    gap: var(--spacing-xs);
  }
  
  .info-item {
    flex-direction: row;
    justify-content: space-between;
    text-align: left;
  }
  
  .info-value {
    margin-left: auto;
  }
}

/* Styles pour le composant temporel */

@media (max-width: 768px) {
}

/* Styles pour le panneau de contrôle unifié - Style Apple Glassmorphism */
.unified-control-panel {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 1000;
  width: 400px;
  background: linear-gradient(135deg, rgba(89, 95, 207, 0.8), rgba(81, 171, 187, 0.8));
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border-radius: 40px;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.1),
    inset 0 0 0 1px rgba(255, 255, 255, 0.2);
  padding: 2px;
  overflow: hidden;
  max-height: calc(100vh - 40px);
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
}

.panel-container {
  background: linear-gradient(145deg, rgba(61, 81, 181, 0.8), rgba(81, 162, 171, 0.8));
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border-radius: 38px;
  padding: 0;
  overflow-y: auto;
  max-height: calc(100vh - 40px);
  display: flex;
    flex-direction: column;
}

.panel-header {
  padding: 28px 24px 20px;
  border-bottom: 0.5px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.02);
}

.panel-header h2 {
  margin: 0 0 20px 0;
  font-size: 34px;
  font-weight: 700;
  letter-spacing: -0.8px;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: none;
}

.mode-toggle {
  display: flex;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 16px;
  padding: 3px;
  gap: 2px;
  backdrop-filter: blur(20px);
  border: 0.5px solid rgba(255, 255, 255, 0.1);
}

.toggle-btn {
  flex: 1;
  padding: 14px 20px;
  border: none;
  border-radius: 13px;
  background: transparent;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 700;
  font-size: 17px;
  letter-spacing: -0.3px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  position: relative;
}

.toggle-btn.active {
  background: rgba(255, 255, 255, 0.25);
  color: rgba(255, 255, 255, 0.95);
  box-shadow: 
    0 2px 12px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(20px);
}

.toggle-btn:hover:not(.active) {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.85);
}

/* Styles pour les suggestions - Apple Style */
.suggestions-list {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(40px);
  border-radius: 16px;
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.15),
    0 4px 12px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.8);
  border: 0.5px solid rgba(255, 255, 255, 0.6);
  z-index: 1001;
  max-height: 280px;
    overflow-y: auto;
  margin-top: 6px;
  animation: slideDown 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-8px) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.suggestion-item {
  padding: 16px 20px;
  cursor: pointer;
  color: #1d1d1f;
  font-weight: 500;
  font-size: 16px;
  letter-spacing: -0.2px;
  transition: all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  border-bottom: 0.5px solid rgba(0, 0, 0, 0.06);
  display: flex;
  align-items: center;
  gap: 12px;
  position: relative;
}

.suggestion-item:last-child {
  border-bottom: none;
  border-bottom-left-radius: 16px;
  border-bottom-right-radius: 16px;
}

.suggestion-item:first-child {
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
}

.suggestion-item:hover {
  background: rgba(0, 0, 0, 0.04);
  color: #000;
  transform: translateX(2px);
}

.suggestion-item::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: linear-gradient(135deg, #007AFF, #5AC8FA);
  opacity: 0.8;
  flex-shrink: 0;
}

/* Styles pour la section temporelle */
.temporal-section {
  margin-top: 20px;
  padding: 20px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 18px;
  border: 0.5px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
}

.temporal-header {
  margin-bottom: 16px;
}

.temporal-title {
  font-size: 20px;
  font-weight: 700;
  letter-spacing: -0.4px;
  color: rgba(255, 255, 255, 0.95);
}

.temporal-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
  
.temporal-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
    gap: 12px;
  }
  
/* Styles pour les informations temporelles */
.temporal-info {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1));
  border-radius: 20px;
  padding: var(--spacing-lg);
  margin-bottom: var(--spacing-lg);
  border: 1px solid rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(25px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  position: relative;
  overflow: hidden;
}

.temporal-info::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), transparent);
  border-radius: 20px;
  z-index: -1;
}

.temporal-details {
  display: flex;
    flex-direction: column;
  gap: var(--spacing-md);
}

.temporal-details .detail-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-md);
  font-size: 15px;
  color: rgba(255, 255, 255, 0.95);
  padding: var(--spacing-sm) var(--spacing-md);
  background: rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.temporal-details .detail-item:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

.clock-icon {
  width: 16px;
  height: 16px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cpolyline points='12 6 12 12 16 14'%3E%3C/polyline%3E%3C/svg%3E");
  background-size: contain;
  opacity: 0.8;
}

.wait-icon {
  width: 16px;
  height: 16px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 2v6m0 6v6'%3E%3C/path%3E%3Cpath d='M23 12h-6m-6 0H1'%3E%3C/path%3E%3C/svg%3E");
  background-size: contain;
  opacity: 0.8;
}

.segment-times {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 4px;
}

.departure-time, .arrival-time {
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 8px;
  border-radius: 8px;
  font-weight: 500;
}

.arrow {
  color: rgba(255, 255, 255, 0.6);
  font-weight: bold;
}

/* Styles pour les éléments d'affichage des stations */
.station-time-item {
  display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  width: 100%;
}

.station-time-item:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.station-time-item.interchange {
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.2), rgba(255, 193, 7, 0.1));
  border-color: rgba(255, 193, 7, 0.4);
}

.station-main-row {
  display: flex;
    justify-content: space-between;
    align-items: center;
    width: 100%;
  gap: 12px;
}

.station-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
  min-width: 0;
}

.station-name {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.98);
  flex: 1;
  min-width: 0;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.interchange-badge {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: rgba(255, 193, 7, 0.9);
  background: rgba(255, 193, 7, 0.2);
  padding: 2px 6px;
  border-radius: 4px;
    align-self: flex-start;
  }
  
.station-times-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  min-width: 120px;
  flex-shrink: 0;
}

.station-times-container {
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-end;
}

.time-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 12px;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  min-width: 0;
  background: rgba(255, 255, 255, 0.15);
}

.time-badge.glassmorphism {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.25), rgba(255, 255, 255, 0.15));
  backdrop-filter: blur(25px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  position: relative;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.time-badge.glassmorphism.departure {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.25), rgba(76, 175, 80, 0.15));
  border-color: rgba(76, 175, 80, 0.4);
}

.time-badge.glassmorphism.arrival {
  background: linear-gradient(135deg, rgba(255, 152, 0, 0.25), rgba(255, 152, 0, 0.15));
  border-color: rgba(255, 152, 0, 0.4);
}

.time-badge.glassmorphism::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), transparent 50%, rgba(255, 255, 255, 0.05));
  border-radius: 12px;
  z-index: -1;
}

.time-badge.glassmorphism.departure::before {
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.1), transparent 50%, rgba(76, 175, 80, 0.05));
}

.time-badge.glassmorphism.arrival::before {
  background: linear-gradient(135deg, rgba(255, 152, 0, 0.1), transparent 50%, rgba(255, 152, 0, 0.05));
}

.time-badge.glassmorphism:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 12px 40px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.4);
}

.time-badge.glassmorphism.departure:hover {
  border-color: rgba(76, 175, 80, 0.5);
  box-shadow: 
    0 12px 40px rgba(76, 175, 80, 0.2),
    inset 0 1px 0 rgba(76, 175, 80, 0.3);
}

.time-badge.glassmorphism.arrival:hover {
  border-color: rgba(255, 152, 0, 0.5);
  box-shadow: 
    0 12px 40px rgba(255, 152, 0, 0.2),
    inset 0 1px 0 rgba(255, 152, 0, 0.3);
}

.time-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
  align-items: center;
}

.time-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  opacity: 0.9;
  color: rgba(255, 255, 255, 0.95);
  white-space: nowrap;
}

.time-value {
  font-size: 14px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.98);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  white-space: nowrap;
  }
  
  .trip-info-panel {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
  padding: 16px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1));
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(25px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

.temporal-info::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), transparent);
  border-radius: 20px;
  z-index: -1;
}

.temporal-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.temporal-details .detail-item {
  display: flex;
  align-items: center;
    gap: 12px;
  font-size: 15px;
  color: rgba(255, 255, 255, 0.95);
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.temporal-details .detail-item:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

.detail-icon {
  width: 16px;
  height: 16px;
  background-size: contain;
  opacity: 0.8;
}

.clock-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cpolyline points='12 6 12 12 16 14'%3E%3C/polyline%3E%3C/svg%3E");
}

.wait-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 2v6m0 6v6'%3E%3C/path%3E%3Cpath d='M23 12h-6m-6 0H1'%3E%3C/path%3E%3C/svg%3E");
}

/* Styles pour les horaires des segments */
  .segment-times {
  display: flex;
  align-items: center;
    gap: 8px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 4px;
}

.departure-time, .arrival-time {
  background: rgba(255, 255, 255, 0.1);
  padding: 4px 8px;
  border-radius: 8px;
  font-weight: 500;
}

.arrow {
  color: rgba(255, 255, 255, 0.6);
  font-weight: bold;
}

/* Styles responsives pour le layout en deux colonnes */
@media (max-width: 1200px) {
  .right-column {
    flex: 0 0 400px;
  }
}



/* Styles pour le composant temporel */

.no-results-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: linear-gradient(135deg, rgba(89, 95, 207, 0.9), rgba(81, 171, 187, 0.9));
  backdrop-filter: blur(30px);
  border: none;
  box-shadow: none;
  overflow: hidden;
  z-index: 1;
}

.no-results-content {
  text-align: center;
  padding: 40px;
  color: white;
}

.no-results-content h3 {
  margin: 0 0 15px 0;
  color: white;
    font-size: 20px;
  font-weight: 600;
}

.no-results-content p {
  margin: 0;
  font-size: 16px;
  line-height: 1.5;
  opacity: 0.9;
}

/* Styles pour l'affichage ACPM standalone */
.acpm-standalone-info {
  margin-top: 30px;
  padding: 20px;
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.2), rgba(255, 193, 7, 0.1));
  border: 1px solid rgba(255, 193, 7, 0.3);
  border-radius: 16px;
  backdrop-filter: blur(10px);
}

.acpm-header h4 {
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
  text-align: center;
}

.acpm-time-display {
  display: flex;
  align-items: center;
    justify-content: space-between;
    gap: 12px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.1);
    border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.acpm-icon-standalone {
  width: 24px;
  height: 24px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z'%3E%3C/path%3E%3Cpolyline points='3.27,6.96 12,12.01 20.73,6.96'%3E%3C/polyline%3E%3Cline x1='12' y1='22.08' x2='12' y2='12'%3E%3C/line%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: center;
  background-size: contain;
  flex-shrink: 0;
}

.acpm-label {
  flex: 1;
    font-size: 16px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
}

.acpm-value {
  font-size: 20px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace;
  background: rgba(255, 255, 255, 0.15);
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

/* Styles responsives pour le panneau flottant */
@media (max-width: 1200px) {
  .floating-panel {
    width: 35vw;
    min-width: 320px;
    max-width: 450px;
  }
}

@media (max-width: 1024px) {
  .floating-panel {
    width: 40vw;
    min-width: 300px;
    max-width: 400px;
    right: 15px;
    top: 15px;
  }
}

@media (max-width: 768px) {
  .floating-panel {
    width: calc(100vw - 30px);
    min-width: auto;
    max-width: none;
    right: 15px;
    left: 15px;
    top: 15px;
    max-height: calc(100vh - 30px);
  }
  
  .content-wrapper {
    padding: 15px;
  }
  
  .path-panel-header h2 {
    font-size: 18px;
  }
}

@media (max-width: 480px) {
  .floating-panel {
    width: calc(100vw - 20px);
    right: 10px;
    left: 10px;
    top: 10px;
    max-height: calc(100vh - 20px);
  }
  
  .content-wrapper {
    padding: 12px;
  }
  
  .path-panel-header {
    padding-bottom: 12px;
    margin-bottom: 15px;
  }
  
  .path-panel-header h2 {
    font-size: 16px;
  }
  
  .trip-info-panel {
    padding: 12px;
    gap: 8px;
  }
  
  .info-item {
    font-size: 12px;
  }
}

/* Styles pour le composant temporel */

/* Styles pour les informations de transfert/correspondance */
.transfer-info {
  margin: 16px 0;
  padding: 0 12px;
}

.transfer-badge.glassmorphism {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.25), rgba(255, 255, 255, 0.15));
  backdrop-filter: blur(25px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 20px;
  padding: 20px;
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  position: relative;
  overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.transfer-badge.glassmorphism::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), transparent 50%, rgba(255, 255, 255, 0.05));
  border-radius: 20px;
  z-index: -1;
}

.transfer-badge.glassmorphism:hover {
  transform: translateY(-4px);
  box-shadow: 
    0 12px 40px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.4);
}

.transfer-header-main {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.transfer-icon-container {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.transfer-icon {
  width: 24px;
  height: 24px;
  color: rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.transfer-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 16px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.transfer-time {
  font-size: 18px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  background: rgba(255, 255, 255, 0.2);
  padding: 8px 16px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.transfer-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 16px;
}

.transfer-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.transfer-item:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

.transfer-label {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.transfer-value {
  font-size: 14px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  background: rgba(255, 255, 255, 0.15);
  padding: 4px 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  min-width: 60px;
  text-align: center;
}

.transfer-arrow {
  font-size: 20px;
  color: rgba(255, 255, 255, 0.6);
  text-align: center;
  margin: 8px 0;
}

/* Styles pour les panneaux de transfert avec temps d'arrêt */
.transfer-panel {
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.2), rgba(255, 193, 7, 0.1));
  border: 1px solid rgba(255, 193, 7, 0.3);
  border-radius: 12px;
  padding: 12px;
  margin-top: 8px;
}

.transfer-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.transfer-header .transfer-title {
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 193, 7, 0.9);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.transfer-progress {
  margin-top: 8px;
}

.progress-bar {
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 4px;
}

.progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-text {
    font-size: 10px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  text-align: center;
  display: block;
}

/* Styles pour les icônes et éléments temporels */
.time-icon {
  width: 16px;
  height: 16px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cpolyline points='12 6 12 12 16 14'%3E%3C/polyline%3E%3C/svg%3E");
  background-size: contain;
  opacity: 0.8;
}

.clock-icon {
  width: 16px;
  height: 16px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cpolyline points='12 6 12 12 16 14'%3E%3C/polyline%3E%3C/svg%3E");
  background-size: contain;
  opacity: 0.8;
}

.wait-icon {
  width: 16px;
  height: 16px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12 2v6m0 6v6'%3E%3C/path%3E%3Cpath d='M23 12h-6m-6 0H1'%3E%3C/path%3E%3C/svg%3E");
  background-size: contain;
  opacity: 0.8;
}

.info-icon {
  width: 16px;
  height: 16px;
  background-size: contain;
  opacity: 0.8;
  margin-bottom: 4px;
}

.segment-times {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
  margin-top: 4px;
}

.departure-time, .arrival-time {
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 8px;
  border-radius: 8px;
  font-weight: 500;
}

.arrow {
  color: rgba(255, 255, 255, 0.6);
  font-weight: bold;
}

/* Styles pour les informations temporelles */
.temporal-info {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1));
  border-radius: 20px;
  padding: 20px;
  margin-bottom: 20px;
  border: 1px solid rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(25px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  position: relative;
  overflow: hidden;
}

.temporal-info::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), transparent);
  border-radius: 20px;
  z-index: -1;
}

.temporal-details {
  display: flex;
  flex-direction: column;
    gap: 12px;
  }
  
.temporal-details .detail-item {
  display: flex;
  align-items: center;
    gap: 12px;
  font-size: 15px;
  color: rgba(255, 255, 255, 0.95);
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s ease;
}

.temporal-details .detail-item:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

/* Styles pour les sections temporelles */
.temporal-section {
  margin-bottom: 20px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.temporal-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.temporal-title {
    font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.temporal-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

/* Styles pour les stations d'échange */
.stations-section {
  margin-bottom: 20px;
}

/* Responsive pour mobile */
@media (max-width: 768px) {
  .temporal-inputs {
    grid-template-columns: 1fr;
  }
  
  .transfer-header-main {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .transfer-time {
    align-self: flex-start;
  }
}

/* Styles pour les sections */
.search-section, .tools-section {
  padding: 24px;
  border-bottom: 0.5px solid rgba(255, 255, 255, 0.08);
}

.tools-section {
  border-bottom: none;
}

.section-title {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.4px;
  color: rgba(255, 255, 255, 0.95);
}

/* Styles pour les inputs de stations */
.stations-inputs {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 20px;
}

.input-group {
  position: relative;
  display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
.input-group label {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.3px;
  color: rgba(255, 255, 255, 0.9);
    margin-bottom: 10px;
  }
  
.label-text {
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.3px;
}

.station-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.station-indicator.departure {
  background: linear-gradient(135deg, #34C759, #30D158);
  box-shadow: 0 0 8px rgba(52, 199, 89, 0.4);
}

.station-indicator.arrival {
  background: linear-gradient(135deg, #FF9F0A, #FF9500);
  box-shadow: 0 0 8px rgba(255, 159, 10, 0.4);
}

.station-input, .time-input, .date-input {
    width: 100%;
  padding: 18px 20px;
  border: 0.5px solid rgba(255, 255, 255, 0.15);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.95);
  font-size: 17px;
  font-weight: 500;
  letter-spacing: -0.3px;
  backdrop-filter: blur(20px);
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  box-shadow: 
    inset 0 1px 0 rgba(255, 255, 255, 0.1),
    0 1px 3px rgba(0, 0, 0, 0.05);
}

.station-input::placeholder, .time-input::placeholder, .date-input::placeholder {
  color: rgba(255, 255, 255, 0.5);
  font-weight: 400;
}

.station-input:focus, .time-input:focus, .date-input:focus {
  outline: none;
  border-color: rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.12);
  box-shadow: 
    0 0 0 4px rgba(255, 255, 255, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.15),
    0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

/* Styles pour les dots de station */
.station-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 8px;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.station-dot.orange {
  background: linear-gradient(135deg, #FF9800, #F57C00);
  box-shadow: 0 2px 8px rgba(255, 152, 0, 0.3);
}

.station-dot.purple {
  background: linear-gradient(135deg, #9C27B0, #7B1FA2);
  box-shadow: 0 2px 8px rgba(156, 39, 176, 0.3);
}

/* Styles pour le bouton de recherche principal - Apple Style */
.primary-search-button {
  width: 100%;
  padding: 20px 24px;
  background: linear-gradient(135deg, #007AFF, #0056D6);
  color: white;
  border: none;
  border-radius: 16px;
  font-size: 19px;
  font-weight: 700;
  letter-spacing: -0.4px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  box-shadow: 
    0 6px 20px rgba(0, 122, 255, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 24px;
  position: relative;
  overflow: hidden;
}

.primary-search-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), transparent 50%, rgba(255, 255, 255, 0.05));
  border-radius: 16px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.primary-search-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #0056D6, #003D9F);
  transform: translateY(-2px);
  box-shadow: 
    0 8px 25px rgba(0, 122, 255, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.25);
}

.primary-search-button:hover:not(:disabled)::before {
  opacity: 1;
}

.primary-search-button:active:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 
    0 4px 15px rgba(0, 122, 255, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

.primary-search-button:disabled {
  background: rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.5);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.button-icon {
  font-size: 18px;
}

/* Styles pour la grille d'outils - Apple Style */
.tools-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.tool-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 18px 12px;
  background: rgba(255, 255, 255, 0.08);
  border: 0.5px solid rgba(255, 255, 255, 0.15);
  border-radius: 14px;
  color: rgba(255, 255, 255, 0.9);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
    font-size: 16px;
  font-weight: 700;
  letter-spacing: -0.3px;
  backdrop-filter: blur(20px);
  box-shadow: 
    inset 0 1px 0 rgba(255, 255, 255, 0.1),
    0 1px 3px rgba(0, 0, 0, 0.05);
  position: relative;
  overflow: hidden;
}

.tool-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), transparent 50%, rgba(255, 255, 255, 0.02));
  border-radius: 14px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.tool-button:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.25);
  transform: translateY(-1px);
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
  color: rgba(255, 255, 255, 0.95);
}

.tool-button:hover::before {
  opacity: 1;
}

.tool-button:active {
  transform: translateY(0);
  box-shadow: 
    0 2px 6px rgba(0, 0, 0, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.tool-text {
  font-weight: 700;
  letter-spacing: -0.3px;
}

/* Responsive pour le panneau unifié */
@media (max-width: 768px) {
  .unified-control-panel {
    width: calc(100vw - 40px);
    left: 20px;
    right: 20px;
    max-width: 420px;
  }
  
  .tools-grid {
    grid-template-columns: repeat(4, 1fr);
  }
  
  .tool-button {
    padding: 12px 8px;
    font-size: 10px;
  }
  
  .tool-icon {
    font-size: 16px;
  }
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: linear-gradient(135deg, rgba(89, 95, 207, 0.95), rgba(81, 171, 187, 0.95));
  backdrop-filter: blur(20px);
  padding: 24px;
  border-radius: 20px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
  max-width: 400px;
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.25);
  color: white;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
  padding-bottom: 16px;
}

.modal-header h3 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  color: white;
}

.close-button {
  font-size: 24px;
  background: none;
  border: none;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.8);
  border-radius: 50%;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.close-button:hover {
  background: rgba(255, 255, 255, 0.1);
  color: white;
}

.modal-body {
  margin-bottom: 20px;
}

.modal-button {
  width: 100%;
  padding: 12px 20px;
  background: linear-gradient(135deg, #4CAF50, #45a049);
  color: white;
  border: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-top: 16px;
}

.modal-button:hover:not(:disabled) {
  background: linear-gradient(135deg, #45a049, #3d8b40);
  transform: translateY(-1px);
}

.modal-button:disabled {
  background: rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.6);
  cursor: not-allowed;
}

.connexity-results {
  margin-top: 16px;
    padding: 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  color: rgba(255, 255, 255, 0.95);
}

.result-label {
  font-weight: 600;
  font-size: 14px;
}

.result-value {
  font-weight: 500;
  font-size: 14px;
}

.result-value.connected {
  color: #4CAF50;
  font-weight: 600;
}
</style>


