/*
 * MetroCity - Mastercamp 2025
 * Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
 * Fichier: index.js
 * Description: Configuration du routeur Vue Router pour l'application
 */

import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import MapDebug from '../components/MapDebug.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/debug',
      name: 'debug',
      component: MapDebug,
    },
  ],
})

export default router
