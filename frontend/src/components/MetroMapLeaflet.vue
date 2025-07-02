```vue
<template>
  <div class="map-container">
    <!-- Panneau supprimé - remplacé par le panneau unifié dans HomeView -->

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
        :key="'line-polyline-' + line.line + '-' + idx"
        :lat-lngs="line.path"
        :color="line.color"
        :weight="6"
        :opacity="0.85"
        :line-cap="'round'"
        :line-join="'round'"
      />

      <!-- Les markers et lignes restent affichés -->
      <l-marker
        v-for="station in allStations"
        :key="station.id"
        :lat-lng="convertPosition(station.position)"
        @mouseover="hoveredStation = station.id"
        @mouseout="hoveredStation = null"
        @click="onStationClick(station)"
      >
        <l-tooltip v-if="hoveredStation === station.id" direction="top" :permanent="false" class="station-tooltip-custom">
          <div class="station-tooltip-title">{{ station.name }}</div>
          <div class="station-tooltip-lines">
            <span v-for="line in station.lines" :key="line" class="line-badge" :style="{ backgroundColor: LINE_COLORS[line] || '#1976d2' }">{{ line }}</span>
          </div>
        </l-tooltip>
        <l-icon
          :icon-url="getIconUrl(station)"
          :icon-size="getIconSize()"
          :icon-anchor="getIconAnchor()"
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
const allStations = ref([])
const hoveredStation = ref(null)
const zoom = ref(13)
const center = ref([48.8566, 2.3522])
const shortestPath = ref([])
const pathDetails = inject('pathDetails')
const debugPath = ref([])
const map = ref(null)
const acpmTotalWeight = ref(null)
const acpmAnimatedWeight = ref(0)
const acpmAnimating = ref(false)

// Injecter les données partagées depuis HomeView
const showACPM = inject('showACPM', ref(false))
const acpmPath = inject('acpmPath', ref([]))
const showLines = inject('showLines', ref(false))
const linesPolylines = inject('linesPolylines', ref([]))

// Injecter les fonctions de sélection de stations
const selectStationFromMap = inject('selectStationFromMap', null)

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
  '14': '#662483',  // Violet - ligne 14
  'A': '#EB2132',  // Rouge - RER A
  'B': '#5091CB',  // Bleu - RER B
  'C': '#FFCC30',  // Jaune - RER C
  'D': '#008B5B',  // Vert - RER D
  'E': '#B94E9A'   // Violet - RER E
}

// Charger les stations depuis l'API
async function fetchStations() {
  try {
    const data = await api.getStationsList()
    // Nouveau mapping avec log et filtrage explicite
    stations.value = data.stations.filter(s => s.position && Array.isArray(s.position) && s.position.length === 2)
      .map(station => {
        let id = undefined;
        if (station.ids && station.ids.length > 0) id = station.ids[0];
        else if (station.id) id = station.id;
        if (!id) {
          console.warn('Station sans id détectée (ignorée):', station);
        }
        return id ? {
          id,
          name: station.name,
          lines: station.lines,
          position: station.position
        } : null;
      })
      .filter(station => station !== null);
    // Log des 5 premières stations pour debug
    console.log('Stations (5 premières):', stations.value.slice(0, 5));
    // Charger aussi allStations pour les trajets temporels
    allStations.value = data.stations.filter(s => s.position && Array.isArray(s.position) && s.position.length === 2)
      .map(station => {
        let id = undefined;
        if (station.ids && station.ids.length > 0) id = station.ids[0];
        else if (station.id) id = station.id;
        if (!id) {
          console.warn('Station sans id détectée (ignorée):', station);
        }
        return id ? {
          id,
          name: station.name,
          lines: station.lines,
          position: station.position
        } : null;
      })
      .filter(station => station !== null);
    console.log('allStations (5 premières):', allStations.value.slice(0, 5));
  } catch (error) {
    console.error('Erreur lors du chargement des stations:', error)
  }
}

// Charger toutes les stations uniques depuis notre nouvelle API
function convertPosition(pos) {
  // Conversion centièmes/millièmes de degrés -> degrés décimaux
  if (!Array.isArray(pos) || pos.length !== 2) return [0, 0];
  return [pos[0] / 1000, pos[1] / 1000];
}

function getStationType(station) {
  // Détecte si la station est une correspondance ou un terminus
  if (station.lines && station.lines.length > 1) return 'correspondance';
  if (station.isTerminus || station.terminus) return 'terminus';
  return 'simple';
}

// Calculer la taille des icônes en fonction du zoom
function getIconSize() {
  // Taille de base plus petite et proportionnelle au zoom
  const baseSize = 12; // Taille de base réduite de 28 à 12
  const zoomFactor = Math.pow(1.3, zoom.value - 13); // Facteur d'échelle basé sur le zoom
  const size = Math.max(6, Math.min(24, baseSize * zoomFactor)); // Taille entre 6 et 24px
  return [size, size];
}

function getIconAnchor() {
  const [width, height] = getIconSize();
  return [width / 2, height / 2];
}

function getIconUrl(station) {
  const line = Array.isArray(station.lines) && station.lines.length > 0 ? station.lines[0] : '1';
  const color = LINE_COLORS[line] || '#1976d2';
  const [iconWidth, iconHeight] = getIconSize();
  
  // Ajuster le rayon et l'épaisseur du trait en fonction de la taille
  const scaleFactor = iconWidth / 12; // Facteur basé sur la taille de base de 12px
  let radius = Math.max(2, 4 * scaleFactor); 
  let stroke = Math.max(1, 1.5 * scaleFactor);
  let fill = color, strokeColor = 'white';
  
  // Détection du type de station
  if (station.lines && station.lines.length > 1) {
    // Correspondance = point blanc avec contour noir plus épais (pas de filtre SVG pour Safari)
    fill = '#fff';
    strokeColor = 'black';
    stroke = Math.max(2, 2.5 * scaleFactor); // Contour plus épais pour compenser l'absence de glow
    radius = Math.max(3, 5 * scaleFactor); // Légèrement plus gros pour être plus visible
  } else if (station.isTerminus || station.terminus) {
    // Terminus = plus gros avec contour plus épais
    radius = Math.max(3, 6 * scaleFactor);
    stroke = Math.max(2, 3 * scaleFactor);
  }
  
  const center = iconWidth / 2;
  // SVG simplifié sans filtres pour compatibilité Safari
  const svg = `<svg xmlns='http://www.w3.org/2000/svg' width='${iconWidth}' height='${iconHeight}' viewBox='0 0 ${iconWidth} ${iconHeight}'><circle cx='${center}' cy='${center}' r='${radius}' fill='${fill}' stroke='${strokeColor}' stroke-width='${stroke}'/></svg>`;
  return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg);
}

// Fonctions de recherche supprimées - gérées maintenant dans HomeView

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
    if (map.value && typeof map.value.invalidateSize === 'function') {
      map.value.invalidateSize();
    }
  });
}

// Watchers pour les changements de données
watch(showLines, (newValue) => {
  console.log('[MetroMapLeaflet] showLines changé:', newValue)
  console.log('[MetroMapLeaflet] linesPolylines actuel:', linesPolylines.value.length, 'lignes')
})

watch(linesPolylines, (newValue) => {
  console.log('[MetroMapLeaflet] linesPolylines changé:', newValue.length, 'lignes')
  console.log('[MetroMapLeaflet] Détail des lignes:', newValue)
  
  // Vérifier que chaque ligne a les bonnes propriétés
  newValue.forEach((line, index) => {
    console.log(`[MetroMapLeaflet] Ligne ${index}:`, {
      line: line.line,
      pathLength: line.path ? line.path.length : 0,
      color: line.color,
      hasPath: !!line.path
    })
    
    // Afficher les coordonnées de la première ligne pour debug
    if (index === 0 && line.path && line.path.length > 0) {
      console.log('[MetroMapLeaflet] Coordonnées de la ligne 1:', line.path.slice(0, 5)) // Afficher les 5 premiers points
    }
  })
}, { deep: true })

watch(acpmPath, (newValue) => {
  console.log('[MetroMapLeaflet] acpmPath changé:', newValue.length, 'chemins')
  console.log('[MetroMapLeaflet] Détail des chemins ACPM:', newValue)
  
  // Afficher le détail du premier chemin pour debug
  if (newValue.length > 0) {
    console.log('[MetroMapLeaflet] Premier chemin ACPM:', newValue[0])
    console.log('[MetroMapLeaflet] Coordonnées du premier chemin:', newValue[0].path)
  }
})

watch(showACPM, (newValue) => {
  console.log('[MetroMapLeaflet] showACPM changé:', newValue)
})

// Watcher pour le zoom afin de mettre à jour la taille des icônes
watch(zoom, () => {
  // Forcer la re-génération des icônes en déclenchant une réactivité
  stations.value = [...stations.value]
}, { immediate: true })

// Fonction pour gérer le clic sur une station
function onStationClick(station) {
  if (selectStationFromMap) {
    selectStationFromMap(station);
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
        // End animation class after a short delay
        setTimeout(() => acpmAnimating.value = false, 600)
      }
    }
    requestAnimationFrame(animate)
  }
})

// Watcher pour mettre à jour l'affichage du trajet sur la carte
watch(pathDetails, (newPathDetails) => {
  if (!newPathDetails || newPathDetails.length === 0) {
    shortestPath.value = []
    return
  }

  console.log('[MetroMapLeaflet] pathDetails reçus:', newPathDetails)
  console.log('[MetroMapLeaflet] allStations disponibles:', allStations.value.length)

  // Remettre à zéro le chemin sur la carte
  shortestPath.value = []

  // Créer les segments pour l'affichage sur la carte
  newPathDetails.forEach((segment, segmentIndex) => {
    // Détecter le format des données
    const isShortestPathFormat = segment.hasOwnProperty('Ligne') && segment.hasOwnProperty('Stations')
    const isTemporalFormat = segment.hasOwnProperty('line') && segment.hasOwnProperty('stations')
    
    console.log(`[MetroMapLeaflet] Segment ${segmentIndex}:`, {
      isShortestPathFormat,
      isTemporalFormat,
      line: segment.line || segment.Ligne,
      stationsCount: segment.stations?.length || segment.Stations?.length
    })
    
    let line, stations
    
    if (isShortestPathFormat) {
      // Format du shortest path : { Ligne: "7", Stations: [{ Nom Station: "...", Position: [...] }] }
      line = segment.Ligne
      stations = segment.Stations
      
      if (stations.length < 2) return // Pas assez de stations pour tracer une ligne

      const pathCoordinates = []
      
      // Convertir toutes les positions des stations de cette ligne
      stations.forEach(station => {
        if (station.Position && station.Position.length === 2) {
          const latLng = convertPosition(station.Position)
          pathCoordinates.push(latLng)
        }
      })

      if (pathCoordinates.length >= 2) {
        shortestPath.value.push({
          path: pathCoordinates,
          color: LINE_COLORS[line] || '#000000',
          weight: 8,
          opacity: 1.0,
          lineCap: 'round',
          lineJoin: 'round',
          className: 'route-main'
        })
      }
    } else if (isTemporalFormat) {
      // Format du chemin temporel : { line: "7", stations: ["Station1", "Station2"] }
      line = segment.line
      stations = segment.stations
      
      if (!stations || stations.length < 2) return // Pas assez de stations pour tracer une ligne

      const pathCoordinates = []
      
      // Si on a les données originales (pour le shortest path transformé), les utiliser
      if (segment.originalStations && segment.originalStations.length > 0) {
        segment.originalStations.forEach(station => {
          if (station.Position && station.Position.length === 2) {
            const latLng = convertPosition(station.Position)
            pathCoordinates.push(latLng)
          }
        })
      } else {
        // Sinon, chercher les stations par nom (pour le vrai format temporel)
        stations.forEach(stationName => {
          // Chercher la station dans allStations par son nom
          const station = allStations.value.find(s => s.name === stationName)
          if (station && station.position && station.position.length === 2) {
            const latLng = convertPosition(station.position)
            pathCoordinates.push(latLng)
          } else {
            console.warn(`[MetroMapLeaflet] Station non trouvée: ${stationName}`)
          }
        })
      }

      console.log(`[MetroMapLeaflet] Segment temporel ${segmentIndex}:`, {
        line,
        stationsCount: stations.length,
        pathCoordinatesCount: pathCoordinates.length,
        pathCoordinates: pathCoordinates.slice(0, 3) // Afficher les 3 premiers points
      })

      if (pathCoordinates.length >= 2) {
        shortestPath.value.push({
          path: pathCoordinates,
          color: LINE_COLORS[line] || '#000000',
          weight: 8,
          opacity: 1.0,
          lineCap: 'round',
          lineJoin: 'round',
          className: 'route-main'
        })
      }
    }
  })
  
  console.log('[MetroMapLeaflet] shortestPath final:', shortestPath.value.length, 'segments')
}, { deep: true })

watch(
  allStations,
  (newVal) => {
    if (newVal && newVal.length > 0) {
      console.log('MetroMapLeaflet: allStations (5 premières après update):', newVal.slice(0, 5));
      newVal.slice(0, 5).forEach(station => {
        console.log('Coordonnées converties:', station.name, convertPosition(station.position));
      });
    }
  },
  { immediate: true }
)

onMounted(async () => {
  try {
    // Charger les stations d'abord
    await fetchStations();
    
    // Initialiser la carte après le montage du composant
    initializeMap();
    if (allStations.value && allStations.value.length > 0) {
      console.log('MetroMapLeaflet: allStations (5 premières):', allStations.value.slice(0, 5));
    } else {
      console.warn('MetroMapLeaflet: allStations vide ou non défini');
    }
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

/* Panneau supprimé - remplacé par le panneau unifié dans HomeView */

/* Styles du panneau supprimés - fonctionnalité déplacée vers HomeView */

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

:deep(.route-main) {
  stroke-opacity: 1 !important;
  filter: none !important;
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
