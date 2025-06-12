<template>
  <div class="map-container">
    <div class="control-panel">
      <h2>Recherche d'itinéraire</h2>
      <div class="search-group">
        <div class="search-input">
          <input
            type="text"
            v-model="searchStart"
            @input="searchStation(searchStart)"
            placeholder="Station de départ"
            list="stations-list"
          />
          <datalist id="stations-list">
            <option v-for="station in allStations" :key="station.id" :value="station.name">
              {{ station.name }}
            </option>
          </datalist>
          <div v-if="searchResults.length > 0 && searchStart" class="search-results">
            <div
              v-for="station in searchResults"
              :key="station.id"
              @click="selectStationFromSearch(station, true)"
              class="search-result-item"
            >
              {{ station.name }}
            </div>
          </div>
        </div>
        <div class="search-input">
          <input
            type="text"
            v-model="searchEnd"
            @input="searchStation(searchEnd)"
            placeholder="Station d'arrivée"
            list="stations-list"
          />
          <div v-if="searchResults.length > 0 && searchEnd" class="search-results">
            <div
              v-for="station in searchResults"
              :key="station.id"
              @click="selectStationFromSearch(station, false)"
              class="search-result-item"
            >
              {{ station.name }}
            </div>
          </div>
        </div>
      </div>
      <div class="control-group">
        <button 
          @click="toggleACPM" 
          :class="{ active: showACPM }"
        >
          {{ showACPM ? 'Masquer ACPM' : 'Afficher ACPM' }}
        </button>
        <button 
          @click="clearPath" 
          :disabled="!selectedStart || !selectedEnd"
        >
          Effacer le trajet
        </button>
        <button @click="debugPolylines">
          Debug Polylines
        </button>
      </div>
      <div v-if="selectedStart && selectedEnd" class="path-info">
        <h3>Itinéraire</h3>
        <div class="path-details">
          <div v-for="(segment, index) in pathDetails" :key="index" class="path-segment">
            <div class="segment-header" :style="{ backgroundColor: LINE_COLORS[segment.line] }">
              <span class="line-number">Ligne {{ segment.line }}</span>
              <span class="segment-duration">{{ formatTime(segment.duration) }}</span>
            </div>
            <div class="segment-stations">
              <div v-for="(station, stationIndex) in segment.stations" 
                   :key="stationIndex"
                   class="station-name"
                   :class="{ 
                     'transfer': stationIndex > 0 && stationIndex < segment.stations.length - 1,
                     'correspondance': stationIndex > 0 && stationIndex < segment.stations.length - 1 && 
                                     (index > 0 || stationIndex > 0)
                   }">
                <span class="station-dot" :style="{ backgroundColor: LINE_COLORS[segment.line] }"></span>
                {{ station }}
                <span v-if="stationIndex === 0" class="station-type">Départ</span>
                <span v-else-if="stationIndex === segment.stations.length - 1" class="station-type">Arrivée</span>
                <span v-else-if="stationIndex > 0 && stationIndex < segment.stations.length - 1" class="station-type">Correspondance</span>
              </div>
            </div>
          </div>
        </div>
        <div class="total-duration">
          Durée totale : {{ formatTime(pathLength) }}
        </div>
      </div>
    </div>
    <l-map
      ref="map"
      v-model:zoom="zoom"
      :center="center"
      :use-global-leaflet="false"
      :crs="crs"
      :min-zoom="minZoom"
      :max-zoom="maxZoom"
      :max-bounds="bounds"
      :max-bounds-viscosity="1.0"
    >
      <l-image-overlay
        url="/metrof_r.png"
        :bounds="bounds"
        :opacity="0.6"
      />
      <l-marker
        v-for="station in stations"
        :key="station.id"
        :lat-lng="getLatLng(station)"
        @mouseover="hoveredStation = station.id"
        @mouseout="hoveredStation = null"
        @click="selectStation(station)"
      >
        <l-tooltip v-if="hoveredStation === station.id">
          {{ station.name }}
        </l-tooltip>
        <l-icon
          :icon-url="getIconUrl(station)"
          :icon-size="[10, 10]"
          :icon-anchor="[5, 5]"
        />
      </l-marker>
      <l-polyline
        v-for="(path, index) in acpmPath"
        :key="'acpm-' + index"
        :lat-lngs="path.path"
        :color="path.color"
        :weight="path.weight || 5"
        :opacity="path.opacity || 0.9"
      />
      <l-polyline
        v-if="shortestPath.length > 0"
        v-for="(segment, index) in shortestPath"
        :key="'path-' + index"
        :lat-lngs="segment.path"
        :color="segment.color"
        :weight="segment.weight || 6"
        :opacity="segment.opacity || 1.0"
      />
      <l-polyline
        v-if="debugPath.length > 0"
        :lat-lngs="debugPath"
        color="red"
        :weight="7"
        :opacity="1.0"
      />
    </l-map>
  </div>
</template>

<script setup>
import { ref, onMounted, inject } from 'vue'
import { LMap, LTileLayer, LMarker, LTooltip, LIcon, LPolyline, LImageOverlay } from '@vue-leaflet/vue-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import { api } from '../services/api'

const stations = ref([])
const hoveredStation = ref(null)
const selectedStart = ref(null)
const selectedEnd = ref(null)
const zoom = ref(-1)
const center = ref([476, 488])
const showACPM = ref(false)
const acpmPath = ref([])
const shortestPath = ref([])
const pathLength = inject('pathLength')
const searchStart = ref('')
const searchEnd = ref('')
const searchResults = ref([])
const allStations = ref([])
const pathDetails = inject('pathDetails')
const debugPath = ref([])

// Configuration de la carte personnalisée
const crs = L.CRS.Simple
const minZoom = -2
const maxZoom = 2

// Dimensions exactes de l'image
const IMAGE_WIDTH = 987
const IMAGE_HEIGHT = 952

// Ajustements pour le padding et les marges
const PADDING_X = 40
const PADDING_Y = 40

// Ajustements pour le décalage
const OFFSET_X = -34  // Décalage vers la gauche
const OFFSET_Y = -4   // Décalage vers le bas

// Bounds de la carte avec padding
const bounds = [
  [0, 0],
  [IMAGE_HEIGHT + PADDING_Y, IMAGE_WIDTH + PADDING_X]
]

// Constantes pour la conversion des coordonnées
const X_MIN = 69
const X_MAX = 907
const Y_MIN = 69
const Y_MAX = 933

// Mapping des couleurs pour les lignes de métro
const LINE_COLORS = {
  '1': '#FFCD00',  // Jaune
  '2': '#003CA6',  // Bleu
  '3': '#837902',  // Marron
  '3bis': '#6EC4E8', // Bleu clair
  '4': '#CF009E',  // Rose
  '5': '#FF7E2E',  // Orange
  '6': '#6ECA97',  // Vert clair
  '7': '#F59FB3',  // Rose clair
  '7bis': '#82C8E6', // Bleu ciel
  '8': '#E19BDF',  // Violet clair
  '9': '#B6BD00',  // Vert olive
  '10': '#C9910D', // Orange foncé
  '11': '#704B1C', // Marron clair
  '12': '#007852', // Vert foncé
  '13': '#6EC4E8', // Bleu clair
  '14': '#62259D'  // Violet
}

// Charger les stations depuis l'API
async function fetchStations() {
  try {
    const res = await fetch('http://localhost:5050/stations')
    const data = await res.json()
    
    // S'assurer que chaque station a une position valide et ajouter la ligne
    stations.value = data.stations.filter(s => s.position && Array.isArray(s.position) && s.position.length === 2)
      .map(station => {
        // Pour la couleur, on prend la première ligne de la station
        const line = Array.isArray(station.lines) && station.lines.length > 0 
          ? station.lines[0] 
          : '1'; // Ligne 1 par défaut
        
        return {
          ...station,
          line: line // Ajouter la propriété line pour faciliter l'accès
        };
      });
    
    console.log("Stations chargées:", stations.value.length)
    console.log("Exemple de station:", stations.value[0])
  } catch (error) {
    console.error('Erreur lors du chargement des stations:', error)
  }
}

// Charger l'ACPM depuis l'API
async function fetchACPM() {
  try {
    console.log("Chargement de l'ACPM...")
    const res = await fetch('http://localhost:5050/acpm')
    const data = await res.json()
    console.log("Données ACPM reçues:", data)
    
    acpmPath.value = data.mst.map(edge => {
      console.log("Traitement de l'arête:", edge)
      
      // Utiliser des noms au lieu des IDs
      const fromStation = stations.value.find(s => s.name === edge.from.name)
      const toStation = stations.value.find(s => s.name === edge.to.name)
      
      console.log("Stations trouvées:", fromStation?.name, toStation?.name)
      
      if (fromStation && toStation && fromStation.position && toStation.position) {
        console.log("Coordonnées:", 
                   "from:", fromStation.position, 
                   "to:", toStation.position)
        
        // Déterminer la ligne - utiliser la ligne de la première station
        const line = fromStation.line || '1'
        const color = LINE_COLORS[line] || '#000000'
        
        console.log(`Ligne: ${line}, Couleur: ${color}`)
        
        const path = {
          path: [getLatLng(fromStation), getLatLng(toStation)],
          color: color,
          weight: 6,
          opacity: 0.9,
          lineCap: 'round',
          lineJoin: 'round'
        }
        console.log("Segment créé:", path)
        return path
      }
      console.warn("Stations non trouvées pour l'arête:", edge)
      return null
    }).filter(path => path !== null)
    
    console.log("ACPM tracé avec", acpmPath.value.length, "segments")
  } catch (error) {
    console.error("Erreur lors du chargement de l'ACPM:", error)
    acpmPath.value = []
  }
}

// Charger toutes les stations uniques depuis notre nouvelle API
async function fetchAllStations() {
  try {
    const res = await api.getStationsList()
    allStations.value = res.stations
    console.log("Toutes les stations chargées:", allStations.value.length)
  } catch (error) {
    console.error('Erreur lors du chargement des stations:', error)
  }
}

// Rechercher une station par nom (une seule fois par nom)
function searchStation(query) {
  if (!query) {
    searchResults.value = []
    return
  }
  searchResults.value = allStations.value
    .filter(station => 
      station.name.toLowerCase().includes(query.toLowerCase())
    )
    .slice(0, 5) // Limiter à 5 résultats
}

// Sélectionner une station depuis les résultats de recherche
function selectStationFromSearch(station, isStart) {
  if (isStart) {
    selectedStart.value = station.name // Utiliser le nom de la station comme identifiant
    searchStart.value = station.name
  } else {
    selectedEnd.value = station.name // Utiliser le nom de la station comme identifiant
    searchEnd.value = station.name
  }
  searchResults.value = []
  if (selectedStart.value && selectedEnd.value) {
    calculatePath()
  }
}

function toggleACPM() {
  showACPM.value = !showACPM.value
  if (showACPM.value) {
    fetchACPM()
  } else {
    acpmPath.value = []
  }
}

function clearPath() {
  selectedStart.value = null
  selectedEnd.value = null
  searchStart.value = ''
  searchEnd.value = ''
  shortestPath.value = []
  pathDetails.value = []
  pathLength.value = null
}

function getStationName(stationId) {
  const station = stations.value.find(s => s.id === stationId)
  return station ? station.name : ''
}

function getLatLng(station) {
  // Gérer différents formats de station
  let x, y;
  
  if (station.position) {
    // Format [x, y]
    [x, y] = station.position;
  } else if (station.x !== undefined && station.y !== undefined) {
    // Format { x, y }
    x = station.x;
    y = station.y;
  } else {
    // Format non reconnu, utiliser des valeurs par défaut
    console.warn("Format de station non reconnu:", station);
    return [0, 0];
  }
  
  // Ajustement des coordonnées pour correspondre à la carte
  const scaleX = IMAGE_WIDTH / (X_MAX - X_MIN);
  const scaleY = IMAGE_HEIGHT / (Y_MAX - Y_MIN);
  
  // Calcul des coordonnées normalisées avec ajustement
  const normalizedX = (x - X_MIN) * scaleX + PADDING_X/2 + OFFSET_X;
  const normalizedY = (Y_MAX - y) * scaleY + PADDING_Y/2 + OFFSET_Y;
  
  // Ajustement fin pour correspondre exactement à la carte
  const finalX = normalizedX * 1.02; // Légère expansion horizontale
  const finalY = normalizedY * 1.02; // Légère expansion verticale
  
  return [finalY, finalX];
}

function getIconUrl(station) {
  if (selectedStart.value === station.name) {
    return 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 8 8"><circle cx="4" cy="4" r="4" fill="green"/></svg>'
  } else if (selectedEnd.value === station.name) {
    return 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 8 8"><circle cx="4" cy="4" r="4" fill="red"/></svg>'
  }
  return 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 8 8"><circle cx="4" cy="4" r="4" fill="black"/></svg>'
}

function selectStation(station) {
  if (!selectedStart.value) {
    selectedStart.value = station.name
    searchStart.value = station.name
  } else if (!selectedEnd.value && station.name !== selectedStart.value) {
    selectedEnd.value = station.name
    searchEnd.value = station.name
    calculatePath()
  } else {
    selectedStart.value = station.name
    searchStart.value = station.name
    selectedEnd.value = null
    searchEnd.value = ''
    shortestPath.value = []
    pathDetails.value = []
    pathLength.value = null
  }
}

async function calculatePath() {
    if (!selectedStart.value || !selectedEnd.value) return

    try {
        // Utiliser directement les noms de stations sélectionnées
        console.log("Calcul d'itinéraire entre:", selectedStart.value, "et", selectedEnd.value)

        const response = await api.calculateItinerary(
            selectedStart.value,
            selectedEnd.value
        )

        console.log("Réponse de l'API:", response)
        console.log("Durée totale en secondes:", response.total_time)

        // Mise à jour des détails du chemin avec regroupement par ligne
        const segments = []
        let currentSegment = null

        for (let i = 0; i < response.path.length; i++) {
            const step = response.path[i]
            const nextStep = response.path[i + 1]

            if (!currentSegment || currentSegment.line !== step.line) {
                if (currentSegment) {
                    segments.push(currentSegment)
                }
                currentSegment = {
                    line: step.line,
                    stations: [step.name],
                    duration: 0
                }
            } else {
                currentSegment.stations.push(step.name)
            }

            // Ajouter le temps réel entre les stations
            if (nextStep && step.time) {
                currentSegment.duration += step.time
            }
        }

        if (currentSegment) {
            segments.push(currentSegment)
        }

        pathDetails.value = segments

        // Remettre à zéro le chemin sur la carte
        shortestPath.value = []
        
        // Regrouper les segments par ligne pour l'affichage
        let currentLine = null
        let currentPathSegment = null
        
        for (let i = 0; i < response.path.length - 1; i++) {
            const current = response.path[i]
            const next = response.path[i + 1]
            
            if (!current || !next) continue
            
            try {
                // Convertir les coordonnées
                const latLngA = getLatLng({ x: current.x, y: current.y })
                const latLngB = getLatLng({ x: next.x, y: next.y })
                
                // Déterminer si c'est un nouveau segment de ligne
                if (current.line !== currentLine) {
                    currentLine = current.line
                    
                    // Créer un nouveau segment pour cette ligne
                    currentPathSegment = {
                        path: [latLngA, latLngB],
                        color: LINE_COLORS[current.line] || '#000000',
                        weight: 7,
                        opacity: 1.0,
                        lineCap: 'round',
                        lineJoin: 'round'
                    }
                    
                    shortestPath.value.push(currentPathSegment)
                } else {
                    // Continuer le segment existant
                    if (currentPathSegment) {
                        currentPathSegment.path.push(latLngB)
                    }
                }
            } catch (error) {
                console.error(`Erreur lors de la création du segment ${i}:`, error)
            }
        }

        // Mise à jour de la durée totale
        pathLength.value = response.total_time
        
        console.log("Temps total en secondes:", pathLength.value)

    } catch (error) {
        console.error('Erreur lors du calcul de l\'itinéraire:', error)
        // Réinitialiser les valeurs en cas d'erreur
        shortestPath.value = []
        pathDetails.value = []
        pathLength.value = null
    }
}

// Fonction pour formater le temps en minutes et secondes
function formatTime(seconds) {
    if (!seconds) return '0m 0s'
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = Math.round(seconds % 60)
    return `${minutes}m ${remainingSeconds}s`
}

function debugPolylines() {
  console.log("Debug polylines")
  console.log("ACPM paths:", acpmPath.value)
  console.log("Shortest path:", shortestPath.value)
  
  // Créer un chemin de test simple
  const center1 = [IMAGE_HEIGHT/2 - 100, IMAGE_WIDTH/2 - 100]
  const center2 = [IMAGE_HEIGHT/2 + 100, IMAGE_WIDTH/2 + 100]
  
  // Chemin de test visible au centre de la carte
  debugPath.value = [center1, center2]
  
  console.log("Debug path créé:", debugPath.value)
  
  // Affichons aussi les limites de la carte
  console.log("Bounds de la carte:", bounds)
  console.log("Center:", center.value)
  console.log("Zoom:", zoom.value)
  
  // Ajoutons un segment de test dans shortestPath
  shortestPath.value.push({
    path: [center1, center2],
    color: '#FF0000',
    weight: 10,
    opacity: 1.0
  })
}

onMounted(async () => {
  try {
    console.log("Initialisation du composant")
    await fetchAllStations()
    await fetchStations()
    console.log("Initialisation terminée")
  } catch (error) {
    console.error("Erreur lors de l'initialisation:", error)
  }
})
</script>

<style scoped>
.map-container {
  width: 100%;
  height: 100vh;
  border: 1px solid #ccc;
  border-radius: 4px;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 1;
  overflow: hidden;
}

.control-panel {
  position: absolute;
  top: 20px;
  right: 20px;
  background: white;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  z-index: 1000;
  min-width: 200px;
}

.control-panel h2 {
  margin: 0 0 15px 0;
  font-size: 1.2em;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

button {
  padding: 8px 12px;
  border: none;
  border-radius: 4px;
  background: #4CAF50;
  color: white;
  cursor: pointer;
  transition: background 0.3s;
}

button:hover {
  background: #45a049;
}

button:disabled {
  background: #cccccc;
  cursor: not-allowed;
}

button.active {
  background: #2196F3;
}

.path-info {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #eee;
}

.path-info p {
  margin: 5px 0;
  font-size: 0.9em;
}

:deep(.leaflet-container) {
  background: transparent;
}

:deep(.leaflet-control-container) {
  display: none;
}

.search-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 15px;
}

.search-input {
  position: relative;
}

.search-input input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 14px;
  background-color: white;
}

.search-input input:focus {
  outline: none;
  border-color: #4CAF50;
  box-shadow: 0 0 0 2px rgba(76, 175, 80, 0.2);
}

.search-results {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #ccc;
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 1000;
}

.search-result-item {
  padding: 8px;
  cursor: pointer;
}

.search-result-item:hover {
  background-color: #f0f0f0;
}

.station-name {
  display: flex;
  align-items: center;
  padding: 0.5rem 0;
  border-bottom: 1px solid #eee;
  gap: 0.5rem;
}

.station-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 0.5rem;
}

.station-type {
  font-size: 0.8em;
  color: #666;
  margin-left: auto;
  font-style: italic;
}

.station-name.correspondance {
  background-color: #f5f5f5;
  padding-left: 1rem;
}

.segment-header {
  padding: 0.75rem 1rem;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.segment-duration {
  background: rgba(255, 255, 255, 0.2);
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.9em;
}

.path-details {
  position: absolute;
  top: 100px;
  left: 10px;
  background-color: white;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  z-index: 1000;
  max-width: 300px;
  max-height: 70vh;
  overflow-y: auto;
}

.path-details h3 {
  margin-top: 0;
  margin-bottom: 10px;
}

.total-time {
  font-weight: bold;
  margin-bottom: 15px;
  font-size: 1.1em;
}

.path-segment {
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #eee;
}

.path-segment:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.segment-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.line-indicator {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  margin-right: 10px;
}

.segment-info {
  flex: 1;
}

.segment-time {
  font-weight: bold;
  font-size: 0.9em;
}

.segment-stations {
  margin-left: 40px;
  font-size: 0.9em;
  color: #555;
}

.stations-ellipsis {
  margin: 3px 0;
  color: #999;
}
</style> 