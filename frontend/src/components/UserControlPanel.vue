<!--
  MetroCity - Mastercamp 2025
  Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
  Fichier: UserControlPanel.vue
  Description: Panneau de contrôle principal pour la recherche d'itinéraires et les outils avancés
-->
<template>
  <div class="unified-control-panel glassmorphism-panel" :style="{ fontFamily: 'var(--font-family)' }">
    <div class="panel-container">
      <!-- En-tête avec titre et mode toggle -->
      <div class="panel-header">
        <h2>Navigation Métro</h2>
        <div class="mode-toggle">
          <button 
            :class="['btn-toggle', { active: searchMode === 'classic' }]"
            @click="$emit('updateSearchMode', 'classic')"
          >
            Classique
          </button>
          <button 
            :class="['btn-toggle', { active: searchMode === 'temporal' }]"
            @click="$emit('updateSearchMode', 'temporal')"
          >
            Temporel
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
            <label for="startStation" class="form-label">
              <span class="station-indicator departure"></span>
              <span class="label-text">De</span>
            </label>
            <input
              id="startStation"
              :value="startStation"
              type="text"
              placeholder="Entrez la station de départ"
              @input="$emit('updateStartStation', $event.target.value)"
              class="form-input station-input"
            />
            <div v-if="startStationSuggestions.length > 0" class="suggestions-list">
              <div
                v-for="suggestion in startStationSuggestions"
                :key="suggestion"
                class="suggestion-item"
                @click="$emit('selectStartStation', suggestion)"
              >
                {{ suggestion }}
                <span v-if="stationLinesMap[suggestion] && stationLinesMap[suggestion].length > 0" class="suggestion-lines">
                  <span v-for="line in stationLinesMap[suggestion]" :key="line" 
                    :class="['suggestion-line-badge', getLineType(line) === 'RER' ? 'rer-badge' : 'metro-badge']" 
                    :style="{ backgroundColor: LINE_COLORS[line] || '#1976d2', color: '#fff' }">
                    {{ line }}
                  </span>
                </span>
              </div>
            </div>
          </div>
          
          <!-- BOUTON D'INVERSION -->
          <div class="swap-button-glass">
            <button @click="$emit('swapStations')" title="Inverser départ et arrivée" class="btn-primary swap-btn">
              <span class="swap-icon">⇄</span>
            </button>
          </div>
          
          <div class="input-group">
            <label for="endStation" class="form-label">
              <span class="station-indicator arrival"></span>
              <span class="label-text">À</span>
            </label>
            <input
              id="endStation"
              :value="endStation"
              type="text"
              placeholder="Entrez la station de destination"
              @input="$emit('updateEndStation', $event.target.value)"
              class="form-input station-input"
            />
            <div v-if="endStationSuggestions.length > 0" class="suggestions-list">
              <div
                v-for="suggestion in endStationSuggestions"
                :key="suggestion"
                class="suggestion-item"
                @click="$emit('selectEndStation', suggestion)"
              >
                {{ suggestion }}
                <span v-if="stationLinesMap[suggestion] && stationLinesMap[suggestion].length > 0" class="suggestion-lines">
                  <span v-for="line in stationLinesMap[suggestion]" :key="line" 
                    :class="['suggestion-line-badge', getLineType(line) === 'RER' ? 'rer-badge' : 'metro-badge']" 
                    :style="{ backgroundColor: LINE_COLORS[line] || '#1976d2', color: '#fff' }">
                    {{ line }}
                  </span>
                </span>
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
                :class="['btn-toggle', { active: timeType === 'departure' }]"
                @click="$emit('updateTimeType', 'departure')"
                style="min-width: 90px;"
              >
                Départ
              </button>
              <button 
                :class="['btn-toggle', { active: timeType === 'arrival' }]"
                @click="$emit('updateTimeType', 'arrival')"
                style="min-width: 90px;"
              >
                Arrivée
              </button>
            </div>
          </div>
          
          <!-- Critère de tri -->
          <div class="sort-criterion-section">
            <span class="sort-criterion-title">Critère de tri</span>
            <div class="sort-criterion-toggle">
              <button 
                :class="['btn-toggle', 'sort-toggle-btn', { active: sortCriterion === 'duration' }]"
                @click="$emit('updateSortCriterion', 'duration')"
              >
                <span class="icon time-icon"></span>
                <span>Durée</span>
              </button>
              <button 
                :class="['btn-toggle', 'sort-toggle-btn', { active: sortCriterion === 'emissions' }]"
                @click="$emit('updateSortCriterion', 'emissions')"
              >
                <span class="icon emissions-icon"></span>
                <span>CO₂</span>
              </button>
            </div>
          </div>
          
          <div class="temporal-inputs">
            <div class="input-group">
              <label :for="timeType === 'departure' ? 'departureTime' : 'arrivalTime'" class="form-label">
                <span class="label-text">
                  {{ timeType === 'departure' ? 'Heure de départ' : 'Heure d\'arrivée' }}
                </span>
              </label>
              <input
                :id="timeType === 'departure' ? 'departureTime' : 'arrivalTime'"
                :value="departureTime"
                type="text"
                :placeholder="timeType === 'departure' ? '08:30 ou 24:30 (00:30 lendemain)' : '09:00 ou 24:30'"
                pattern="^([0-2]?[0-9]|3[0-1]):[0-5][0-9]$"
                class="form-input time-input"
                @input="$emit('updateDepartureTime', $event.target.value)"
                @blur="$emit('validateTimeInput')"
              />
            </div>
            <div class="input-group">
              <label for="departureDate" class="form-label">
                <span class="label-text">Date</span>
              </label>
              <input
                id="departureDate"
                :value="departureDate"
                type="date"
                min="2024-03-01"
                max="2024-03-31"
                class="form-input date-input"
                @input="$emit('updateDepartureDate', $event.target.value)"
              />
            </div>
          </div>
        </div>

        <!-- Bouton de recherche principal -->
        <button
          class="btn-primary primary-search-button"
          @click="$emit('findPath')"
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
          <button class="btn-primary tool-button" @click="$emit('toggleACPM')">
            <span class="tool-text">ACPM</span>
          </button>
          
          <button class="btn-primary tool-button" @click="$emit('showConnexityModal')">
            <span class="tool-text">Connexité</span>
          </button>
          
          <button class="btn-primary tool-button" @click="$emit('toggleLines')">
            <span class="tool-text">Lignes</span>
          </button>
          
          <button class="btn-primary tool-button" @click="$emit('clearPath')">
            <span class="tool-text">Effacer</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { 
  LINE_COLORS, 
  getLineType
} from '../constants/metro'

// Props
const props = defineProps({
  searchMode: String,
  startStation: String,
  endStation: String,
  startStationSuggestions: Array,
  endStationSuggestions: Array,
  stationLinesMap: Object,
  timeType: String,
  sortCriterion: String,
  departureTime: String,
  departureDate: String,
  isLoading: Boolean
})

// Émissions d'événements
const emit = defineEmits([
  'updateSearchMode',
  'updateStartStation',
  'updateEndStation',
  'selectStartStation',
  'selectEndStation',
  'swapStations',
  'updateTimeType',
  'updateSortCriterion',
  'updateDepartureTime',
  'updateDepartureDate',
  'validateTimeInput',
  'findPath',
  'toggleACPM',
  'showConnexityModal',
  'toggleLines',
  'clearPath'
])
</script>

<style scoped>
/* ===================================
   PANNEAU DE CONTRÔLE
   =================================== */
.unified-control-panel {
  position: absolute;
  top: 20px;
  left: 20px;
  z-index: 1000;
  width: 400px;
  max-height: calc(100vh - 40px);
  font-family: var(--font-family);
}

.panel-container {
  background: var(--secondary-gradient);
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
  gap: 0;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 16px;
  padding: 4px;
  backdrop-filter: blur(25px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 
    inset 0 1px 0 rgba(255, 255, 255, 0.1),
    0 8px 32px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
}

.mode-toggle::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
  border-radius: 16px;
  pointer-events: none;
}

.btn-toggle {
  flex: 1;
  padding: 12px 20px;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 600;
  font-size: 15px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  z-index: 1;
  text-align: center;
  letter-spacing: -0.3px;
  backdrop-filter: blur(10px);
}

.btn-toggle.active {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.25), rgba(255, 255, 255, 0.15));
  color: rgba(255, 255, 255, 0.95);
  box-shadow: 
    0 4px 20px rgba(255, 255, 255, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.2),
    0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
  backdrop-filter: blur(30px);
}

.btn-toggle:hover:not(.active) {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.85);
}



/* ===================================
   SECTIONS
   =================================== */
.search-section, .tools-section {
  padding: var(--spacing-lg) var(--spacing-xl);
}

.section-title {
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-sm);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.section-title span {
  font-size: 18px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  letter-spacing: -0.4px;
}

/* ===================================
   STATIONS ET FORMULAIRES
   =================================== */
.stations-inputs {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
  margin-bottom: var(--spacing-lg);
}

.input-group {
  position: relative;
}

.station-input {
  padding-left: 48px;
}

.station-indicator {
  position: absolute;
  left: 16px;
  bottom: 14px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  z-index: 1;
}

.station-indicator.departure {
  background: var(--success-color);
  box-shadow: 0 0 8px rgba(76, 175, 80, 0.4);
}

.station-indicator.arrival {
  background: var(--error-color);
  box-shadow: 0 0 8px rgba(244, 67, 54, 0.4);
}

.suggestions-list {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: rgba(255, 255, 255, 0.95);
  border-radius: var(--border-radius-md);
  backdrop-filter: blur(20px);
  box-shadow: var(--shadow-glass);
  z-index: 1000;
  max-height: 200px;
  overflow-y: auto;
  margin-top: 4px;
}

.suggestion-item {
  padding: var(--spacing-sm) var(--spacing-md);
  cursor: pointer;
  color: rgba(0, 0, 0, 0.8);
  transition: var(--transition-fast);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.suggestion-item:hover {
  background: rgba(0, 0, 0, 0.1);
}

.suggestion-lines {
  display: flex;
  gap: 4px;
}

/* ===================================
   BOUTON D'INVERSION
   =================================== */
.swap-button-glass {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 var(--spacing-sm);
}

.swap-btn {
  border-radius: var(--border-radius-full);
  width: 48px;
  height: 48px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.swap-icon {
  font-size: 20px;
  font-weight: 700;
}

/* ===================================
   SECTION TEMPORELLE
   =================================== */
.temporal-section {
  margin-bottom: var(--spacing-lg);
}

.temporal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-md);
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.temporal-title {
  font-size: 16px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.sort-criterion-section {
  margin-bottom: var(--spacing-md);
}

.sort-criterion-title {
  display: block;
  margin-bottom: var(--spacing-sm);
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.sort-criterion-toggle {
  display: flex;
  gap: var(--spacing-xs);
}

.sort-toggle-btn {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  min-width: 80px;
  justify-content: center;
}

.temporal-inputs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
}

/* ===================================
   BOUTONS
   =================================== */
.primary-search-button {
  width: 100%;
  margin-bottom: var(--spacing-lg);
  font-size: 16px;
  font-weight: 700;
  padding: var(--spacing-lg) var(--spacing-xl);
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-sm);
}

.tool-button {
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
}

.tool-text {
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.3px;
}

/* ===================================
   RESPONSIVE
   =================================== */
@media (max-width: 768px) {
  .unified-control-panel {
    left: 10px;
    top: 10px;
    width: calc(100vw - 20px);
    max-width: 400px;
  }
  
  .panel-header {
    padding: 20px 16px 16px;
  }
  
  .panel-header h2 {
    font-size: 28px;
    margin-bottom: 16px;
  }
  
  .search-section, .tools-section {
    padding: var(--spacing-md) var(--spacing-lg);
  }
  
  .temporal-inputs {
    grid-template-columns: 1fr;
  }
  
  .temporal-header {
    flex-direction: column;
    align-items: flex-start;
  }
}

.form-label {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.label-text {
  font-size: 20px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  letter-spacing: -0.5px;
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}
</style> 