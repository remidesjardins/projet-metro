```vue
<template>
  <div class="map-container">
    <div class="liquid-glass-panel">
      <div class="content-wrapper">
        <div class="search-section">
          <div class="search-label">From</div>
          <div class="search-input-wrapper">
            <div class="station-dot orange"></div>
            <input
              type="text"
              v-model="searchStart"
              @input="searchStationStart(searchStart)"
              @focus="isStartFocused = true"
              @blur="setTimeout(() => isStartFocused = false, 150)"
              placeholder="Station de départ"
              class="glass-input"
            />
            <div class="chevron-icon"></div>
            <div v-if="isStartFocused && searchResultsStart.length > 0 && searchStart" class="search-results">
              <div
                v-for="station in searchResultsStart"
                :key="station.id"
                @mousedown.prevent="selectStationFromSearch(station, true)"
                class="search-result-item"
              >
                {{ station.name }}
              </div>
            </div>
          </div>

          <div class="search-label">To</div>
          <div class="search-input-wrapper">
            <div class="station-dot purple"></div>
            <input
              type="text"
              v-model="searchEnd"
              @input="searchStationEnd(searchEnd)"
              @focus="isEndFocused = true"
              @blur="setTimeout(() => isEndFocused = false, 150)"
              placeholder="Station d'arrivée"
              class="glass-input"
            />
            <div class="chevron-icon"></div>
            <div v-if="isEndFocused && searchResultsEnd.length > 0 && searchEnd" class="search-results">
              <div
                v-for="station in searchResultsEnd"
                :key="station.id"
                @mousedown.prevent="selectStationFromSearch(station, false)"
                class="search-result-item"
              >
                {{ station.name }}
              </div>
            </div>
          </div>
        </div>

        <div class="control-actions">
          <button
            @click="toggleACPM"
            :class="{ 'active': showACPM }"
            class="acpm-button"
          >
            {{ showACPM ? 'Hide ACPM' : 'Display ACPM' }}
          </button>
          <transition name="fade-scale">
            <div v-if="showACPM && acpmTotalWeight !== null" class="acpm-refined-badge-wrap">
              <div :class="['acpm-refined-badge', { 'is-animating': acpmAnimating }]">
                <span class="acpm-refined-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <polyline points="12 6 12 12 16 14"></polyline>
                  </svg>
                </span>
                <div class="acpm-refined-value-wrapper">
                  <transition-group name="slide-up-num" tag="span">
                    <span :key="acpmAnimatedWeight" class="acpm-refined-anim-value">{{ formatSecondsToHMS(acpmAnimatedWeight) }}</span>
                  </transition-group>
                </div>
              </div>
            </div>
          </transition>

          <button
            v-if="selectedStart && selectedEnd"
            @click="clearPath"
            class="clear-button"
          >
            Effacer le trajet
          </button>
          <button class="acpm-button secondary" @click="handleTestConnexity" style="margin-top:8px;">
            Tester la connexité
          </button>
          <button class="acpm-button secondary" @click="toggleLines" style="margin-top:8px;">
            {{ showLines ? 'Masquer les lignes' : 'Afficher les lignes' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Carte remplaçant l'image par OpenStreetMap -->
    <l-map
      ref="map"
      v-model:zoom="zoom"
      :center="center"
      :use-global-leaflet="false"
      class="metro-map"
    >
      <!-- Utilisation de OpenStreetMap -->
      <l-tile-layer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        layer-type="base"
        name="OpenStreetMap"
      />

      <!-- Tracé des lignes de métro -->
      <l-polyline
        v-if="showLines"
        v-for="(line, idx) in linesPolylines"
        :key="'line-polyline-' + line.line"
        :lat-lngs="line.path"
        :color="line.color"
        :weight="6"
        :opacity="0.85"
        :line-cap="'round'"
        :line-join="'round'"
      />

      <!-- Les markers et lignes restent affichés -->
      <l-marker
        v-for="station in stations"
        :key="station.id"
        :lat-lng="getLatLng(station)"
        @mouseover="hoveredStation = station.id"
        @mouseout="hoveredStation = null"
        @click="selectStation(station)"
      >
        <l-tooltip v-if="hoveredStation === station.id" direction="top" :permanent="false" class="station-tooltip-custom">
          <div class="station-tooltip-title">{{ station.name }}</div>
          <div class="station-tooltip-lines">
            <span v-for="line in station.lines" :key="line" class="line-badge" :style="{ backgroundColor: LINE_COLORS[line] || '#1976d2' }">{{ line }}</span>
          </div>
        </l-tooltip>
        <l-icon
          :icon-url="getIconUrl(station)"
          :icon-size="[28, 28]"
          :icon-anchor="[14, 14]"
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
        :weight="segment.weight"
        :opacity="segment.opacity"
        :line-cap="segment.lineCap"
        :line-join="segment.lineJoin"
        :class="segment.className"
      />
      <l-polyline
        v-if="debugPath.length > 0"
        :lat-lngs="debugPath"
        color="red"
        :weight="7"
        :opacity="1.0"
      />
    </l-map>

    <!-- Légende des lignes -->
    <div class="legend-lines">
      <div v-for="(color, line) in LINE_COLORS" :key="line" class="legend-line-item">
        <span class="legend-line-badge" :style="{ backgroundColor: color }">{{ line }}</span>
        <span class="legend-line-label">Ligne {{ line }}</span>
      </div>
    </div>

    <!-- Modal Connexité -->
    <div v-if="showConnexityModal" class="connexity-modal-bg" @click.self="closeConnexityModal">
      <div class="connexity-modal-glass">
        <button class="close-modal-btn" @click="closeConnexityModal">&times;</button>
        <h2>Test de connexité</h2>
        <div v-if="connexityLoading" class="connexity-loading">Vérification en cours...</div>
        <div v-else-if="connexityError" class="connexity-error">{{ connexityError }}</div>
        <div v-else-if="connexityResult">
          <div class="connexity-status" :class="{connected: connexityResult.is_connected, disconnected: !connexityResult.is_connected}">
            <span v-if="connexityResult.is_connected">Le graphe est <b>connexe</b></span>
            <span v-else>Le graphe n'est <b>pas connexe</b> </span>
          </div>
          <div class="connexity-details">
            <div>Nombre de composantes : <b>{{ connexityResult.components_count }}</b></div>
            <div v-if="connexityResult.components && connexityResult.components.length">
              <div style="margin-top:8px;">Composantes non connexes :</div>
              <ul>
                <li v-for="(comp, idx) in connexityResult.components" :key="idx">
                  {{ comp.join(', ') }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, inject, watch } from 'vue'
import { LMap, LMarker, LTooltip, LIcon, LPolyline, LImageOverlay, LTileLayer } from '@vue-leaflet/vue-leaflet'
import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import { api } from '../services/api'

// Fix de l'icône Leaflet
import { nextTick } from 'vue';
import iconRetinaUrl from 'leaflet/dist/images/marker-icon-2x.png';
import iconUrl from 'leaflet/dist/images/marker-icon.png';
import shadowUrl from 'leaflet/dist/images/marker-shadow.png';

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl,
  iconUrl,
  shadowUrl,
});

const stations = ref([])
const hoveredStation = ref(null)
const selectedStart = ref(null)
const selectedEnd = ref(null)
const startId = ref(null)
const endId = ref(null)
const zoom = ref(13)
const center = ref([48.8566, 2.3522])
const showACPM = ref(false)
const acpmPath = ref([])
const shortestPath = ref([])
const searchStart = ref('')
const searchEnd = ref('')
const searchResultsStart = ref([])
const searchResultsEnd = ref([])
const isStartFocused = ref(false)
const isEndFocused = ref(false)
const allStations = ref([])
const pathDetails = inject('pathDetails')
const debugPath = ref([])
const map = ref(null)
const showConnexityModal = ref(false)
const connexityResult = ref(null)
const connexityLoading = ref(false)
const connexityError = ref(null)
const showLines = ref(false)
const linesPolylines = ref([])
const acpmTotalWeight = ref(null)
const acpmAnimatedWeight = ref(0)
const acpmAnimating = ref(false)

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

// Charger les stations depuis l'API
async function fetchStations() {
  try {
    const res = await fetch('http://localhost:5050/stations', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include'
    })
    const data = await res.json()
    console.log(data)

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
  } catch (error) {
    console.error('Erreur lors du chargement des stations:', error)
  }
}

// Charger l'ACPM depuis l'API
async function fetchACPM() {
  try {
    const res = await fetch('http://localhost:5050/acpm')
    const data = await res.json()
    acpmTotalWeight.value = data.total_weight
    acpmPath.value = data.mst.map(edge => {
      // Utiliser des noms au lieu des IDs
      const fromStation = stations.value.find(s => s.name === edge.from.name)
      const toStation = stations.value.find(s => s.name === edge.to.name)

      if (fromStation && toStation && fromStation.position && toStation.position) {
        // Déterminer la ligne - utiliser la ligne de la première station
        const line = fromStation.line || '1'
        const color = LINE_COLORS[line] || '#000000'

        const path = {
          path: [getLatLng(fromStation), getLatLng(toStation)],
          color: color,
          weight: 5,
          opacity: 1,
          lineCap: 'round',
          lineJoin: 'round'
        }
        return path
      }
      return null
    }).filter(path => path !== null)
  } catch (error) {
    console.error("Erreur lors du chargement de l'ACPM:", error)
    acpmPath.value = []
    acpmTotalWeight.value = null
  }
}

// Charger toutes les stations uniques depuis notre nouvelle API
async function fetchAllStations() {
  try {
    const res = await api.getStationsList()
    allStations.value = res.stations
  } catch (error) {
    console.error('Erreur lors du chargement des stations:', error)
  }
}

function searchStationStart(query) {
  if (!query) {
    searchResultsStart.value = []
    return
  }
  searchResultsStart.value = allStations.value
    .filter(station => station.name.toLowerCase().includes(query.toLowerCase()))
    .slice(0, 5)
}

function searchStationEnd(query) {
  if (!query) {
    searchResultsEnd.value = []
    return
  }
  searchResultsEnd.value = allStations.value
    .filter(station => station.name.toLowerCase().includes(query.toLowerCase()))
    .slice(0, 5)
}

function selectStationFromSearch(station, isStart) {
  if (isStart) {
    selectedStart.value = station.name
    searchStart.value = station.name
    startId.value = station.ids[0]
    searchResultsStart.value = []
    isStartFocused.value = false
  } else {
    selectedEnd.value = station.name
    searchEnd.value = station.name
    endId.value = station.ids[0]
    searchResultsEnd.value = []
    isEndFocused.value = false
  }
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

  return [x/1000, y/1000];
}

function getStationType(station) {
  // Détecte si la station est une correspondance ou un terminus
  if (station.lines && station.lines.length > 1) return 'correspondance';
  if (station.isTerminus || station.terminus) return 'terminus';
  return 'simple';
}

function getIconUrl(station) {
  const line = Array.isArray(station.lines) && station.lines.length > 0 ? station.lines[0] : '1';
  const color = LINE_COLORS[line] || '#1976d2';
  let radius = 7, stroke = 3, glow = '', fill = color, strokeColor = 'white';
  // Détection du type de station
  if (station.lines && station.lines.length > 1) {
    radius = 7; stroke = 3; // même taille que les stations simples
    fill = '#fff'; // correspondance = point blanc
    strokeColor = 'black'; // contour noir pour correspondance
    glow = `<filter id='glow' x='-50%' y='-50%' width='200%' height='200%'><feGaussianBlur stdDeviation='3' result='coloredBlur'/><feMerge><feMergeNode in='coloredBlur'/><feMergeNode in='SourceGraphic'/></feMerge></filter>`;
  } else if (station.isTerminus || station.terminus) {
    radius = 12; stroke = 5;
    glow = `<filter id='glow' x='-50%' y='-50%' width='200%' height='200%'><feGaussianBlur stdDeviation='4' result='coloredBlur'/><feMerge><feMergeNode in='coloredBlur'/><feMergeNode in='SourceGraphic'/></feMerge></filter>`;
  }
  // Encodage du SVG, attention au # dans filter
  const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='28' height='28' viewBox='0 0 28 28'>${glow}<circle cx='14' cy='14' r='${radius}' fill='${fill}' stroke='${strokeColor}' stroke-width='${stroke}'${glow ? " filter='url(%23glow)'" : ''}/></svg>`;
  return 'data:image/svg+xml;utf8,' + encodeURIComponent(svg);
}

function selectStation(station) {
  if (!selectedStart.value) {
    selectedStart.value = station.name
    searchStart.value = station.name
    startId.value = station.ids[0]
    } else if (!selectedEnd.value && station.name !== selectedStart.value) {
    selectedEnd.value = station.name
    searchEnd.value = station.name
    endId.value = station.ids[0]
    calculatePath()
  } else {
    selectedStart.value = station.name
    searchStart.value = station.name
    startId.value = station.ids[0]
    selectedEnd.value = null
    searchEnd.value = ''
    endId.value = null
    shortestPath.value = []
    pathDetails.value = []
  }
}

const pathLength = inject('pathLength')

async function calculatePath() {
    try {
        const response = await api.calculateItinerary(startId.value, endId.value)
        
        pathLength.value = {
            duration: response.duration,
            emissions: response.emissions,
            stationsCount: response.stations_count
        }
        
        const segments = response.chemin.map(ligneSegment => ({
            line: ligneSegment.Ligne,
            stations: ligneSegment.Stations.map(station => station["Nom Station"]),
            duration: ligneSegment.Duration,
            stationsCount: ligneSegment.Stations.length
        }))

        pathDetails.value = segments

        // Remettre à zéro le chemin sur la carte
        shortestPath.value = []

        // Créer les segments pour l'affichage sur la carte
        response.chemin.forEach((ligneSegment, segmentIndex) => {
            const ligne = ligneSegment.Ligne
            const stations = ligneSegment.Stations
            
            if (stations.length < 2) return // Pas assez de stations pour tracer une ligne

            const pathCoordinates = []
            
            // Convertir toutes les positions des stations de cette ligne
            stations.forEach(station => {
                if (station.Position && station.Position.length === 2) {
                    const latLng = getLatLng({ position: station.Position })
                    pathCoordinates.push(latLng)
                }
            })

            if (pathCoordinates.length >= 2) {
                shortestPath.value.push({
                    path: pathCoordinates,
                    color: LINE_COLORS[ligne] || '#000000',
                    weight: 8,
                    opacity: 1.0,
                    lineCap: 'round',
                    lineJoin: 'round',
                    className: 'route-main'
                })
            }
        })

    } catch (error) {
        console.error('Erreur lors du calcul:', error)
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
  // Créer un chemin de test simple
  const center1 = [IMAGE_HEIGHT/2 - 100, IMAGE_WIDTH/2 - 100]
  const center2 = [IMAGE_HEIGHT/2 + 100, IMAGE_WIDTH/2 + 100]

  // Chemin de test visible au centre de la carte
  debugPath.value = [center1, center2]

  // Ajoutons un segment de test dans shortestPath
  shortestPath.value.push({
    path: [center1, center2],
    color: '#FF0000',
    weight: 10,
    opacity: 1.0
  })
}

function initializeMap() {
  nextTick(() => {
    if (map.value) {
      map.value.invalidateSize();
    }
  });
}

async function handleTestConnexity() {
  connexityLoading.value = true
  connexityError.value = null
  try {
    const result = await api.testConnexity()
    connexityResult.value = result
    showConnexityModal.value = true
  } catch (e) {
    connexityError.value = e.message || 'Erreur inconnue'
    showConnexityModal.value = true
  } finally {
    connexityLoading.value = false
  }
}

function closeConnexityModal() {
  showConnexityModal.value = false
  connexityResult.value = null
  connexityError.value = null
}

function toggleLines() {
  showLines.value = !showLines.value
  if (showLines.value) {
    computeLinesPolylines()
  }
}

async function computeLinesPolylines() {
  try {
    const res = await fetch('http://localhost:5050/stations/ordered_by_line');
    const data = await res.json();
    // data: { ligne: [ [branche1], [branche2], ... ] }
    linesPolylines.value = [];
    Object.entries(data).forEach(([line, branches]) => {
      branches.forEach(branch => {
        linesPolylines.value.push({
          line,
          color: LINE_COLORS[line] || '#000',
          path: branch.map(s => [s.position[0] / 1000, s.position[1] / 1000]),
        });
      });
    });
  } catch (e) {
    linesPolylines.value = [];
    console.error('Erreur lors du chargement des lignes ordonnées:', e);
  }
}

function formatSecondsToHMS(seconds) {
  if (!seconds || isNaN(seconds)) return '0s';
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  return [
    h > 0 ? String(h).padStart(2, '0') : null,
    String(m).padStart(2, '0'),
    String(s).padStart(2, '0')
  ].filter(Boolean).join(':');
}

watch(acpmTotalWeight, (newVal) => {
  if (typeof newVal === 'number' && newVal > 0) {
    acpmAnimating.value = true
    let start = 0
    const duration = 1200 // ms
    const startTime = performance.now()
    function animate(now) {
      const elapsed = now - startTime
      const progress = Math.min(elapsed / duration, 1)
      acpmAnimatedWeight.value = Math.floor(progress * newVal)
      if (progress < 1) {
        requestAnimationFrame(animate)
      } else {
        acpmAnimatedWeight.value = newVal
        setTimeout(() => acpmAnimating.value = false, 600)
      }
    }
    requestAnimationFrame(animate)
  }
})

onMounted(async () => {
  try {
    await fetchAllStations();
    await fetchStations();

    // Initialiser la carte après le montage du composant
    initializeMap();
  } catch (error) {
    console.error("Erreur lors de l'initialisation:", error);
  }
})
</script>

<style scoped>
.map-container {
  width: 100vw;
  height: 100vh;
  position: fixed;
  top: 0;
  left: 0;
  overflow: hidden;
  z-index: 0;
}

.liquid-glass-panel {
  position: absolute;
  top: var(--spacing-xl);
  left: var(--spacing-xl);
  z-index: 1000;
  width: 400px;
  pointer-events: auto;
  border-radius: 40px;
  background: linear-gradient(135deg, rgba(89, 95, 207, 0.8), rgba(81, 171, 187, 0.8));
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.1),
    inset 0 0 0 1px rgba(255, 255, 255, 0.2);
  padding: 2px;
  overflow: hidden;
}

.content-wrapper {
  background: linear-gradient(145deg, rgba(61, 81, 181, 0.8), rgba(81, 162, 171, 0.8));
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border-radius: 38px;
  padding: var(--spacing-xl);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.search-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.search-label {
  font-size: 28px;
  font-weight: 600;
  color: white;
  margin-bottom: -8px;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.search-input-wrapper {
  position: relative;
  margin-top: 10px;
  margin-bottom: 15px;
}

.glass-input {
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
  border: none;
  border-radius: 25px;
  padding: 20px 50px;
  font-size: 20px;
  width: 100%;
  color: white;
  font-weight: 500;
  transition: all 0.3s ease;
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.2),
    0 4px 8px rgba(0, 0, 0, 0.1);
}

.glass-input::placeholder {
  color: rgba(255, 255, 255, 0.7);
}

.glass-input:focus {
  outline: none;
  background: rgba(255, 255, 255, 0.25);
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.3),
    0 4px 12px rgba(0, 0, 0, 0.15);
}

.station-dot {
  position: absolute;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  top: 50%;
  left: 15px;
  transform: translateY(-50%);
  z-index: 2;
}

.station-dot.orange {
  background: #FF9C41;
  box-shadow: 0 0 10px rgba(255, 156, 65, 0.5);
}

.station-dot.purple {
  background: #A15CFF;
  box-shadow: 0 0 10px rgba(161, 92, 255, 0.5);
}

.chevron-icon {
  position: absolute;
  width: 24px;
  height: 24px;
  top: 50%;
  right: 15px;
  transform: translateY(-50%);
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='white' stroke-width='2'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' d='M9 5l7 7-7 7'%3E%3C/path%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: center;
  opacity: 0.8;
}

.control-actions {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-top: var(--spacing-sm);
}

.acpm-button {
  background: linear-gradient(135deg, #4B7FFD, #59D8E9);
  color: white;
  border: none;
  border-radius: 30px;
  padding: 18px;
  font-size: 20px;
  font-weight: 600;
  width: 100%;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.15);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.acpm-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

.acpm-button:active {
  transform: translateY(0);
  box-shadow: 0 6px 15px rgba(0, 0, 0, 0.1);
}

.acpm-button.active {
  background: linear-gradient(135deg, #3A67DB, #4ABFCE);
}

.clear-button {
  background: rgba(255, 255, 255, 0.15);
  color: white;
  border: none;
  border-radius: 30px;
  padding: 12px;
  font-size: 16px;
  font-weight: 500;
  width: 100%;
  cursor: pointer;
  transition: all 0.2s ease;
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
}

.clear-button:hover {
  background: rgba(255, 255, 255, 0.2);
}

.search-results {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.9);
  border-radius: var(--radius-md);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  max-height: 200px;
  overflow-y: auto;
  z-index: 1000;
}

.search-result-item {
  padding: 15px 20px;
  cursor: pointer;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  color: #333;
  font-weight: 500;
}

.search-result-item:last-child {
  border-bottom: none;
}

.search-result-item:hover {
  background-color: rgba(0, 0, 0, 0.03);
}

.metro-map {
  height: 100vh;
  width: 100vw;
  position: absolute;
  top: 0;
  left: 0;
  z-index: 1;
}

:deep(.leaflet-container) {
  width: 100vw !important;
  height: 100vh !important;
  min-width: 100vw !important;
  min-height: 100vh !important;
  margin: 0 !important;
  padding: 0 !important;
  overflow: hidden !important;
  background: rgb(242, 242, 247);
}

:deep(.leaflet-control-container) {
  display: none;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .liquid-glass-panel {
    width: calc(100% - 32px);
    left: 16px;
    right: 16px;
    transform: none;
  }
}

:deep(.route-main) {
  stroke-opacity: 1 !important;
  filter: none !important;
}

.acpm-button.secondary {
  background: linear-gradient(135deg, #b1b5c9 0%, #7fd8e9 100%);
  color: #222;
  font-weight: 600;
  margin-top: 8px;
  border: none;
  border-radius: 30px;
  padding: 14px;
  font-size: 18px;
  width: 100%;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.acpm-button.secondary:hover {
  background: linear-gradient(135deg, #7fd8e9 0%, #b1b5c9 100%);
}

.connexity-modal-bg {
  position: fixed;
  z-index: 3000;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(30,40,60,0.25);
  display: flex;
  align-items: center;
  justify-content: center;
}
.connexity-modal-glass {
  min-width: 320px;
  max-width: 90vw;
  background: linear-gradient(135deg, rgba(89, 95, 207, 0.92), rgba(81, 171, 187, 0.92));
  border-radius: 32px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.18);
  padding: 36px 32px 28px 32px;
  position: relative;
  color: #fff;
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  border: 1.5px solid rgba(255,255,255,0.18);
  text-align: center;
  animation: fadeIn 0.25s;
}
@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.98); }
  to { opacity: 1; transform: scale(1); }
}
.close-modal-btn {
  position: absolute;
  top: 16px;
  right: 22px;
  background: none;
  border: none;
  color: #fff;
  font-size: 2rem;
  cursor: pointer;
  opacity: 0.7;
  transition: opacity 0.2s;
}
.close-modal-btn:hover {
  opacity: 1;
}
.connexity-status {
  font-size: 1.2rem;
  margin-bottom: 12px;
  padding: 10px 0;
  border-radius: 18px;
  background: rgba(255,255,255,0.10);
  font-weight: 600;
}
.connexity-status.connected {
  color: #7fffa7;
}
.connexity-status.disconnected {
  color: #ffbaba;
}
.connexity-details {
  font-size: 1rem;
  margin-top: 8px;
  color: #fff;
}
.connexity-loading {
  color: #fff;
  font-size: 1.1rem;
  margin: 24px 0;
}
.connexity-error {
  color: #ffbaba;
  font-size: 1.1rem;
  margin: 24px 0;
}

.path-info {
  position: absolute;
  top: 20px;
  right: 20px;
  background: rgba(255, 255, 255, 0.95);
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  font-size: 14px;
}

.path-info > div {
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.path-info > div:last-child {
  margin-bottom: 0;
}

.path-info i {
  width: 16px;
  color: #666;
}

.duration {
  color: #2196F3;
  font-weight: 600;
}

.emissions {
  color: #4CAF50;
}

.stations-count {
  color: #FF9800;
}

.station-tooltip-custom {
  background: rgba(255,255,255,0.95);
  color: #222;
  border-radius: 10px;
  padding: 8px 14px;
  font-size: 15px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.12);
  min-width: 90px;
  text-align: center;
}
.station-tooltip-title {
  font-weight: 700;
  font-size: 16px;
  margin-bottom: 4px;
}
.station-tooltip-lines {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  justify-content: center;
}
.line-badge {
  display: inline-block;
  color: #fff;
  font-weight: 600;
  font-size: 13px;
  border-radius: 8px;
  padding: 2px 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.10);
  border: 1.5px solid #fff;
}
.legend-lines {
  display: none;
}
.acpm-refined-badge-wrap {
  margin-top: 16px;
}
.acpm-refined-badge {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 12px;
  background: rgba(242, 245, 248, 0.65);
  backdrop-filter: blur(18px) saturate(160%);
  -webkit-backdrop-filter: blur(18px) saturate(160%);
  border-radius: 50px;
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow:
    inset 0 0 0 1.5px rgba(255, 255, 255, 0.9),
    0 4px 12px rgba(0, 0, 0, 0.05),
    0 8px 24px rgba(0, 0, 0, 0.05);
  padding: 8px 20px 8px 12px;
  transition: all 0.4s cubic-bezier(0.22, 1, 0.36, 1);
}
.acpm-refined-badge.is-animating {
  transform: scale(1.03);
  box-shadow:
    inset 0 0 0 1.5px rgba(255, 255, 255, 1),
    0 6px 16px rgba(45, 140, 245, 0.1),
    0 12px 32px rgba(45, 140, 245, 0.15);
}
.acpm-refined-icon {
  display: flex;
  align-items: center;
  color: #005bb5;
  opacity: 0.8;
}
.acpm-refined-value-wrapper {
  font-variant-numeric: tabular-nums;
  font-size: 1.3em;
  font-weight: 600;
  color: #003c7a;
  position: relative;
  height: 1.4em;
  line-height: 1.4em;
  overflow: hidden;
}
.slide-up-num-enter-active, .slide-up-num-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: absolute;
}
.slide-up-num-enter-from {
  opacity: 0.5;
  transform: translateY(100%);
}
.slide-up-num-leave-to {
  opacity: 0.5;
  transform: translateY(-100%);
}
.acpm-refined-anim-value {
  display: inline-block;
}
.fade-scale-enter-active, .fade-scale-leave-active {
  transition: all 0.5s cubic-bezier(0.22, 1, 0.36, 1);
}
.fade-scale-enter-from, .fade-scale-leave-to {
  opacity: 0;
  transform: scale(0.9);
}
</style>
