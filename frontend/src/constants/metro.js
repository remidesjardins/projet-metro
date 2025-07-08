/*
 * MetroCity - Mastercamp 2025
 * Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
 * Fichier: metro.js
 * Description: Constantes et utilitaires pour le réseau de métro parisien
 */

// Mapping des couleurs pour les lignes de métro
export const LINE_COLORS = {
  '1': '#FFCE00',  // Jaune - ligne 1
  '2': '#0064B0',  // Bleu foncé - ligne 2
  '3': '#9F9825',  // Marron - ligne 3
  '3bis': '#98D4E2',  // Bleu clair - ligne 3bis
  '3B': '#6EC4E8',    // Bleu - ligne 3B
  '4': '#C902A0',  // Rose foncé - ligne 4
  '5': '#F28E42',  // Orange - ligne 5
  '6': '#6EC68D',  // Vert - ligne 6
  '7': '#FA9EBA',  // Rose - ligne 7
  '7bis': '#84C0D4',  // Bleu ciel - ligne 7bis
  '7B': '#6ECA97',    // Vert d'eau - ligne 7B
  '8': '#C5A3CA',  // Violet clair - ligne 8
  '9': '#CEC92B',  // Vert olive - ligne 9
  '10': '#E4B327',  // Orange foncé - ligne 10
  '11': '#8D5E2A',  // Marron clair - ligne 11
  '12': '#007E52',  // Vert foncé - ligne 12
  '13': '#73C0E9',  // Bleu clair - ligne 13
  '14': '#662483',  // Violet - ligne 14
  'A': '#EB2132',  // Rouge - RER A
  'B': '#5091CB',  // Bleu - RER B
  'C': '#FFCC30',  // Jaune - RER C
  'D': '#008B5B',  // Vert - RER D
  'E': '#B94E9A'   // Violet - RER E
}

// Lignes avec climatisation complète
export const AIR_CONDITIONED_LINES = ["1", "2", "5", "9", "11", "14", "A"]

// Lignes avec climatisation partielle
export const PARTIAL_AIR_CONDITIONED_LINES = ["4", "B", "C", "D"]

// Fonction utilitaire pour déterminer le type de ligne
export function getLineType(line) {
  if (['A', 'B', 'C', 'D', 'E'].includes(line)) {
    return 'RER'
  }
  return 'Metro'
}

// Fonction utilitaire pour obtenir les lignes uniques d'un itinéraire
export function getUniqueLines(segments) {
  if (!segments || segments.length === 0) return []
  
  const lines = segments.map(segment => segment.line)
  return [...new Set(lines)]
} 