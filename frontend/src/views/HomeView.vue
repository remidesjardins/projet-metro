<script setup>
import MetroMapLeaflet from '../components/MetroMapLeaflet.vue'
import { ref, provide } from 'vue'

const pathDetails = ref([])
const pathLength = ref(null)

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

// Fournir ces valeurs aux composants enfants
provide('pathDetails', pathDetails)
provide('pathLength', pathLength)
</script>

<template>
  <main>
    <h1>Carte interactive du métro de Paris</h1>
    <div class="content">
      <MetroMapLeaflet />
      <div v-if="pathDetails && pathDetails.length > 0" class="path-summary">
        <h2>Résumé de l'itinéraire</h2>
        <div class="path-segments">
          <div v-for="(segment, index) in pathDetails" :key="index" class="path-segment">
            <div class="segment-header" :style="{ backgroundColor: LINE_COLORS[segment.line] || '#000000' }">
              <span class="line-number">Ligne {{ segment.line }}</span>
              <span class="segment-duration">{{ Math.round(segment.duration) }} min</span>
            </div>
            <div class="segment-stations">
              <div v-for="(station, stationIndex) in segment.stations" 
                   :key="stationIndex"
                   class="station-name"
                   :class="{ 'transfer': stationIndex > 0 && stationIndex < segment.stations.length - 1 }">
                {{ station }}
              </div>
            </div>
          </div>
        </div>
        <div class="total-duration">
          Durée totale : {{ pathLength }} minutes
        </div>
      </div>
    </div>
  </main>
</template>

<style scoped>
main {
  padding: 2rem 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

h1 {
  margin-bottom: 2rem;
  font-size: 2rem;
  font-weight: 700;
  color: #1976d2;
}

.content {
  width: 100%;
  display: flex;
  gap: 2rem;
  padding: 0 2rem;
}

.path-summary {
  flex: 1;
  max-width: 400px;
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}

.path-summary h2 {
  margin: 0 0 1.5rem 0;
  color: #333;
  font-size: 1.5rem;
}

.path-segments {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.path-segment {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.segment-header {
  padding: 0.75rem 1rem;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.line-number {
  font-size: 1.1em;
}

.segment-duration {
  background: rgba(255, 255, 255, 0.2);
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
}

.segment-stations {
  padding: 1rem;
  background: white;
}

.station-name {
  padding: 0.5rem 0;
  border-bottom: 1px solid #eee;
}

.station-name:last-child {
  border-bottom: none;
}

.station-name.transfer {
  color: #666;
  font-style: italic;
}

.total-duration {
  margin-top: 1.5rem;
  padding: 1rem;
  background: #f5f5f5;
  border-radius: 4px;
  text-align: center;
  font-weight: bold;
}

@media (max-width: 1024px) {
  .content {
    flex-direction: column;
  }
  
  .path-summary {
    max-width: none;
    margin-top: 1rem;
  }
}
</style>
