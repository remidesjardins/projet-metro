<!--
  MetroCity - Mastercamp 2025
  Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
  Fichier: AlternativePathsSelector.vue
  Description: Composant pour sélectionner parmi les chemins alternatifs trouvés
-->
<template>
  <div v-if="alternativePaths && alternativePaths.length > 0 && selectedAlternativeIndex === null" 
       class="floating-panel fade-in glassmorphism">
    <div class="content-wrapper">
      <div class="path-panel-header flex-between">
        <h2>Meilleurs itinéraires</h2>
        <div class="sort-indicator" v-if="searchMode === 'temporal'">
          <span class="icon" :class="sortCriterion === 'emissions' ? 'emissions-icon' : 'time-icon'"></span>
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
          @click="$emit('selectAlternativePath', idx)"
        >
          <!-- En-tête avec numéro d'itinéraire -->
          <div class="alt-header flex-between">
            <div class="alt-number">
              <span class="alt-number-text">Itinéraire {{ idx + 1 }}</span>
            </div>
            <div class="alt-emissions-compact">
              <div class="emissions-badge-compact badge badge-success">
                <span class="icon emissions-icon"></span>
                <span class="emissions-value-compact">{{ alt.emissions || 0 }}g CO₂</span>
              </div>
            </div>
          </div>
          
          <!-- Lignes utilisées -->
          <div class="alt-lines-section">
            <div class="alt-lines-label">Lignes :</div>
            <div class="alt-lines">
              <span v-for="line in getUniqueLines(alt.segments)" :key="line" 
                :class="['suggestion-line-badge', getLineType(line) === 'RER' ? 'rer-badge' : 'metro-badge']" 
                :style="{ backgroundColor: LINE_COLORS[line] || '#1976d2', color: '#fff' }">
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
</template>

<script setup>
import { 
  LINE_COLORS, 
  getLineType, 
  getUniqueLines 
} from '../constants/metro'

// Props
const props = defineProps({
  alternativePaths: Array,
  selectedAlternativeIndex: Number,
  searchMode: String,
  sortCriterion: String,
  formatTime: Function
})

// Émissions d'événements
const emit = defineEmits([
  'selectAlternativePath'
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
  width: 380px;
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

.sort-indicator {
  display: flex;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-xs) var(--spacing-sm);
  background: rgba(76, 175, 80, 0.15);
  border: 1px solid rgba(76, 175, 80, 0.3);
  border-radius: var(--border-radius-md);
  backdrop-filter: blur(10px);
}

.sort-indicator-text {
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* ===================================
   LISTE DES ALTERNATIVES
   =================================== */
.alternative-paths-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.alternative-path-summary {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.25);
  border-radius: var(--border-radius-lg);
  padding: var(--spacing-lg);
  cursor: pointer;
  transition: var(--transition-smooth);
  position: relative;
  overflow: hidden;
  backdrop-filter: blur(20px);
}

.alternative-path-summary:hover {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.35);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.alternative-path-summary.selected {
  background: rgba(76, 175, 80, 0.2);
  border-color: rgba(76, 175, 80, 0.4);
}

/* ===================================
   EN-TÊTE D'ALTERNATIVE
   =================================== */
.alt-header {
  margin-bottom: var(--spacing-md);
}

.alt-number {
  display: flex;
  align-items: center;
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
  font-size: 12px;
  padding: 5px 10px;
}

.emissions-value-compact {
  font-weight: 600;
}

/* ===================================
   LIGNES UTILISÉES
   =================================== */
.alt-lines-section {
  margin-bottom: var(--spacing-md);
}

.alt-lines-label {
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: var(--spacing-xs);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.alt-lines {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}



/* ===================================
   INFORMATIONS TEMPORELLES
   =================================== */
.alt-times-section {
  margin-bottom: var(--spacing-sm);
}

.alt-times-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-sm);
}

.alt-time-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--spacing-xs);
  background: rgba(255, 255, 255, 0.1);
  border-radius: var(--border-radius-md);
}

.alt-time-label {
  font-size: 10px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.8);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 2px;
}

.alt-time-value {
  font-size: 13px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

/* ===================================
   INDICATEUR DE SÉLECTION
   =================================== */
.alt-selection-indicator {
  position: absolute;
  top: 50%;
  right: var(--spacing-md);
  transform: translateY(-50%);
  opacity: 0;
  transition: var(--transition-smooth);
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
  border-radius: var(--border-radius-full);
  color: rgba(255, 255, 255, 0.9);
  font-size: 16px;
  font-weight: 700;
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
    gap: var(--spacing-sm);
  }
  
  .path-panel-header h2 {
    font-size: 18px;
  }
  
  .alt-times-grid {
    grid-template-columns: 1fr;
    gap: var(--spacing-xs);
  }
  
  .alt-time-item {
    flex-direction: row;
    justify-content: space-between;
    text-align: left;
  }
  
  .alternative-path-summary {
    padding: var(--spacing-md);
  }
}
</style> 