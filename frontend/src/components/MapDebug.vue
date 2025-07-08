<!--
  MetroCity - Mastercamp 2025
  Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
  Fichier: MapDebug.vue
  Description: Composant de débogage pour la carte (développement)
-->
<template>
  <div class="debug-container">
    <div class="map-container">
      <l-map
        ref="map"
        :zoom="13"
        :center="[48.8566, 2.3522]"
        :use-global-leaflet="false"
      >
        <l-tile-layer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          layer-type="base"
          name="OpenStreetMap"
        />
      </l-map>
    </div>
  </div>
</template>

<script setup>
import { LMap, LTileLayer } from '@vue-leaflet/vue-leaflet'
import 'leaflet/dist/leaflet.css'
</script>

<style scoped>
.debug-container {
  width: 100%;
  height: 100vh;
}

.map-container {
  width: 100%;
  height: 100%;
}
</style> 