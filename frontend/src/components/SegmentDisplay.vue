<!--
  MetroCity - Mastercamp 2025
  Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
  Fichier: SegmentDisplay.vue
  Description: Composant d'affichage détaillé d'un segment d'itinéraire (trajet sur une ligne)
-->
<template>
  <div class="segment glassmorphism" :style="{ borderLeftColor: segmentColor }">
    <div class="segment-header flex-between">
      <div class="line-info">
        <span class="line-badge" 
              :class="getLineType(segment.line) === 'RER' ? 'rer-badge' : 'metro-badge'"
              :style="{ backgroundColor: segmentColor, color: '#fff' }">
          {{ segment.line }}
        </span>
        <span class="direction">Direction {{ segment.direction }}</span>
      </div>
      
      <!-- Affichage des conditions -->
      <div class="segment-conditions">
        <!-- Correspondance -->
        <div v-if="isInterchange(segmentIndex, segment)" class="correspondence-info glassmorphism-transfer">
          <span class="icon transfer-icon"></span>
          <span class="correspondence-text">
            Correspondance {{ getTransferProgress(segmentIndex, segment) }}
          </span>
          <span class="correspondence-time" :style="{ color: getTransferProgressColor(segmentIndex, segment) }">
            {{ getTotalStopTime(segmentIndex, segment) }}
          </span>
        </div>
        
        <!-- Climatisation -->
        <div v-if="getAirConditioningStatus(segment.line)" class="climate-badge" :class="getAirConditioningClass(segment.line)">
          <span class="climate-icon">❄️</span>
          <span class="climate-text">{{ getAirConditioningText(segment.line) }}</span>
        </div>
      </div>
    </div>

    <!-- Stations du segment -->
    <div class="stations-list">
      <div class="stations-path">
        <!-- Station de départ -->
        <div class="station start-station">
          <div class="station-marker" :style="{ backgroundColor: segmentColor }"></div>
          <div class="station-content">
            <div class="station-name">{{ segment.from_station }}</div>
            <div v-if="searchMode === 'temporal' && segment.departure_time" class="station-time">
              {{ segment.departure_time }}
            </div>
            <div v-if="stationLinesMap[segment.from_station] && stationLinesMap[segment.from_station].length > 1" class="station-lines">
              <span v-for="line in stationLinesMap[segment.from_station]" :key="line" 
                    :class="['station-line-badge', getLineType(line) === 'RER' ? 'rer-badge' : 'metro-badge']"
                    :style="{ backgroundColor: LINE_COLORS[line] || '#1976d2' }">
                {{ line }}
              </span>
            </div>
          </div>
        </div>

        <!-- Indicateur de voyage -->
        <div class="travel-indicator" :style="{ borderColor: segmentColor }">
          <div class="travel-line" :style="{ backgroundColor: segmentColor }"></div>
          <div class="travel-info">
            <span class="travel-duration">{{ formatTime(segment.duration) }}</span>
            <span class="travel-stations">{{ segment.stations ? segment.stations.length - 1 : 0 }} arrêts</span>
          </div>
        </div>

        <!-- Station d'arrivée -->
        <div class="station end-station">
          <div class="station-marker" :style="{ backgroundColor: segmentColor }"></div>
          <div class="station-content">
            <div class="station-name">{{ segment.to_station }}</div>
            <div v-if="searchMode === 'temporal' && segment.arrival_time" class="station-time">
              {{ segment.arrival_time }}
            </div>
            <div v-if="stationLinesMap[segment.to_station] && stationLinesMap[segment.to_station].length > 1" class="station-lines">
              <span v-for="line in stationLinesMap[segment.to_station]" :key="line" 
                    :class="['station-line-badge', getLineType(line) === 'RER' ? 'rer-badge' : 'metro-badge']"
                    :style="{ backgroundColor: LINE_COLORS[line] || '#1976d2' }">
                {{ line }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Stations intermédiaires (optionnel, expansible) -->
    <div v-if="segment.stations && segment.stations.length > 2" class="intermediate-stations">
      <button class="btn-toggle expand-button" @click="showIntermediateStations = !showIntermediateStations">
        <span v-if="!showIntermediateStations">
          Voir {{ segment.stations.length - 2 }} stations intermédiaires
        </span>
        <span v-else>Masquer les stations intermédiaires</span>
        <span class="expand-icon">{{ showIntermediateStations ? '▲' : '▼' }}</span>
      </button>
      
      <div v-if="showIntermediateStations" class="intermediate-list">
        <div v-for="station in segment.stations.slice(1, -1)" :key="station.name || station" class="intermediate-station">
          <div class="intermediate-marker" :style="{ backgroundColor: segmentColor }"></div>
          <div class="intermediate-content">
            <span class="intermediate-name">{{ station.name || station }}</span>
            <span v-if="searchMode === 'temporal' && station.time" class="intermediate-time">
              {{ station.time }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

// Props
const props = defineProps({
  segment: Object,
  segmentIndex: Number,
  searchMode: String,
  stationLinesMap: Object,
  isInterchange: Function,
  getTotalStopTime: Function,
  getTransferTime: Function,
  getWaitTime: Function,
  getTransferProgress: Function,
  getTransferProgressColor: Function,
  getTransferProgressText: Function,
  formatTime: Function,
  darkenColor: Function,
  LINE_COLORS: Object,
  getLineType: Function,
  AIR_CONDITIONED_LINES: Array,
  PARTIAL_AIR_CONDITIONED_LINES: Array
})

// State local
const showIntermediateStations = ref(false)

// Computed
const segmentColor = computed(() => {
  return props.darkenColor(props.LINE_COLORS[props.segment.line] || '#1976d2')
})

// Methods
function getAirConditioningStatus(line) {
  return props.AIR_CONDITIONED_LINES.includes(line) || props.PARTIAL_AIR_CONDITIONED_LINES.includes(line)
}

function getAirConditioningClass(line) {
  if (props.AIR_CONDITIONED_LINES.includes(line)) {
    return 'fully-conditioned'
  } else if (props.PARTIAL_AIR_CONDITIONED_LINES.includes(line)) {
    return 'partially-conditioned'
  }
  return ''
}

function getAirConditioningText(line) {
  if (props.AIR_CONDITIONED_LINES.includes(line)) {
    return 'Climatisé'
  } else if (props.PARTIAL_AIR_CONDITIONED_LINES.includes(line)) {
    return 'Partiellement climatisé'
  }
  return ''
}
</script>

<style scoped>
/* ===================================
   SEGMENT
   =================================== */
.segment {
  padding: var(--spacing-lg);
  border-radius: var(--border-radius-lg);
  border-left: 4px solid;
  transition: var(--transition-smooth);
}

.segment:hover {
  transform: translateX(4px);
  box-shadow: var(--shadow-hover);
}

/* ===================================
   EN-TÊTE DU SEGMENT
   =================================== */
.segment-header {
  margin-bottom: var(--spacing-lg);
  flex-wrap: wrap;
  gap: var(--spacing-sm);
}

.line-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.line-badge {
  padding: 10px 16px;
  border-radius: var(--border-radius-xl);
  font-size: 16px;
  font-weight: 700;
  min-width: 52px;
  text-align: center;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(15px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.3);
  position: relative;
  overflow: hidden;
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
  letter-spacing: 0.2px;
}

.line-badge::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), transparent 50%, rgba(255, 255, 255, 0.1));
  border-radius: inherit;
  z-index: -1;
}

.rer-badge {
  border: 2px solid rgba(255, 255, 255, 0.4);
  border-radius: var(--border-radius-lg);
}

.metro-badge {
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: var(--border-radius-full);
}

.direction {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.85);
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
  letter-spacing: 0.1px;
}

/* ===================================
   CONDITIONS DU SEGMENT
   =================================== */
.segment-conditions {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  align-items: flex-end;
}

.correspondence-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: var(--border-radius-md);
  font-size: 12px;
  font-weight: 600;
}

.correspondence-text {
  color: rgba(255, 255, 255, 0.9);
}

.correspondence-time {
  font-weight: 700;
}

.transfer-icon {
  width: 12px;
  height: 12px;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2'%3E%3Cpath d='M7 13l3 3 7-7'%3E%3C/path%3E%3C/svg%3E");
}

.climate-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: var(--border-radius-lg);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  backdrop-filter: blur(15px);
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.3);
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
}

.fully-conditioned {
  background: rgba(76, 175, 80, 0.2);
  border: 1px solid rgba(76, 175, 80, 0.4);
  color: rgba(255, 255, 255, 0.9);
}

.partially-conditioned {
  background: rgba(255, 152, 0, 0.2);
  border: 1px solid rgba(255, 152, 0, 0.4);
  color: rgba(255, 255, 255, 0.9);
}

.climate-icon {
  font-size: 10px;
}

.climate-text {
  font-size: 9px;
}

/* ===================================
   LISTE DES STATIONS
   =================================== */
.stations-list {
  margin-bottom: var(--spacing-md);
}

.stations-path {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.station {
  display: flex;
  align-items: flex-start;
  gap: var(--spacing-md);
  position: relative;
}

.station-marker {
  width: 16px;
  height: 16px;
  border-radius: var(--border-radius-full);
  border: 3px solid rgba(255, 255, 255, 0.2);
  flex-shrink: 0;
  margin-top: 4px;
  position: relative;
  z-index: 1;
}

.station-content {
  flex: 1;
  padding-bottom: var(--spacing-md);
}

.station-name {
  font-size: 17px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.95);
  margin-bottom: 4px;
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
  letter-spacing: 0.1px;
}

.station-time {
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: var(--spacing-xs);
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
}

.station-lines {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  align-items: center;
  margin-top: 2px;
}



/* ===================================
   INDICATEUR DE VOYAGE
   =================================== */
.travel-indicator {
  position: relative;
  padding: var(--spacing-md) 0;
  margin-left: 8px;
  border-left: 2px dashed;
  margin-bottom: var(--spacing-sm);
}

.travel-line {
  position: absolute;
  left: -1px;
  top: 0;
  bottom: 0;
  width: 2px;
  opacity: 0.6;
}

.travel-info {
  margin-left: var(--spacing-lg);
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.travel-duration {
  font-size: 15px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
}

.travel-stations {
  font-size: 12px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.7);
  text-transform: uppercase;
  letter-spacing: 0.3px;
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
}

/* ===================================
   STATIONS INTERMÉDIAIRES
   =================================== */
.intermediate-stations {
  margin-top: var(--spacing-md);
  padding-top: var(--spacing-md);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.expand-button {
  width: 100%;
  justify-content: space-between;
  font-size: 12px;
  padding: var(--spacing-sm) var(--spacing-md);
  margin-bottom: var(--spacing-sm);
}

.expand-icon {
  font-size: 10px;
  font-weight: 700;
}

.intermediate-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
  padding-left: var(--spacing-lg);
}

.intermediate-station {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-xs);
  background: rgba(255, 255, 255, 0.05);
  border-radius: var(--border-radius-sm);
}

.intermediate-marker {
  width: 8px;
  height: 8px;
  border-radius: var(--border-radius-full);
  opacity: 0.7;
}

.intermediate-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.intermediate-name {
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
}

.intermediate-time {
  font-size: 12px;
  font-weight: 400;
  color: rgba(255, 255, 255, 0.6);
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
}

/* ===================================
   RESPONSIVE
   =================================== */
@media (max-width: 768px) {
  .segment {
    padding: var(--spacing-md);
  }
  
  .segment-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .segment-conditions {
    align-items: flex-start;
    width: 100%;
  }
  
  .station-name {
    font-size: 14px;
  }
  
  .line-badge {
    font-size: 14px;
    padding: 8px 12px;
    min-width: 48px;
  }
  
  .travel-info {
    margin-left: var(--spacing-md);
  }
}
</style> 