<template>
  <Transition name="loading-slide" appear>
    <div v-if="show" class="loading-notification-overlay">
      <div class="loading-notification-container">
        <!-- Icône de chargement animée -->
        <div class="loading-icon-container">
          <div class="loading-icon">
            <div class="spinner">
              <div class="spinner-ring"></div>
              <div class="spinner-ring"></div>
              <div class="spinner-ring"></div>
            </div>
          </div>
        </div>

        <!-- Contenu du chargement -->
        <div class="loading-content">
          <h3 class="loading-title">{{ title }}</h3>
          <p class="loading-message">{{ message }}</p>
          
          <!-- Barre de progression si fournie -->
          <div v-if="showProgress" class="progress-container">
            <div class="progress-bar">
              <div 
                class="progress-fill"
                :style="{ width: progressPercentage + '%' }"
              ></div>
            </div>
            <span class="progress-text">{{ progressPercentage }}%</span>
          </div>
          
          <!-- Indicateur de progression textuel -->
          <div v-if="currentStep && totalSteps" class="step-indicator">
            <span class="step-text">Étape {{ currentStep }} sur {{ totalSteps }}</span>
          </div>
        </div>

        <!-- Bouton d'annulation optionnel -->
        <div v-if="canCancel" class="loading-actions">
          <button 
            class="cancel-button"
            @click="handleCancel"
          >
            <span class="button-icon">✕</span>
            <span class="button-text">Annuler</span>
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: 'Chargement en cours'
  },
  message: {
    type: String,
    default: 'Veuillez patienter...'
  },
  progress: {
    type: Number,
    default: 0
  },
  currentStep: {
    type: Number,
    default: null
  },
  totalSteps: {
    type: Number,
    default: null
  },
  canCancel: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['cancel'])

const progressPercentage = computed(() => {
  return Math.min(Math.max(props.progress, 0), 100)
})

const showProgress = computed(() => {
  return props.progress > 0 && props.progress <= 100
})

const handleCancel = () => {
  emit('cancel')
}
</script>

<style scoped>
/* Overlay avec effet de flou */
.loading-notification-overlay {
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
.loading-notification-container {
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
.loading-notification-container::before {
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

/* Icône de chargement animée */
.loading-icon-container {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.loading-icon {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #2196F3, #1976D2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 24px;
  box-shadow: 
    0 8px 16px rgba(33, 150, 243, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  animation: loadingPulse 2s ease-in-out infinite;
}

.spinner {
  position: relative;
  width: 32px;
  height: 32px;
}

.spinner-ring {
  position: absolute;
  width: 100%;
  height: 100%;
  border: 3px solid transparent;
  border-top: 3px solid white;
  border-radius: 50%;
  animation: spin 1.2s linear infinite;
}

.spinner-ring:nth-child(2) {
  width: 80%;
  height: 80%;
  top: 10%;
  left: 10%;
  animation-delay: -0.4s;
  animation-duration: 1.6s;
}

.spinner-ring:nth-child(3) {
  width: 60%;
  height: 60%;
  top: 20%;
  left: 20%;
  animation-delay: -0.8s;
  animation-duration: 2s;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

@keyframes loadingPulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 
      0 8px 16px rgba(33, 150, 243, 0.3),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
  }
  50% {
    transform: scale(1.05);
    box-shadow: 
      0 12px 24px rgba(33, 150, 243, 0.4),
      inset 0 1px 0 rgba(255, 255, 255, 0.2);
  }
}

/* Contenu du chargement */
.loading-content {
  text-align: center;
  margin-bottom: 24px;
}

.loading-title {
  font-size: 24px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  margin: 0 0 12px 0;
  text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.loading-message {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.5;
  margin: 0 0 20px 0;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

/* Barre de progression */
.progress-container {
  margin-top: 20px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #2196F3, #1976D2);
  border-radius: 4px;
  transition: width 0.3s ease;
  position: relative;
}

.progress-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(90deg, 
    transparent 0%, 
    rgba(255, 255, 255, 0.3) 50%, 
    transparent 100%);
  animation: progressShine 2s ease-in-out infinite;
}

@keyframes progressShine {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(100%);
  }
}

.progress-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 600;
}

/* Indicateur d'étape */
.step-indicator {
  margin-top: 16px;
}

.step-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 500;
}

/* Actions */
.loading-actions {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.cancel-button {
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
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0.1));
  color: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.cancel-button::before {
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

.cancel-button:hover::before {
  opacity: 1;
}

.cancel-button:hover {
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

/* Animations d'entrée/sortie */
.loading-slide-enter-active,
.loading-slide-leave-active {
  transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.loading-slide-enter-from {
  opacity: 0;
  transform: scale(0.8) translateY(20px);
}

.loading-slide-leave-to {
  opacity: 0;
  transform: scale(0.9) translateY(-20px);
}

/* Responsive */
@media (max-width: 768px) {
  .loading-notification-container {
    margin: 20px;
    padding: 24px;
    max-width: none;
  }
  
  .loading-title {
    font-size: 20px;
  }
  
  .loading-message {
    font-size: 14px;
  }
  
  .cancel-button {
    width: 100%;
  }
}
</style> 