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
const startStationSuggestions = ref([])
const connexityResult = ref(null)
const isLoading = ref(false)
const allStations = ref([])
const stationLinesMap = ref({})

// Mapping des couleurs pour les lignes de métro avec saturation augmentée pour meilleur contraste
const LINE_COLORS = {
  '1': '#FFCE00',  // Jaune - ligne 1
  '2': '#0064B0',  // Bleu foncé - ligne 2
  '3': '#9F9825',  // Marron - ligne 3
  '3bis': '#98D4E2',  // Bleu clair - ligne 3bis
  '4': '#C902A0',  // Rose foncé - ligne 4
  '5': '#F28E42',  // Orange - ligne 5
  '6': '#6EC68D',  // Vert - ligne 6
  '7': '#FA9EBA',  // Rose - ligne 7
  '7bis': '#84C0D4',  // Bleu ciel - ligne 7bis
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

// Détecte si la station courante est une correspondance de changement de ligne
function isInterchange(segmentIndex, stationIndex) {
  if (
    segmentIndex < pathDetails.value.length - 1 &&
    stationIndex === pathDetails.value[segmentIndex].stations.length - 1
  ) {
    return true;
  }
  return false;
}

// ✅ WATCHER POUR DÉBUGGER
watch(pathLength, (newValue) => {
    console.log('=== DEBUG HOMEVIEW pathLength WATCH ===')
    console.log('HomeView pathLength changé:', newValue)
    console.log('Duration:', newValue?.duration, 'Type:', typeof newValue?.duration)
    console.log('Emissions:', newValue?.emissions, 'Type:', typeof newValue?.emissions)
}, { deep: true })

// ✅ FONCTION formatTime AMÉLIORÉE avec debug
function formatTime(pathLengthObj) {
    console.log('=== DEBUG formatTime ===')
    console.log('Input reçu:', pathLengthObj)
    console.log('Type input:', typeof pathLengthObj)
    
    const seconds = pathLengthObj?.duration || pathLengthObj || 0;
    console.log('Seconds calculées:', seconds, 'Type:', typeof seconds)
    
    if (!seconds || isNaN(seconds)) {
        console.log('Seconds invalides, retour 0 min')
        return '0 min';
    }

    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    
    console.log('Minutes:', minutes, 'Secondes restantes:', remainingSeconds)

    if (minutes === 0) {
        return `${remainingSeconds} sec`;
    } else if (remainingSeconds === 0) {
        return `${minutes} min`;
    } else {
        return `${minutes} min ${remainingSeconds} sec`;
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
    const res = await api.getStationsList()
    allStations.value = res.stations
    // Création d'une map nom -> lignes
    stationLinesMap.value = Object.fromEntries(
      res.stations.map(s => [s.name, s.lines])
    )
  } catch (e) {
    allStations.value = []
    stationLinesMap.value = {}
  }
})

function handleStartStationInput() {
  if (startStation.value.length < 2) {
    startStationSuggestions.value = [];
    return;
  }

  const searchTerm = startStation.value.toLowerCase();
  startStationSuggestions.value = stations
    .filter(station => station.toLowerCase().includes(searchTerm))
    .slice(0, 5);
}

function selectStartStation(station) {
  startStation.value = station;
  startStationSuggestions.value = [];
}

async function testConnexity() {
  isLoading.value = true;
  connexityResult.value = null;

  try {
    const url = startStation.value
      ? `${apiUrl}/connexity?station=${encodeURIComponent(startStation.value)}`
      : `${apiUrl}/connexity`;

    const response = await fetch(url);
    const data = await response.json();

    if (response.ok) {
      connexityResult.value = data;
    } else {
      throw new Error(data.error || 'Erreur lors du test de connexité');
    }
  } catch (error) {
    console.error('Erreur:', error);
    alert(error.message);
  } finally {
    isLoading.value = false;
  }
}

function closeConnexityModal() {
  showConnexityModal.value = false;
  startStation.value = '';
  startStationSuggestions.value = [];
  connexityResult.value = null;
}
</script>

<template>
  <main class="app-container">
    <MetroMapLeaflet />
    <ServerStatus />

    <div v-if="pathDetails && pathDetails.length > 0" class="liquid-glass-panel fade-in">
      <div class="content-wrapper">
        <div class="path-panel-header">
          <h2>Itinéraire</h2>
          <div class="total-time-badge">
            <span class="time-icon"></span>
            {{ formatTime(pathLength) }}
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
              </div>

              <div
                class="segment-stations"
                :style="{ '--segment-line-color': LINE_COLORS[segment.line] || '#ccc' }"
              >
                <div
                  v-for="(station, stationIndex) in segment.stations"
                  :key="stationIndex"
                  class="station-item"
                  :class="{
                    'station-start': stationIndex === 0,
                    'station-end': stationIndex === segment.stations.length - 1,
                    'station-interchange': isInterchange(index, stationIndex)
                  }"
                >
                  <span
                    class="station-dot"
                    :style="{
                      backgroundColor: isInterchange(index, stationIndex) ? '#fff' : (LINE_COLORS[segment.line] || '#000000'),
                      borderColor: '#fff',
                      boxShadow: '0 0 0 2px ' + (LINE_COLORS[segment.line] || '#000')
                    }"
                  ></span>
                  <span class="station-name">{{ station }}</span>
                  <span class="station-lines">
                    <span
                      v-for="line in (stationLinesMap[station] || []).filter(l => l !== segment.line)"
                      :key="line"
                      class="station-line-pill"
                      :style="{ backgroundColor: LINE_COLORS[line] || '#888', color: (line === '1' || line === '9' || line === '14') ? '#222' : '#fff' }"
                    >
                      {{ line }}
                    </span>
                  </span>
                  <span v-if="stationIndex === 0" class="station-label">Départ</span>
                  <span v-else-if="stationIndex === segment.stations.length - 1" class="station-label">Arrivée</span>
                  <span
                    v-else-if="stationLinesMap[station] && stationLinesMap[station].length > 1"
                    class="station-label transfer-indicator-label"
                  >
                    Correspondance
                  </span>
                  <span
                    v-if="isInterchange(index, stationIndex)"
                    class="interchange-lines"
                  >
                    {{ segment.line }} → {{ pathDetails[index + 1]?.line }}
                  </span>
                </div>
              </div>
            </div>

          </div>
        </div>

        <div class="path-summary-footer">
          <div class="path-details-pill">
            <span class="detail-item">
              <span class="detail-icon stop-icon"></span>
              {{ getTotalStations() }} stations
            </span>
            <span class="detail-item">
              <span class="detail-icon transfer-icon"></span>
              {{ pathDetails.length - 1 }} correspondances
            </span>
            <span class="detail-item">
              <span class="detail-icon emissions-icon"></span>
              {{ pathLength?.emissions || 0 }}g CO₂
            </span>
          </div>
        </div>
      </div>
    </div>

    <div class="app-title centered-pill">
      <h1>Metro Paris</h1>
    </div>

    <!-- Modal de connexité -->
    <div v-if="showConnexityModal" class="modal-overlay" @click="closeConnexityModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>Test de Connexité</h2>
          <button class="close-button" @click="closeConnexityModal">&times;</button>
        </div>

        <div class="modal-body">
          <div class="input-group">
            <label for="startStation">Station de départ (optionnel) :</label>
            <input
              id="startStation"
              v-model="startStation"
              type="text"
              placeholder="Entrez une station de départ"
              @input="handleStartStationInput"
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
            class="test-button"
            @click="testConnexity"
            :disabled="isLoading"
          >
            {{ isLoading ? 'Test en cours...' : 'Tester la connexité' }}
          </button>

          <div v-if="connexityResult" class="result-container">
            <div class="result-header">
              <h3>Résumé</h3>
              <div class="status-badge" :class="{ 'connected': connexityResult.is_connected }">
                {{ connexityResult.is_connected ? 'Connexe' : 'Non connexe' }}
              </div>
            </div>

            <div class="result-details">
              <p v-if="connexityResult.start_station">
                Test effectué depuis la station : <strong>{{ connexityResult.start_station }}</strong>
              </p>
              <p>Nombre total de stations : <strong>{{ connexityResult.total_stations }}</strong></p>
              <p>Stations accessibles : <strong>{{ connexityResult.reachable_stations }}</strong></p>
              <p>Stations non accessibles : <strong>{{ connexityResult.unreachable_count }}</strong></p>
              <p v-if="connexityResult.total_stations">
                Pourcentage de connexité :
                <strong>{{ ((connexityResult.reachable_stations / connexityResult.total_stations) * 100).toFixed(1) }}%</strong>
              </p>
              <div v-if="connexityResult.unreachable_stations && connexityResult.unreachable_stations.length > 0" class="unreachable-stations">
                <h4>Stations non accessibles ({{ connexityResult.unreachable_stations.length }}) :</h4>
                <ul>
                  <li v-for="station in connexityResult.unreachable_stations" :key="station.id">
                    {{ station.name }} (Ligne {{ station.line }})
                  </li>
                </ul>
              </div>
              <div v-else>
                <p>Toutes les stations sont accessibles depuis la station de départ.</p>
              </div>
              <div v-if="allStations.length && connexityResult.reachable_stations">
                <h4>Liste des stations accessibles ({{ connexityResult.reachable_stations }}) :</h4>
                <div class="stations-list">
                  <span v-for="station in allStations.filter(s => !connexityResult.unreachable_stations.map(u => u.name).includes(s))" :key="station" class="station-pill">{{ station }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ✅ DEBUG DANS LE TEMPLATE -->
    <div class="debug-panel" style="position: fixed; top: 10px; left: 10px; background: black; color: white; padding: 10px; z-index: 9999; font-size: 12px;">
        <div>pathLength: {{ JSON.stringify(pathLength, null, 2) }}</div>
        <div>duration: {{ pathLength?.duration }} ({{ typeof pathLength?.duration }})</div>
        <div>emissions: {{ pathLength?.emissions }} ({{ typeof pathLength?.emissions }})</div>
    </div>
  </main>
</template>

<style scoped>
.app-container {
  width: 100vw;
  height: 100vh;
  position: relative;
  overflow: hidden;
  background-color: var(--apple-ui-background);
}

.centered-pill {
  position: absolute;
  top: 40px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 2000;
  background: linear-gradient(135deg, rgba(89, 95, 207, 0.85), rgba(81, 171, 187, 0.85));
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  padding: 12px 40px;
  border-radius: var(--radius-pill);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12), 0 1.5px 6px rgba(0,0,0,0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1.5px solid rgba(255,255,255,0.18);
}

.app-title h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.12);
  letter-spacing: 0.5px;
}

.liquid-glass-panel {
  position: absolute;
  top: var(--spacing-xl);
  right: var(--spacing-xl);
  width: 380px;
  max-height: calc(100vh - 48px);
  overflow-y: auto;
  z-index: 1000;
  pointer-events: auto;
  border-radius: 40px;
  background: linear-gradient(135deg, rgba(89, 95, 207, 0.8), rgba(81, 171, 187, 0.8));
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.1),
    inset 0 0 0 1px rgba(255, 255, 255, 0.2);
  padding: 2px;
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
  overflow: hidden;
}

.path-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--spacing-md);
}

.path-panel-header h2 {
  font-size: 28px;
  font-weight: 600;
  margin: 0;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.total-time-badge {
  background: rgba(255, 255, 255, 0.2);
  padding: 8px 16px;
  border-radius: var(--radius-pill);
  font-weight: 600;
  font-size: 18px;
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  color: white;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.2);
}

.time-icon {
  width: 18px;
  height: 18px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cpolyline points='12 6 12 12 16 14'%3E%3C/polyline%3E%3C/svg%3E");
  background-size: contain;
  display: block;
}

.timeline {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.timeline-segment {
  display: flex;
  gap: var(--spacing-md);
}

.line-indicator {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 700;
  font-size: 18px;
  flex-shrink: 0;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.segment-content {
  flex-grow: 1;
  display: flex;
  flex-direction: column;
}

.segment-header {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  margin-bottom: var(--spacing-sm);
}

.segment-title {
  font-weight: 600;
  font-size: 18px;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.segment-duration {
  font-size: 16px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.85);
  background: rgba(255, 255, 255, 0.1);
  padding: 4px 12px;
  border-radius: 15px;
}

.segment-stations {
  display: flex;
  flex-direction: column;
  gap: 4px;
  position: relative;
}

.segment-stations::before {
  content: "";
  position: absolute;
  left: 6px;
  top: 10px;
  bottom: 10px;
  width: 2px;
  background-color: var(--segment-line-color);
  z-index: 1;
}

.station-item {
  display: flex;
  align-items: center;
  padding: 10px 0;
  position: relative;
}

.station-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  z-index: 2;
  border: 2px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.2), 0 0 5px rgba(255, 255, 255, 0.5);
  margin-right: var(--spacing-sm);
  flex-shrink: 0;
}

.station-name {
  font-size: 16px;
  font-weight: 500;
  color: white;
}

.station-label {
  margin-left: auto;
  font-size: 13px;
  font-weight: 500;
  background: rgba(255, 255, 255, 0.15);
  padding: 3px 10px;
  border-radius: var(--radius-pill);
  color: white;
}

.station-start .station-label {
  background: #FF9C41;
  color: white;
  box-shadow: 0 0 8px rgba(255, 156, 65, 0.5);
}

.station-end .station-label {
  background: #A15CFF;
  color: white;
  box-shadow: 0 0 8px rgba(161, 92, 255, 0.5);
}

.station-transfer {
  color: rgba(255, 255, 255, 0.8);
}

.transfer-indicator-label {
  background: #FFD700;
  color: #222;
  box-shadow: 0 0 8px rgba(255, 215, 0, 0.6);
}

.path-summary-footer {
  margin-top: var(--spacing-lg);
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  padding-top: var(--spacing-md);
}

.path-details-pill {
  display: flex;
  justify-content: space-around;
  background: rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-pill);
  padding: var(--spacing-sm) var(--spacing-md);
}

.detail-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  font-size: 15px;
  font-weight: 500;
  color: white;
}

.detail-icon {
  width: 18px;
  height: 18px;
  background-size: contain;
  display: block;
}

.stop-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='3'%3E%3C/circle%3E%3C/svg%3E");
}

.transfer-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M8 3L4 7l4 4'%3E%3C/path%3E%3Cpath d='M4 7h16'%3E%3C/path%3E%3Cpath d='M16 21l4-4-4-4'%3E%3C/path%3E%3Cpath d='M20 17H4'%3E%3C/path%3E%3C/svg%3E");
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .liquid-glass-panel {
    width: calc(100% - 32px);
    left: 16px;
    right: 16px;
    top: auto;
    bottom: 16px;
    max-height: 70vh;
  }

  .app-title {
    top: 16px;
    left: 16px;
  }
}

.input-group {
  margin-bottom: 1rem;
  position: relative;
}

.input-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--text-color);
}

.input-group input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-color);
  font-size: 1rem;
}

.suggestions-list {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  max-height: 200px;
  overflow-y: auto;
}

.suggestion-item {
  padding: 0.75rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.suggestion-item:hover {
  background-color: rgba(0, 0, 0, 0.05);
}

.result-container {
  margin-top: 1.5rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.status-badge {
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-weight: 500;
  background: #ff4d4d;
  color: white;
}

.status-badge.connected {
  background: #4CAF50;
}

.result-details {
  margin-bottom: 1rem;
}

.result-details p {
  margin: 0.5rem 0;
  color: var(--text-color);
}

.unreachable-stations {
  margin-top: 1rem;
}

.unreachable-stations h4 {
  margin-bottom: 0.5rem;
  color: var(--text-color);
}

.unreachable-stations ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.unreachable-stations li {
  padding: 0.5rem;
  margin: 0.25rem 0;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  color: var(--text-color);
}

.test-button {
  width: 100%;
  padding: 0.75rem;
  background: var(--primary-color);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: background-color 0.2s;
}

.test-button:hover {
  background: var(--primary-color-dark);
}

.test-button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.stations-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
}
.station-pill {
  background: rgba(255,255,255,0.18);
  color: var(--text-color);
  border-radius: 16px;
  padding: 0.3em 0.9em;
  font-size: 0.95em;
  margin-bottom: 0.2em;
  box-shadow: 0 1px 4px rgba(0,0,0,0.07);
}

.station-lines {
  display: inline-flex;
  gap: 0.2em;
  margin-left: 0.5em;
  vertical-align: middle;
}
.station-line-pill {
  display: inline-block;
  min-width: 1.7em;
  padding: 0.1em 0.5em;
  border-radius: 1em;
  font-size: 0.95em;
  font-weight: 700;
  margin-right: 0.1em;
  box-shadow: 0 1px 4px rgba(0,0,0,0.10);
  letter-spacing: 0.02em;
  text-align: center;
}


/* Nouveau design pour la correspondance */
.transfer-box {
  margin: 16px auto;
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  text-align: center;
  color: white;
  font-size: 16px;
  font-weight: 500;
  box-shadow: 0 1px 5px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.transfer-line-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.transfer-line {
  color: white;
  font-weight: 600;
  padding: 6px 12px;
  border-radius: 20px;
  min-width: 36px;
  text-align: center;
  font-size: 15px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.2);
}

.transfer-arrow {
  font-size: 20px;
}

.transfer-label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
}

.interchange-lines {
  font-size: 13px;
  font-weight: 500;
  margin-left: 1.5em;
  color: #fff;
  opacity: 0.8;
}

.trip-info-panel {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: var(--spacing-sm);
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.info-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 4px;
}

.info-icon {
  width: 24px;
  height: 24px;
  background-size: contain;
  opacity: 0.8;
}

.info-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
}

.info-value {
  font-size: 16px;
  color: white;
  font-weight: 600;
}

.emissions-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M7 13l3 3 7-7'%3E%3C/path%3E%3Cpath d='M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z'%3E%3C/path%3E%3C/svg%3E");
}

.stations-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='3'%3E%3C/circle%3E%3Cpath d='M12 1v6m0 6v6'%3E%3C/path%3E%3Cpath d='M23 12h-6m-6 0H1'%3E%3C/path%3E%3C/svg%3E");
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
</style>
