<!--
  MetroCity - Mastercamp 2025
  Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
  Fichier: HomeView.vue
  Description: Vue principale de l'application gérant l'interface utilisateur et la logique métier
-->
<script setup>
import MetroMapLeaflet from '../components/MetroMapLeaflet.vue'
import ServerStatus from '../components/ServerStatus.vue'
import ErrorNotification from '../components/ErrorNotification.vue'
import SuccessNotification from '../components/SuccessNotification.vue'
import LoadingNotification from '../components/LoadingNotification.vue'
import UserControlPanel from '../components/UserControlPanel.vue'
import { ref, provide, computed, watch } from 'vue'
import { api } from '../services/api'

import { useStations } from '../hooks/useStations'
import { useItinerary } from '../hooks/useItinerary'
import { useAdvancedTools } from '../hooks/useAdvancedTools'
import { useFormatting } from '../hooks/useFormatting'
import { usePathAnalysis } from '../hooks/usePathAnalysis'
import { useStationSwap } from '../hooks/useStationSwap'
import { useTransferDataCustom } from '../hooks/useTransferDataCustom'
import { useAppLifecycle } from '../hooks/useAppLifecycle'
import {
  LINE_COLORS,
  AIR_CONDITIONED_LINES,
  PARTIAL_AIR_CONDITIONED_LINES,
  getLineType,
  getUniqueLines
} from '../constants/metro'

const {
  allStations,
  stationLinesMap,
  startStation,
  endStation,
  startStationId,
  endStationId,
  startStationSuggestions,
  endStationSuggestions,
  loadStations,
  selectStationFromMap,
  clearResults: clearStationResults,
  handleStartStationInput,
  handleEndStationInput,
  selectStartStation,
  selectEndStation
} = useStations()

const {
  findPath,
  alternativePaths,
  selectedAlternativeIndex,
  selectAlternativePath,
  pathDetails,
  pathLength,
  temporalData,
  searchMode,
  sortCriterion,
  timeType,
  departureTime,
  departureDate,
  isLoading,
  validateTimeInput,
  clearResults,
  notificationService
} = useItinerary({ startStation, endStation, startStationId, endStationId })

const {
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
  clearAllTools
} = useAdvancedTools(notificationService)

const {
  formatTime,
  formatTimeDisplay,
  formatACPMTime,
  darkenColor
} = useFormatting()

const {
  getTransferCount: getTransferCountBase,
  getTotalStations: getTotalStationsBase
} = usePathAnalysis()

// Hook pour l'inversion des stations
const { swapStations } = useStationSwap({
  startStation,
  endStation,
  startStationId,
  endStationId,
  startStationSuggestions,
  endStationSuggestions
})

// Hook pour les données de correspondance personnalisées
const {
  isInterchange,
  getTransferTime,
  getWaitTime,
  getTotalStopTime,
  getTransferProgress,
  getTransferProgressColor,
  getTransferProgressText
} = useTransferDataCustom({ pathDetails })

// Hook pour le cycle de vie de l'application
useAppLifecycle(loadStations)

// Watchers
watch([showACPM, acpmPath], () => {
  // État ACPM mis à jour
})

// Méthodes pour les composants
function updateSearchMode(mode) {
  searchMode.value = mode
  clearResults()
}

function updateTimeType(type) {
  timeType.value = type
}

function updateSortCriterion(criterion) {
  sortCriterion.value = criterion
}

function updateDepartureTime(time) {
  departureTime.value = time
}

function updateDepartureDate(date) {
  departureDate.value = date
}

function updateStartStation(value) {
  startStation.value = value
  handleStartStationInput()
}

function updateEndStation(value) {
  endStation.value = value
  handleEndStationInput()
}

function getTransferCount() {
  return getTransferCountBase(pathLength.value, pathDetails.value)
}

function getTotalStations() {
  return getTotalStationsBase(pathLength.value, pathDetails.value)
}

// Notifications (après l'init du hook !)
const errorState = notificationService.getErrorState()
const successState = notificationService.getSuccessState()

// Fournir ces valeurs aux composants enfants
provide('pathDetails', pathDetails)
provide('pathLength', pathLength)
provide('showACPM', showACPM)
provide('acpmPath', acpmPath)
provide('showLines', showLines)
provide('linesPolylines', linesPolylines)
provide('selectStationFromMap', selectStationFromMap)

// Fonction clearPath maintenant utilise clearAllTools du hook
function clearPath() {
  // Effacer les résultats de l'itinéraire
  clearResults();
  clearStationResults();
  
  // Effacer tous les outils avancés via le hook
  clearAllTools();
}
</script>

<template>
  <main class="app-container">
    <!-- Carte en arrière-plan qui prend tout l'écran -->
    <div class="map-container">
      <MetroMapLeaflet />
      <ServerStatus />

      <!-- Panneau de contrôle unifié -->
      <UserControlPanel
        :searchMode="searchMode"
        :startStation="startStation"
        :endStation="endStation"
        :startStationSuggestions="startStationSuggestions"
        :endStationSuggestions="endStationSuggestions"
        :stationLinesMap="stationLinesMap"
        :timeType="timeType"
        :sortCriterion="sortCriterion"
        :departureTime="departureTime"
        :departureDate="departureDate"
        :isLoading="isLoading"
        @updateSearchMode="updateSearchMode"
        @updateStartStation="updateStartStation"
        @updateEndStation="updateEndStation"
        @selectStartStation="selectStartStation"
        @selectEndStation="selectEndStation"
        @swapStations="swapStations"
        @updateTimeType="updateTimeType"
        @updateSortCriterion="updateSortCriterion"
        @updateDepartureTime="updateDepartureTime"
        @updateDepartureDate="updateDepartureDate"
        @validateTimeInput="validateTimeInput"
        @findPath="findPath"
        @toggleACPM="toggleACPM"
        @showConnexityModal="showConnexityModal = true"
        @toggleLines="toggleLines"
        @clearPath="clearPath"
      />

      <!-- Sélecteur de chemins alternatifs - ANCIEN STYLE RESTAURÉ -->
      <div v-if="alternativePaths && alternativePaths.length > 0 && selectedAlternativeIndex === null" class="floating-panel fade-in">
        <div class="content-wrapper">
          <div class="path-panel-header">
            <h2>Meilleurs itinéraires</h2>
            <div class="sort-indicator" v-if="searchMode === 'temporal'">
              <span class="sort-indicator-icon" :class="sortCriterion === 'emissions' ? 'emissions-icon' : 'time-icon'"></span>
              <span class="sort-indicator-text">
                Trié par {{ sortCriterion === 'emissions' ? 'émissions CO₂' : 'durée' }}
              </span>
            </div>
          </div>
          <div class="alternative-paths-list">
            <div
              v-for="(alt, idx) in alternativePaths"
              :key="idx"
              :class="['alternative-path-summary', { selected: selectedAlternativeIndex === idx }]"
              @click="selectAlternativePath(idx)"
            >
              <!-- En-tête avec numéro d'itinéraire -->
              <div class="alt-header">
                <div class="alt-number">
                  <span class="alt-number-text">Itinéraire {{ idx + 1 }}</span>
                </div>
                <div class="alt-emissions-compact">
                  <div class="emissions-badge-compact">
                    <span class="emissions-icon-small"></span>
                    <span class="emissions-value-compact">{{ alt.emissions || 0 }}g CO₂</span>
                  </div>
                </div>
              </div>
              
              <!-- Lignes utilisées -->
              <div class="alt-lines-section">
                <div class="alt-lines-label">Lignes :</div>
              <div class="alt-lines">
                <span v-for="line in getUniqueLines(alt.segments)" :key="line" :class="['suggestion-line-badge', getLineType(line) === 'RER' ? 'rer-badge' : 'metro-badge']" :style="{ backgroundColor: LINE_COLORS[line] || '#1976d2', color: '#fff' }">
                  {{ line }}
                </span>
              </div>
              </div>
              
              <!-- Informations temporelles -->
              <div class="alt-times-section">
                <div class="alt-times-grid">
                  <div class="alt-time-item">
                    <span class="alt-time-label">Départ</span>
                    <span class="alt-time-value">{{ alt.departure_time }}</span>
            </div>
                  <div class="alt-time-item">
                    <span class="alt-time-label">Arrivée</span>
                    <span class="alt-time-value">{{ alt.arrival_time }}</span>
                  </div>
                  <div class="alt-time-item">
                    <span class="alt-time-label">Durée</span>
                    <span class="alt-time-value">{{ formatTime(alt.total_duration) }}</span>
                  </div>
                </div>
              </div>
              
              <!-- Indicateur de sélection -->
              <div class="alt-selection-indicator">
                <div class="selection-arrow">→</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Affichage de l'itinéraire détaillé - ANCIEN STYLE RESTAURÉ -->
      <div v-if="(selectedAlternativeIndex !== null && pathDetails && pathDetails.length > 0) || (alternativePaths.length === 0 && pathDetails && pathDetails.length > 0)" class="floating-panel fade-in">
        <div class="content-wrapper">
          <div class="path-panel-header">
            <button v-if="alternativePaths.length > 0" class="back-button" @click="selectedAlternativeIndex = null" title="Retour aux choix" style="margin-right: 16px;">
              ←
            </button>
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
                  <span class="segment-air-conditioning" v-if="AIR_CONDITIONED_LINES.includes(segment.line)">Climatisé</span>
                  <span class="segment-partial-air-conditioning" v-else-if="PARTIAL_AIR_CONDITIONED_LINES.includes(segment.line)">Partiellement climatisé</span>
                  <span class="segment-no-air-conditioning" v-else>Non climatisé</span>
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
                        {{ formatTime(segment.transferInfo.transfer_time) }}
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
      <div v-else-if="!isLoading && (showACPM || startStation || endStation) && alternativePaths.length === 0 && pathDetails.length === 0" class="floating-panel fade-in">
        <div class="content-wrapper">
          <div v-if="!showACPM || (showACPM && !acpmTotalWeight)" class="no-results-content">
            <div class="no-results-icon"></div>
            <h3>Recherche d'itinéraire</h3>
            <p>Sélectionnez vos stations pour commencer.</p>
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
        <div class="modal-content glassmorphism" @click.stop>
          <div class="modal-header flex-between">
            <h3>Test de connexité</h3>
            <button class="btn-primary close-button" @click="closeConnexityModal">×</button>
          </div>

          <div class="modal-body">
            <div class="input-group">
              <label for="connexityStation" class="form-label">Station (optionnel)</label>
              <input
                id="connexityStation"
                v-model="startStation"
                type="text"
                placeholder="Laisser vide pour tester tout le réseau"
                @input="handleStartStationInput"
                class="form-input station-input"
              />
              <div v-if="startStationSuggestions.length > 0" class="suggestions-list">
                <div
                  v-for="suggestion in startStationSuggestions"
                  :key="suggestion"
                  class="suggestion-item"
                  @click="selectStartStation(suggestion)"
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

            <button
              class="btn-primary modal-button"
              @click="() => testConnexity(startStation)"
              :disabled="isLoading"
            >
              {{ isLoading ? 'Test en cours...' : 'Tester la connexité' }}
            </button>

            <div v-if="connexityResult" class="connexity-results glassmorphism">
              <div class="result-item">
                <span class="result-label">Connexité :</span>
                <span class="result-value" :class="{ connected: connexityResult.is_connected }">
                  {{ connexityResult.is_connected === true ? 'Connecté' : (connexityResult.is_connected === false ? 'Non connecté' : 'Indéterminé') }}
                </span>
              </div>
              <div class="result-item">
                <span class="result-label">Stations accessibles :</span>
                <span class="result-value">{{ connexityResult.reachable_stations ?? '-' }} / {{ connexityResult.total_stations ?? '-' }}</span>
              </div>
              <div class="result-item" v-if="connexityResult.unreachable_count > 0">
                <span class="result-label">Stations inaccessibles :</span>
                <span class="result-value">{{ connexityResult.unreachable_count }}</span>
              </div>
              <div class="result-item" v-if="connexityResult.start_station">
                <span class="result-label">Station de départ :</span>
                <span class="result-value">{{ connexityResult.start_station }}</span>
              </div>
              <div class="result-item" v-if="connexityResult.unreachable_stations && connexityResult.unreachable_stations.length > 0">
                <span class="result-label">Exemples inaccessibles :</span>
                <span class="result-value">
                  <span v-for="(station, index) in connexityResult.unreachable_stations.slice(0, 3)" :key="station.id">
                    {{ station.name }}<span v-if="station.line"> ({{ Array.isArray(station.line) ? station.line.join(', ') : station.line }})</span>{{ index < 2 ? ', ' : '' }}
                  </span>
                  <span v-if="connexityResult.unreachable_stations.length > 3">... ({{ connexityResult.unreachable_stations.length - 3 }} autres)</span>
                </span>
              </div>
              <div class="result-item" v-if="connexityResult.error">
                <span class="result-label">Erreur :</span>
                <span class="result-value text-error">{{ connexityResult.error }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>

  <!-- Notifications -->
  <ErrorNotification
    :show="errorState.show"
    :title="errorState.title"
    :message="errorState.message"
    :details="errorState.details"
    @close="notificationService.hideError"
  />
  
  <SuccessNotification
    :show="successState.show"
    :title="successState.title"
    :message="successState.message"
    @close="notificationService.hideSuccess"
  />
  
  <LoadingNotification />
</template>

<style scoped>
/* ===================================
   CONTENEUR PRINCIPAL
   =================================== */
.app-container {
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  position: relative;
  background: radial-gradient(ellipse at center, #667eea 0%, #764ba2 100%);
}

.map-container {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

/* ===================================
   MODAL DE CONNEXITÉ
   =================================== */
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
  z-index: 2000;
  backdrop-filter: blur(5px);
}

.modal-content {
  max-width: 500px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  padding: var(--spacing-xl);
  border-radius: var(--border-radius-xl);
  background: var(--primary-gradient);
  color: white;
}

.modal-header {
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.modal-header h3 {
  font-size: 20px;
  font-weight: 600;
  margin: 0;
  color: white;
}

.close-button {
  font-size: 18px;
  width: 32px;
  height: 32px;
  padding: 0;
  border-radius: var(--border-radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-body {
  margin-bottom: var(--spacing-lg);
}

.modal-button {
  width: 100%;
  margin-top: var(--spacing-md);
  font-size: 14px;
  font-weight: 600;
}

.connexity-results {
  margin-top: var(--spacing-md);
  padding: var(--spacing-lg);
  border-radius: var(--border-radius-md);
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm) 0;
  color: rgba(255, 255, 255, 0.95);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.result-item:last-child {
  border-bottom: none;
}

.result-label {
  font-weight: 600;
  font-size: 14px;
}

.result-value {
  font-weight: 500;
  font-size: 14px;
  text-align: right;
  max-width: 60%;
}

.result-value.connected {
  color: var(--success-color);
  font-weight: 600;
}

.text-error {
  color: var(--error-color);
}

/* ===================================
   SUGGESTIONS DANS LA MODAL
   =================================== */
.modal-content .suggestions-list {
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

.modal-content .suggestion-item {
  padding: var(--spacing-sm) var(--spacing-md);
  cursor: pointer;
  color: rgba(0, 0, 0, 0.8);
  transition: var(--transition-fast);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-content .suggestion-item:hover {
  background: rgba(0, 0, 0, 0.1);
}

.modal-content .suggestion-lines {
  display: flex;
  gap: 4px;
}

/* ===================================
   PANNEAUX FLOTTANTS
   =================================== */
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
  display: flex;
  flex-direction: column;
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
  flex: 1 1 auto;
  overflow-y: auto;
  max-height: calc(100vh - 80px);
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

.fade-in {
  animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ===================================
   EN-TÊTES DE PANNEAUX
   =================================== */
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

.back-button {
  background: none;
  border: none;
  color: white;
  font-size: 22px;
  font-weight: bold;
  cursor: pointer;
  padding: 0 8px 0 0;
  transition: color 0.2s;
  outline: none;
}

.back-button:hover {
  color: #ffd700;
}

.total-time-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.3), rgba(76, 175, 80, 0.2));
  border-radius: 12px;
  border: 1px solid rgba(76, 175, 80, 0.4);
  backdrop-filter: blur(20px);
  font-weight: 600;
  color: rgba(255, 255, 255, 0.98);
  box-shadow: 0 4px 16px rgba(76, 175, 80, 0.3);
}

.sort-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  padding: 8px 12px;
  background: rgba(76, 175, 80, 0.15);
  border: 1px solid rgba(76, 175, 80, 0.3);
  border-radius: 8px;
  backdrop-filter: blur(10px);
}

.sort-indicator-icon {
  width: 16px;
  height: 16px;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  opacity: 0.9;
}

.sort-indicator-text {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  letter-spacing: 0.3px;
}

/* ===================================
   INFORMATIONS VOYAGE
   =================================== */
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
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.2px;
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

.info-icon {
  width: 16px;
  height: 16px;
  background-size: contain;
  opacity: 0.8;
  margin-bottom: 4px;
}

.time-icon {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cpolyline points='12 6 12 12 16 14'%3E%3C/polyline%3E%3C/svg%3E");
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

/* ===================================
   TIMELINE ET SEGMENTS
   =================================== */
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

.segment-air-conditioning,
.segment-partial-air-conditioning,
.segment-no-air-conditioning {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
  background: rgba(255, 255, 255, 0.15);
  padding: 4px 10px;
  border-radius: 8px;
  flex-shrink: 0;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.segment-air-conditioning {
  background-color: rgba(0, 255, 0, 0.2);
}

.segment-partial-air-conditioning {
  background-color: rgba(255, 193, 7, 0.2);
}

.segment-no-air-conditioning {
  background-color: rgba(255, 0, 0, 0.2);
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

/* ===================================
   STATIONS ET HORAIRES
   =================================== */
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
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.2px;
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

.time-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
  align-items: center;
}

.time-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.2px;
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

/* ===================================
   INFORMATIONS TEMPORELLES
   =================================== */
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

/* ===================================
   CORRESPONDANCES ET TRANSFERTS
   =================================== */
.transfer-info {
  margin: 16px 0;
  border-radius: 16px;
  overflow: hidden;
}

.transfer-badge {
  background: linear-gradient(135deg, rgba(255, 152, 0, 0.3), rgba(255, 152, 0, 0.2));
  border: 1px solid rgba(255, 152, 0, 0.4);
  border-radius: 16px;
  padding: 16px;
  backdrop-filter: blur(25px);
  box-shadow: 0 8px 32px rgba(255, 152, 0, 0.2);
  color: rgba(255, 255, 255, 0.95);
}

.transfer-header-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.transfer-icon-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.transfer-icon {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.9);
}

.transfer-title {
  font-size: 16px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
}

.transfer-time {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
  background: rgba(255, 255, 255, 0.15);
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.transfer-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
}

.transfer-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  width: 100%;
  text-align: center;
}

.transfer-label {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  letter-spacing: 0.2px;
}

.transfer-value {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
}

.transfer-arrow {
  font-size: 20px;
  font-weight: bold;
  color: rgba(255, 255, 255, 0.8);
  margin: 4px 0;
}

.transfer-panel {
  margin-top: 12px;
  padding: 16px;
  background: linear-gradient(135deg, rgba(255, 193, 7, 0.3), rgba(255, 193, 7, 0.2));
  border: 1px solid rgba(255, 193, 7, 0.4);
  border-radius: 12px;
  backdrop-filter: blur(20px);
  color: rgba(255, 255, 255, 0.95);
}

.transfer-panel .transfer-header {
  margin-bottom: 12px;
  text-align: center;
}

.transfer-panel .transfer-title {
  font-size: 15px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
  letter-spacing: 0.2px;
}

.transfer-panel .transfer-details {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 16px;
}

.transfer-panel .transfer-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.transfer-panel .transfer-label {
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
}

.transfer-panel .transfer-value {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
}

.transfer-progress {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, rgba(76, 175, 80, 0.8), rgba(76, 175, 80, 0.6));
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
  text-align: center;
  letter-spacing: 0.2px;
}

/* ===================================
   ALTERNATIVES
   =================================== */
.alternative-paths-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 16px;
}

.alternative-path-summary {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.12), rgba(255, 255, 255, 0.08));
  border: 1.5px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  backdrop-filter: blur(20px);
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.alternative-path-summary:hover {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.16), rgba(255, 255, 255, 0.12));
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
}

.alt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.alt-number-text {
  font-size: 16px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.alt-emissions-compact {
  display: flex;
  align-items: center;
}

.emissions-badge-compact {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background: linear-gradient(135deg, rgba(76, 175, 80, 0.25), rgba(76, 175, 80, 0.15));
  border: 1px solid rgba(76, 175, 80, 0.3);
  border-radius: 10px;
  backdrop-filter: blur(15px);
}

.emissions-icon-small {
  width: 16px;
  height: 16px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M7 13l3 3 7-7'%3E%3C/path%3E%3Cpath d='M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z'%3E%3C/path%3E%3C/svg%3E");
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  opacity: 0.9;
}

.emissions-value-compact {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
}

.alt-lines-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.alt-lines-label {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  letter-spacing: 0.2px;
}

.alt-lines {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.alt-times-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.alt-times-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.alt-time-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  text-align: center;
}

.alt-time-label {
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  letter-spacing: 0.2px;
}

.alt-time-value {
  font-size: 14px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.alt-selection-indicator {
  position: absolute;
  top: 50%;
  right: 16px;
  transform: translateY(-50%);
  opacity: 0;
  transition: all 0.3s ease;
}

.alternative-path-summary:hover .alt-selection-indicator {
  opacity: 1;
}

.selection-arrow {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(76, 175, 80, 0.2);
  border: 1px solid rgba(76, 175, 80, 0.4);
  border-radius: 50%;
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
  font-weight: 700;
}

/* ===================================
   BADGES DE LIGNES
   =================================== */
.suggestion-line-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
  margin-right: 6px;
  color: #fff;
  box-shadow: 0 1px 2px rgba(0,0,0,0.08);
  border: 2px solid #fff;
  letter-spacing: 0.5px;
}

.metro-badge {
  width: 24px;
  height: 24px;
  border-radius: 50%;
}

.rer-badge {
  width: 26px;
  height: 24px;
  border-radius: 8px;
}

/* ===================================
   ACPM STANDALONE
   =================================== */
.no-results-content {
  text-align: center;
  padding: 40px;
  color: white;
}

.no-results-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 20px auto;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z'%3E%3C/path%3E%3Ccircle cx='12' cy='10' r='3'%3E%3C/circle%3E%3C/svg%3E");
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  opacity: 0.7;
}

.no-results-content h3 {
  margin: 0 0 15px 0;
  color: white;
  font-size: 18px;
  font-weight: 600;
}

.no-results-content p {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
  opacity: 0.8;
}

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

/* ===================================
   RESPONSIVE
   =================================== */
@media (max-width: 768px) {
  .modal-content {
    width: 95%;
    padding: var(--spacing-lg);
  }
  
  .modal-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-sm);
  }
  
  .result-item {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-xs);
  }
  
  .result-value {
    text-align: left;
    max-width: 100%;
  }
}
</style> 