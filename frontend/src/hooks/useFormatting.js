/*
 * MetroCity - Mastercamp 2025
 * Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
 * Fichier: useFormatting.js
 * Description: Hook Vue pour les utilitaires de formatage (temps, couleurs)
 */

export function useFormatting() {
  
  // Formate le temps en minutes et secondes
  function formatTime(pathLengthObj) {
    const seconds = pathLengthObj?.duration || pathLengthObj || 0;
    
    if (!seconds || isNaN(seconds)) {
      return '0 min';
    }

    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.round(seconds % 60);
    
    if (minutes === 0) {
      return `${remainingSeconds}s`;
    } else if (remainingSeconds === 0) {
      return `${minutes}min`;
    } else {
      return `${minutes}min ${remainingSeconds}s`;
    }
  }

  // Formate l'affichage du temps (supprime les secondes si 00)
  function formatTimeDisplay(timeStr) {
    if (!timeStr) return '';
    // Supprimer les secondes si elles sont à 00
    return timeStr.replace(':00', '');
  }

  // Formate le temps ACPM en heures et minutes
  function formatACPMTime(totalWeight) {
    if (!totalWeight || isNaN(totalWeight)) {
      return '00:00';
    }
    
    // Convertir le poids total en temps (supposant que le poids représente des secondes)
    const totalMinutes = Math.floor(totalWeight / 60);
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;
    
    // Formater au format hh:mm
    const formattedHours = hours.toString().padStart(2, '0');
    const formattedMinutes = minutes.toString().padStart(2, '0');
    
    return `${formattedHours}:${formattedMinutes}`;
  }

  // Assombrit une couleur hexadécimale d'un facteur donné
  function darkenColor(hex, factor = 0.7) {
    // hex: #RRGGBB, factor < 1 pour foncer
    if (!hex || typeof hex !== 'string' || !hex.startsWith('#')) return hex;
    let r = parseInt(hex.slice(1, 3), 16);
    let g = parseInt(hex.slice(3, 5), 16);
    let b = parseInt(hex.slice(5, 7), 16);
    r = Math.floor(r * factor);
    g = Math.floor(g * factor);
    b = Math.floor(b * factor);
    return `#${r.toString(16).padStart(2, '0')}${g.toString(16).padStart(2, '0')}${b.toString(16).padStart(2, '0')}`;
  }

  return {
    formatTime,
    formatTimeDisplay,
    formatACPMTime,
    darkenColor
  }
} 