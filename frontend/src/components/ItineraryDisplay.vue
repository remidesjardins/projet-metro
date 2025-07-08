<!--
  MetroCity - Mastercamp 2025
  Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
  Fichier: ItineraryDisplay.vue
  Description: Composant d'affichage détaillé de l'itinéraire sélectionné
-->
<template>
  <div v-if="shouldShowItinerary" class="floating-panel fade-in glassmorphism">
    <div class="content-wrapper">
      <!-- En-tête de l'itinéraire -->
      <div class="path-panel-header flex-between">
        <button v-if="alternativePaths.length > 0" 
                class="btn-primary back-button" 
                @click="$emit('goBackToAlternatives')" 
                title="Retour aux choix">
          ←
        </button>
        <h2>Itinéraire {{ searchMode === 'temporal' ? 'temporel' : '' }}</h2>
        <div class="badge badge-success total-time-badge">
          <span class="icon time-icon"></span>
          {{ formatTime(pathLength) }}
        </div>
      </div>

      <!-- Informations temporelles spécifiques -->
      <div v-if="searchMode === 'temporal' && temporalData" class="temporal-info glassmorphism">
        <div class="temporal-details">
          <div class="detail-item">
            <span class="icon clock-icon"></span>
            <span>Départ: {{ temporalData.departure_time }}</span>
          </div>
          <div class="detail-item">
            <span class="icon clock-icon"></span>
            <span>Arrivée: {{ temporalData.arrival_time }}</span>
          </div>
          <div class="detail-item">
            <span class="icon wait-icon"></span>
            <span>Temps d'attente: {{ formatTime(temporalData.total_wait_time) }}</span>
          </div>
        </div>
      </div>

      <!-- Panneau d'informations du voyage -->
      <div class="trip-info-panel glassmorphism">
        <div class="info-item">
          <span class="icon time-icon"></span>
          <span class="info-label">Durée</span>
          <span class="info-value">{{ formatTime(pathLength) }}</span>
        </div>
        <div class="info-item">
          <span class="icon emissions-icon"></span>
          <span class="info-label">Émissions</span>
          <span class="info-value">{{ pathLength?.emissions || 0 }}g CO₂</span>
        </div>
        <div class="info-item">
          <span class="icon stations-icon"></span>
          <span class="info-label">Stations</span>
          <span class="info-value">{{ getTotalStations() }}</span>
        </div>
        <!-- Affichage du temps total ACPM quand activé -->
        <div v-if="showACPM && acpmTotalWeight" class="info-item acpm-info glassmorphism-warning">
          <span class="icon acpm-icon"></span>
          <span class="info-label">ACPM Total</span>
          <span class="info-value">{{ formatACPMTime(acpmTotalWeight) }}</span>
        </div>
      </div>

      <!-- Timeline des segments -->
      <div class="timeline">
        <SegmentDisplay
          v-for="(segment, index) in pathDetails"
          :key="index"
          :segment="segment"
          :segmentIndex="index"
          :searchMode="searchMode"
          :stationLinesMap="stationLinesMap"
          :isInterchange="isInterchange"
          :getTotalStopTime="getTotalStopTime"
          :getTransferTime="getTransferTime"
          :getWaitTime="getWaitTime"
          :getTransferProgress="getTransferProgress"
          :getTransferProgressColor="getTransferProgressColor"
          :getTransferProgressText="getTransferProgressText"
          :formatTime="formatTime"
          :darkenColor="darkenColor"
          :LINE_COLORS="LINE_COLORS"
          :getLineType="getLineType"
          :AIR_CONDITIONED_LINES="AIR_CONDITIONED_LINES"
          :PARTIAL_AIR_CONDITIONED_LINES="PARTIAL_AIR_CONDITIONED_LINES"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import SegmentDisplay from './SegmentDisplay.vue'
import { 
  LINE_COLORS, 
  AIR_CONDITIONED_LINES, 
  PARTIAL_AIR_CONDITIONED_LINES, 
  getLineType
} from '../constants/metro'
import { computed } from 'vue'

// Props
const props = defineProps({
  selectedAlternativeIndex: Number,
  pathDetails: Array,
  pathLength: [Number, Object],
  alternativePaths: Array,
  temporalData: Object,
  searchMode: String,
  stationLinesMap: Object,
  showACPM: Boolean,
  acpmTotalWeight: Number,
  formatTime: Function,
  formatACPMTime: Function,
  darkenColor: Function,
  getTotalStations: Function,
  isInterchange: Function,
  getTotalStopTime: Function,
  getTransferTime: Function,
  getWaitTime: Function,
  getTransferProgress: Function,
  getTransferProgressColor: Function,
  getTransferProgressText: Function
})

// Computed
const shouldShowItinerary = computed(() => {
  return (props.selectedAlternativeIndex !== null && props.pathDetails && props.pathDetails.length > 0) || 
         (props.alternativePaths.length === 0 && props.pathDetails && props.pathDetails.length > 0)
})

// Émissions d'événements
const emit = defineEmits([
  'goBackToAlternatives'
])
</script>

<style scoped>
/* ===================================
   PANNEAU FLOTTANT
   =================================== */
.floating-panel {
  position: fixed;
  top: 80px;
  right: 20px;
  z-index: 999;
  width: 450px;
  max-height: calc(100vh - 100px);
  background: var(--primary-gradient);
  border-radius: var(--border-radius-xl);
  border: 1px solid rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(25px);
  box-shadow: var(--shadow-glass);
  overflow: hidden;
}

.content-wrapper {
  padding: var(--spacing-xl);
  overflow-y: auto;
  max-height: calc(100vh - 100px);
}

/* ===================================
   EN-TÊTE DU PANNEAU
   =================================== */
.path-panel-header {
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  flex-wrap: wrap;
  gap: var(--spacing-sm);
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
  padding: var(--spacing-sm) var(--spacing-md);
  margin-right: var(--spacing-md);
  font-size: 18px;
  font-weight: 700;
  border-radius: var(--border-radius-md);
}

.total-time-badge {
  font-weight: 600;
  font-size: 15px;
}

/* ===================================
   INFORMATIONS TEMPORELLES
   =================================== */
.temporal-info {
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-lg);
  border-radius: var(--border-radius-lg);
}

.temporal-details {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
}

.detail-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.9);
}

/* ===================================
   PANNEAU D'INFORMATIONS DU VOYAGE
   =================================== */
.trip-info-panel {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: var(--spacing-sm);
  margin-bottom: var(--spacing-lg);
  padding: var(--spacing-lg);
  border-radius: var(--border-radius-lg);
}

.info-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-sm);
  background: rgba(255, 255, 255, 0.15);
  border-radius: var(--border-radius-md);
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: var(--transition-smooth);
  text-align: center;
}

.info-item:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

.info-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  color: rgba(255, 255, 255, 0.9);
  white-space: nowrap;
}

.info-value {
  font-size: 14px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.98);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  white-space: nowrap;
}

.acpm-info {
  border-color: rgba(255, 193, 7, 0.3);
}

/* ===================================
   TIMELINE
   =================================== */
.timeline {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

/* ===================================
   RESPONSIVE
   =================================== */
@media (max-width: 768px) {
  .floating-panel {
    right: 10px;
    left: 10px;
    width: auto;
    top: 60px;
    max-height: calc(100vh - 80px);
  }
  
  .content-wrapper {
    padding: var(--spacing-lg);
    max-height: calc(100vh - 80px);
  }
  
  .path-panel-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .path-panel-header h2 {
    font-size: 18px;
  }
  
  .trip-info-panel {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .info-item {
    flex-direction: row;
    justify-content: space-between;
    text-align: left;
  }
  
  .temporal-details {
    gap: var(--spacing-xs);
  }
  
  .detail-item {
    font-size: 13px;
  }
}
</style> 