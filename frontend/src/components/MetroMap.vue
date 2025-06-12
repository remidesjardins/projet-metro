<template>
  <div class="metro-map-container">
    <img
      src="/metro-map.png"
      alt="Plan du métro"
      class="metro-map-bg"
      ref="mapImg"
      @load="onImageLoad"
    />
    <div
      v-for="station in stations"
      :key="station.id"
      class="station-dot"
      :style="getStationStyle(station)"
      @mouseenter="hoveredStation = station.id"
      @mouseleave="hoveredStation = null"
      @click="selectStation(station)"
    >
      <div v-if="hoveredStation === station.id" class="station-tooltip">
        {{ station.name }}
      </div>
      <div
        :class="['dot', {
          'selected': selectedStart === station.id || selectedEnd === station.id
        }]"
      ></div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const stations = ref([])
const hoveredStation = ref(null)
const selectedStart = ref(null)
const selectedEnd = ref(null)
const mapImg = ref(null)
const mapSize = ref({ width: 1000, height: 800 }) // à ajuster selon l'image réelle

// Charger les stations depuis l'API
async function fetchStations() {
  const res = await fetch('http://localhost:5000/stations')
  const data = await res.json()
  stations.value = data.stations.filter(s => s.position)
}

onMounted(() => {
  fetchStations()
})

function getStationStyle(station) {
  // Adapter les coordonnées à la taille de l'image
  const [x, y] = station.position
  return {
    left: `${(x / 1000) * mapSize.value.width}px`,
    top: `${(y / 800) * mapSize.value.height}px`
  }
}

function onImageLoad() {
  if (mapImg.value) {
    mapSize.value.width = mapImg.value.naturalWidth
    mapSize.value.height = mapImg.value.naturalHeight
  }
}

function selectStation(station) {
  if (!selectedStart.value) {
    selectedStart.value = station.id
  } else if (!selectedEnd.value && station.id !== selectedStart.value) {
    selectedEnd.value = station.id
  } else {
    selectedStart.value = station.id
    selectedEnd.value = null
  }
}
</script>

<style scoped>
.metro-map-container {
  position: relative;
  width: 100%;
  max-width: 1000px;
  margin: 0 auto;
}
.metro-map-bg {
  width: 100%;
  display: block;
}
.station-dot {
  position: absolute;
  transform: translate(-50%, -50%);
  cursor: pointer;
}
.dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #1976d2;
  border: 2px solid #fff;
  box-shadow: 0 0 2px #0008;
  transition: background 0.2s;
}
.dot.selected {
  background: #e53935;
}
.station-tooltip {
  position: absolute;
  top: -28px;
  left: 50%;
  transform: translateX(-50%);
  background: #222;
  color: #fff;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 13px;
  white-space: nowrap;
  pointer-events: none;
  z-index: 2;
}
</style> 