<!--
  MetroCity - Mastercamp 2025
  Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
  Fichier: SuccessNotification.vue
  Description: Composant de notification de succès avec animation
-->
<template>
  <Transition name="success-slide" appear>
    <div v-if="show" class="success-notification-overlay" @click="handleOverlayClick">
      <div class="success-notification-container" @click.stop>
        <!-- Icône de succès animée -->
        <div class="success-icon-container">
          <div class="success-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
              <polyline points="22,4 12,14.01 9,11.01"></polyline>
            </svg>
          </div>
        </div>

        <!-- Contenu du succès -->
        <div class="success-content">
          <h3 class="success-title">{{ title }}</h3>
          <p class="success-message">{{ message }}</p>
        </div>

        <!-- Actions -->
        <div class="success-actions">
          <button 
            class="action-button close-button"
            @click="handleClose"
          >
            <span class="button-icon">✓</span>
            <span class="button-text">Continuer</span>
          </button>
        </div>

        <!-- Barre de progression pour l'auto-fermeture -->
        <div v-if="autoClose" class="progress-bar">
          <div 
            class="progress-fill"
            :style="{ width: progressPercentage + '%' }"
          ></div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: 'Succès'
  },
  message: {
    type: String,
    required: true
  },
  autoClose: {
    type: Boolean,
    default: true
  },
  autoCloseDelay: {
    type: Number,
    default: 3000
  }
})

const emit = defineEmits(['close'])

const progressPercentage = ref(0)
let progressInterval = null
let autoCloseTimer = null

// Gestion de l'auto-fermeture
onMounted(() => {
  if (props.autoClose && props.show) {
    startAutoClose()
  }
})

onUnmounted(() => {
  clearTimers()
})

const startAutoClose = () => {
  const startTime = Date.now()
  
  progressInterval = setInterval(() => {
    const elapsed = Date.now() - startTime
    progressPercentage.value = Math.min((elapsed / props.autoCloseDelay) * 100, 100)
    
    if (elapsed >= props.autoCloseDelay) {
      handleClose()
    }
  }, 50)
  
  autoCloseTimer = setTimeout(() => {
    handleClose()
  }, props.autoCloseDelay)
}

const clearTimers = () => {
  if (progressInterval) {
    clearInterval(progressInterval)
    progressInterval = null
  }
  if (autoCloseTimer) {
    clearTimeout(autoCloseTimer)
    autoCloseTimer = null
  }
}

const handleClose = () => {
  clearTimers()
  emit('close')
}

const handleOverlayClick = () => {
  handleClose()
}
</script>

<style scoped>
/* Overlay avec effet de flou */
.success-notification-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

/* Container principal avec glassmorphism */
.success-notification-container {
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.25) 0%, 
    rgba(255, 255, 255, 0.15) 50%, 
    rgba(255, 255, 255, 0.1) 100%);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 24px;
  padding: 32px;
  max-width: 500px;
  width: 100%;
  position: relative;
  overflow: hidden;
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.1),
    0 8px 16px rgba(0, 0, 0, 0.05),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

/* Effet de brillance */
.success-notification-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, 
    rgba(255, 255, 255, 0.1) 0%, 
    transparent 50%, 
    rgba(255, 255, 255, 0.05) 100%);
  border-radius: 24px;
  pointer-events: none;
}

/* Icône de succès animée */
.success-icon-container {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.success-icon {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #4CAF50, #45a049);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  box-shadow: 
    0 8px 16px rgba(76, 175, 80, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  animation: successPulse 2s ease-in-out infinite;
}

.success-icon svg {
  width: 32px;
  height: 32px;
}

@keyframes successPulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 
      0 8px 16px rgba(76, 175, 80, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 
      0 12px 24px rgba(76, 175, 80, 0.4),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
  }
}

/* Contenu du succès */
.success-content {
  text-align: center;
  margin-bottom: 24px;
}

.success-title {
  font-size: 24px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  margin: 0 0 12px 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.success-message {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.5;
  margin: 0;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

/* Actions */
.success-actions {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.action-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: 16px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  border: none;
  position: relative;
  overflow: hidden;
  min-width: 120px;
  justify-content: center;
}

.action-button::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), transparent 50%, rgba(255, 255, 255, 0.05));
  border-radius: 16px;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.action-button:hover::before {
  opacity: 1;
}

.close-button {
  background: linear-gradient(135deg, #4CAF50, #45a049);
  color: white;
  box-shadow: 
    0 4px 12px rgba(76, 175, 80, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.close-button:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 8px 20px rgba(76, 175, 80, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.button-icon {
  font-size: 16px;
}

.button-text {
  font-weight: 600;
  letter-spacing: -0.3px;
}

/* Barre de progression */
.progress-bar {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 0 0 24px 24px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4CAF50, #45a049);
  border-radius: 0 0 24px 24px;
  transition: width 0.1s linear;
}

/* Animations d'entrée/sortie */
.success-slide-enter-active,
.success-slide-leave-active {
  transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.success-slide-enter-from {
  opacity: 0;
  transform: scale(0.8) translateY(20px);
}

.success-slide-leave-to {
  opacity: 0;
  transform: scale(0.9) translateY(-20px);
}

/* Responsive */
@media (max-width: 768px) {
  .success-notification-container {
    margin: 20px;
    padding: 24px;
    max-width: none;
  }
  
  .success-title {
    font-size: 20px;
  }
  
  .success-message {
    font-size: 14px;
  }
  
  .action-button {
    width: 100%;
  }
}
</style> 