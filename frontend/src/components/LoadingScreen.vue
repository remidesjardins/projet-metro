<!--
  MetroCity - Mastercamp 2025
  Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
  Fichier: LoadingScreen.vue
  Description: Écran de chargement initial de l'application
-->
<template>
  <div class="loading-screen" v-if="isLoading">
    <div class="loading-container glass">
      <!-- Logo ou titre -->
      <div class="loading-header">
        <div class="metro-logo">
          <div class="metro-icon">🚇</div>
          <h1 class="app-title">Métro Parisien</h1>
        </div>
        <p class="loading-subtitle">Chargement des données en cours...</p>
      </div>

      <!-- Barre de progression -->
      <div class="progress-container">
        <div class="progress-bar glass-bar">
          <div 
            class="progress-fill liquid-glass" 
            :style="{ width: `${progress}%` }"
          ></div>
        </div>
        <div class="progress-text">
          <span class="progress-percentage">{{ progress }}%</span>
          <span class="progress-step">{{ currentStep }}</span>
        </div>
      </div>

      <!-- Étapes de chargement -->
      <div class="loading-steps">
        <div 
          v-for="(step, index) in steps" 
          :key="index"
          :class="['loading-step', { 
            'completed': index < currentStepIndex,
            'current': index === currentStepIndex,
            'pending': index > currentStepIndex
          }]"
        >
          <div class="step-icon">
            <span v-if="index < currentStepIndex" class="check-icon">✓</span>
            <span v-else-if="index === currentStepIndex" class="loading-icon">⟳</span>
            <span v-else class="pending-icon">○</span>
          </div>
          <span class="step-text">{{ step }}</span>
        </div>
      </div>

      <!-- Animation de chargement -->
      <div class="loading-animation">
        <div class="metro-train glass-bar">
          <div class="train-body">
            <div class="train-window"></div>
            <div class="train-window"></div>
            <div class="train-window"></div>
          </div>
        </div>
        <div class="track glass-bar"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { api } from '../services/api'

const isLoading = ref(true)
const progress = ref(0)
const currentStep = ref('Initialisation...')
const currentStepIndex = ref(0)
const steps = ref([
  'Initialisation',
  'Chargement des routes',
  'Chargement des trips',
  'Chargement des stop_times',
  'Chargement des stops',
  'Fusion des stations physiques',
  'Construction du graphe',
  'Finalisation'
])

let statusInterval = null
let errorCount = 0

const checkLoadingStatus = async () => {
  try {
    const response = await api.get('/loading-status')
    const status = response
    
    isLoading.value = status.is_loading
    progress.value = status.progress
    currentStep.value = status.current_step
    
    // Calculer l'index de l'étape actuelle
    currentStepIndex.value = Math.floor((status.progress / 100) * (steps.value.length - 1))
    
    // Si le chargement est terminé, arrêter le polling
    if (!status.is_loading && status.progress === 100) {
      clearInterval(statusInterval)
      // Attendre un peu avant de masquer l'écran
      setTimeout(() => {
        isLoading.value = false
      }, 1000)
    }
  } catch (error) {
    // Erreur lors de la vérification du statut de chargement
    
    // Si on a trop d'erreurs consécutives, arrêter le polling
    if (errorCount > 5) {
      // Trop d'erreurs, arrêt du polling de statut
      clearInterval(statusInterval)
      setTimeout(() => {
        isLoading.value = false
      }, 3000)
      return
    }
    
    errorCount++
    
    // En cas d'erreur, masquer l'écran après un délai plus long
    setTimeout(() => {
      isLoading.value = false
    }, 5000)
  }
}

onMounted(() => {
  // Vérifier le statut toutes les 2 secondes au lieu de 500ms
  statusInterval = setInterval(checkLoadingStatus, 2000)
  // Vérifier immédiatement
  checkLoadingStatus()
})

onUnmounted(() => {
  if (statusInterval) {
    clearInterval(statusInterval)
  }
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;600;700&display=swap');

.loading-screen {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: linear-gradient(135deg, #e0e7ef 0%, #c9d6ff 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  font-family: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif;
}

.loading-container.glass {
  background: rgba(255, 255, 255, 0.35);
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.18);
  backdrop-filter: blur(18px) saturate(180%);
  -webkit-backdrop-filter: blur(18px) saturate(180%);
  border-radius: 32px;
  border: 1.5px solid rgba(255,255,255,0.25);
  padding: 48px;
  text-align: center;
  max-width: 500px;
  width: 90%;
  transition: box-shadow 0.3s;
}

.loading-header {
  margin-bottom: 32px;
}

.metro-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin-bottom: 16px;
}

.metro-icon {
  font-size: 48px;
  animation: bounce 2s infinite;
  filter: drop-shadow(0 2px 8px #b3b3b3);
}

.app-title {
  font-size: 32px;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0;
  letter-spacing: -1px;
  text-shadow: 0 2px 8px rgba(255,255,255,0.2);
}

.loading-subtitle {
  font-size: 16px;
  color: #666;
  margin: 0;
  text-shadow: 0 1px 4px rgba(255,255,255,0.2);
}

.progress-container {
  margin-bottom: 32px;
}

.progress-bar.glass-bar {
  width: 100%;
  height: 12px;
  background: rgba(255,255,255,0.18);
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 12px;
  box-shadow: 0 2px 8px rgba(31, 38, 135, 0.10);
  border: 1px solid rgba(255,255,255,0.25);
}

.progress-fill.liquid-glass {
  height: 100%;
  background: linear-gradient(90deg, #a1c4fd 0%, #c2e9fb 100%);
  border-radius: 8px;
  transition: width 0.3s cubic-bezier(.4,2,.6,1);
  position: relative;
  box-shadow: 0 2px 12px 0 rgba(100, 180, 255, 0.18);
  overflow: hidden;
}

.progress-fill.liquid-glass::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.35), transparent);
  animation: shimmer 2s infinite;
}

.progress-text {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 15px;
  font-weight: 500;
  color: #3a3a3a;
  text-shadow: 0 1px 4px rgba(255,255,255,0.2);
}

.progress-percentage {
  font-weight: 600;
  color: #4a90e2;
}

.progress-step {
  color: #666;
  max-width: 60%;
  text-align: right;
}

.loading-steps {
  margin-bottom: 32px;
}

.loading-step {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  font-size: 15px;
  transition: all 0.3s ease;
}

.step-icon {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 13px;
  font-weight: bold;
  background: rgba(255,255,255,0.25);
  box-shadow: 0 1px 4px rgba(31, 38, 135, 0.10);
}

.check-icon {
  color: #4CAF50;
  animation: checkmark 0.5s ease;
}

.loading-icon {
  color: #4a90e2;
  animation: spin 1s linear infinite;
}

.pending-icon {
  color: #ccc;
}

.step-text {
  color: #333;
  text-shadow: 0 1px 4px rgba(255,255,255,0.2);
}

.loading-step.completed .step-text {
  color: #4CAF50;
  font-weight: 500;
}

.loading-step.current .step-text {
  color: #4a90e2;
  font-weight: 600;
}

.loading-step.pending .step-text {
  color: #999;
}

.loading-animation {
  position: relative;
  height: 60px;
  margin-top: 24px;
}

.metro-train.glass-bar {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 40px;
  animation: train-move 3s ease-in-out infinite;
  background: rgba(255,255,255,0.18);
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(31, 38, 135, 0.10);
}

.train-body {
  width: 80px;
  height: 24px;
  background: linear-gradient(90deg, #e0e7ef 0%, #c9d6ff 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: space-around;
  padding: 0 8px;
  margin: 0 auto;
  box-shadow: 0 2px 8px rgba(31, 38, 135, 0.10);
}

.train-window {
  width: 12px;
  height: 12px;
  background: #b3e0ff;
  border-radius: 50%;
  animation: window-glow 2s ease-in-out infinite alternate;
  box-shadow: 0 0 8px #b3e0ff;
}

.track.glass-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 5px;
  background: rgba(31, 38, 135, 0.10);
  border-radius: 2px;
  box-shadow: 0 1px 4px rgba(31, 38, 135, 0.10);
}

@keyframes bounce {
  0%, 20%, 50%, 80%, 100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-10px);
  }
  60% {
    transform: translateY(-5px);
  }
}

@keyframes shimmer {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

@keyframes checkmark {
  0% {
    transform: scale(0);
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

@keyframes train-move {
  0%, 100% {
    transform: translateX(-100%);
  }
  50% {
    transform: translateX(100%);
  }
}

@keyframes window-glow {
  0% {
    opacity: 0.7;
    box-shadow: 0 0 5px #b3e0ff;
  }
  100% {
    opacity: 1;
    box-shadow: 0 0 15px #b3e0ff;
  }
}

/* Responsive */
@media (max-width: 768px) {
  .loading-container.glass {
    padding: 32px 16px;
    margin: 20px;
  }
  .app-title {
    font-size: 24px;
  }
  .metro-icon {
    font-size: 36px;
  }
  .progress-step {
    max-width: 50%;
    font-size: 12px;
  }
}
</style> 