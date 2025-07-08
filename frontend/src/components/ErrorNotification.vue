<!--
  MetroCity - Mastercamp 2025
  Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
  Fichier: ErrorNotification.vue
  Description: Composant de notification d'erreur avec animation et détails
-->
<template>
  <Transition name="error-slide" appear>
    <div v-if="show" class="error-notification-overlay" @click="handleOverlayClick">
      <div class="error-notification-container" @click.stop>
        <!-- Icône d'erreur animée -->
        <div class="error-icon-container">
          <div class="error-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="15" y1="9" x2="9" y2="15"></line>
              <line x1="9" y1="9" x2="15" y2="15"></line>
            </svg>
          </div>
        </div>

        <!-- Contenu de l'erreur -->
        <div class="error-content">
          <h3 class="error-title">{{ title }}</h3>
          <p class="error-message">{{ message }}</p>
          
          <!-- Détails techniques optionnels -->
          <div v-if="details" class="error-details">
            <button 
              class="details-toggle"
              @click="showDetails = !showDetails"
            >
              <span class="toggle-text">{{ showDetails ? 'Masquer' : 'Afficher' }} les détails</span>
              <span class="toggle-icon" :class="{ 'rotated': showDetails }">▼</span>
            </button>
            
            <Transition name="details-expand">
              <div v-if="showDetails" class="details-content">
                <pre class="details-text">{{ details }}</pre>
              </div>
            </Transition>
          </div>
        </div>

        <!-- Actions -->
        <div class="error-actions">
          <button 
            v-if="retryAction"
            class="action-button retry-button"
            @click="handleRetry"
          >
            <span class="button-icon">🔄</span>
            <span class="button-text">Réessayer</span>
          </button>
          
          <button 
            class="action-button close-button"
            @click="handleClose"
          >
            <span class="button-icon">✕</span>
            <span class="button-text">Fermer</span>
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
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: 'Erreur'
  },
  message: {
    type: String,
    required: true
  },
  details: {
    type: String,
    default: null
  },
  retryAction: {
    type: Function,
    default: null
  },
  autoClose: {
    type: Boolean,
    default: false
  },
  autoCloseDelay: {
    type: Number,
    default: 5000
  }
})

const emit = defineEmits(['close', 'retry'])

const showDetails = ref(false)
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
  const endTime = startTime + props.autoCloseDelay
  
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

const handleRetry = () => {
  if (props.retryAction) {
    props.retryAction()
  }
  emit('retry')
}

const handleOverlayClick = () => {
  handleClose()
}
</script>

<style scoped>
/* Overlay avec effet de flou */
.error-notification-overlay {
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
.error-notification-container {
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
.error-notification-container::before {
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

/* Icône d'erreur animée */
.error-icon-container {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.error-icon {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #ff6b6b, #ee5a52);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  box-shadow: 
    0 8px 16px rgba(255, 107, 107, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  animation: errorPulse 2s ease-in-out infinite;
}

.error-icon svg {
  width: 32px;
  height: 32px;
}

@keyframes errorPulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 
      0 8px 16px rgba(255, 107, 107, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 
      0 12px 24px rgba(255, 107, 107, 0.4),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
  }
}

/* Contenu de l'erreur */
.error-content {
  text-align: center;
  margin-bottom: 24px;
}

.error-title {
  font-size: 24px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  margin: 0 0 12px 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.error-message {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.5;
  margin: 0;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

/* Détails techniques */
.error-details {
  margin-top: 20px;
}

.details-toggle {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 8px 16px;
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 auto;
}

.details-toggle:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-1px);
}

.toggle-icon {
  transition: transform 0.3s ease;
  font-size: 12px;
}

.toggle-icon.rotated {
  transform: rotate(180deg);
}

.details-content {
  margin-top: 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.details-text {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.4;
}

/* Actions */
.error-actions {
  display: flex;
  gap: 12px;
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

.retry-button {
  background: linear-gradient(135deg, #4CAF50, #45a049);
  color: white;
  box-shadow: 
    0 4px 12px rgba(76, 175, 80, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.retry-button:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 8px 20px rgba(76, 175, 80, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.close-button {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0.1));
  color: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.close-button:hover {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.15));
  border-color: rgba(255, 255, 255, 0.3);
  transform: translateY(-2px);
  box-shadow: 
    0 8px 20px rgba(0, 0, 0, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
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
  background: linear-gradient(90deg, #ff6b6b, #ee5a52);
  border-radius: 0 0 24px 24px;
  transition: width 0.1s linear;
}

/* Animations d'entrée/sortie */
.error-slide-enter-active,
.error-slide-leave-active {
  transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.error-slide-enter-from {
  opacity: 0;
  transform: scale(0.8) translateY(20px);
}

.error-slide-leave-to {
  opacity: 0;
  transform: scale(0.9) translateY(-20px);
}

/* Animation pour les détails */
.details-expand-enter-active,
.details-expand-leave-active {
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  overflow: hidden;
}

.details-expand-enter-from,
.details-expand-leave-to {
  opacity: 0;
  max-height: 0;
  transform: translateY(-10px);
}

.details-expand-enter-to,
.details-expand-leave-from {
  opacity: 1;
  max-height: 200px;
  transform: translateY(0);
}

/* Responsive */
@media (max-width: 768px) {
  .error-notification-container {
    margin: 20px;
    padding: 24px;
    max-width: none;
  }
  
  .error-title {
    font-size: 20px;
  }
  
  .error-message {
    font-size: 14px;
  }
  
  .error-actions {
    flex-direction: column;
  }
  
  .action-button {
    width: 100%;
  }
}
</style> 