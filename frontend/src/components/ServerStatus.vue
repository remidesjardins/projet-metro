<!--
  MetroCity - Mastercamp 2025
  Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
  Fichier: ServerStatus.vue
  Description: Composant affichant le statut de connexion au serveur backend
-->
<template>
  <div class="server-status">
    <div class="status-indicator" :class="{ 'online': isOnline, 'offline': !isOnline }">
      <div class="status-dot"></div>
      <span class="status-text">{{ isOnline ? 'En ligne' : 'Hors ligne' }}</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../services/api'

const isOnline = ref(false)

async function checkServerStatus() {
  try {
    await api.get('/stations')
    isOnline.value = true
  } catch (error) {
    isOnline.value = false
  }
}

onMounted(() => {
  checkServerStatus()
  // Vérifier le statut toutes les 30 secondes
  setInterval(checkServerStatus, 30000)
})
</script>

<style scoped>
.server-status {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.7);
  border-radius: 20px;
  color: white;
  font-size: 12px;
  font-weight: 500;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ff4444;
  transition: background-color 0.3s ease;
}

.status-indicator.online .status-dot {
  background: #44ff44;
}

.status-text {
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.2px;
}
</style> 