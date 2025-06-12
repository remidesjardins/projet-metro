<template>
  <div class="server-status" :class="{ 'online': isOnline, 'offline': !isOnline }">
    <div class="status-indicator"></div>
    <span>{{ isOnline ? 'Serveur connecté' : 'Serveur déconnecté' }}</span>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { api } from '../services/api';

const isOnline = ref(false);
let checkInterval;

async function checkServerStatus() {
  try {
    await fetch('http://localhost:5050/stations', { method: 'HEAD' });
    isOnline.value = true;
  } catch (error) {
    isOnline.value = false;
    console.error('Erreur de connexion au serveur:', error);
  }
}

onMounted(() => {
  checkServerStatus();
  checkInterval = setInterval(checkServerStatus, 10000);
});

onUnmounted(() => {
  clearInterval(checkInterval);
});
</script>

<style scoped>
.server-status {
  position: fixed;
  bottom: 20px;
  left: 20px;
  padding: 8px 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-radius: 20px;
  font-size: 14px;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(5px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  transition: background-color 0.3s;
}

.online .status-indicator {
  background-color: var(--apple-green);
}

.offline .status-indicator {
  background-color: var(--apple-red);
}
</style> 