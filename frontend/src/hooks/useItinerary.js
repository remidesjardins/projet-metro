/*
 * MetroCity - Mastercamp 2025
 * Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
 * Fichier: useItinerary.js
 * Description: Hook Vue principal pour la recherche d'itinéraires et la gestion des chemins
 */

import { ref, computed, watch } from 'vue';
import { api } from '../services/api';
import { notificationService } from '../services/notificationService';

export function useItinerary({
  startStation,
  endStation,
  startStationId,
  endStationId
}) {
  // États principaux
  const pathDetails = ref([]);
  const pathLength = ref({ duration: null, emissions: null, stationsCount: null });
  const temporalData = ref(null);
  const alternativePaths = ref([]);
  const selectedAlternativeIndex = ref(null);
  const isLoading = ref(false);

  // Critères de recherche
  const searchMode = ref('classic'); // 'classic' ou 'temporal'
  const sortCriterion = ref('duration'); // 'duration' ou 'emissions'
  const departureTime = ref('08:30');
  const departureDate = ref('2024-03-15');
  const timeType = ref('departure'); // 'departure' ou 'arrival'

  function clearResults() {
    pathDetails.value = [];
    pathLength.value = { duration: null, emissions: null, stationsCount: null };
    temporalData.value = null;
    alternativePaths.value = [];
    selectedAlternativeIndex.value = null;
  }

  function validateTimeInput() {
    const timePattern = /^([0-2]?[0-9]|3[0-1]):([0-5][0-9])$/;
    if (!timePattern.test(departureTime.value)) {
      notificationService.showValidationError('Format d\'heure invalide. Utilisez HH:MM (ex: 08:30, 24:30 pour 00:30 du lendemain)');
      return false;
    }
    const [hours, minutes] = departureTime.value.split(':').map(Number);
    if (hours < 0 || hours > 31) {
      notificationService.showValidationError('Heures invalides. Utilisez 0-23 pour le jour même, 24-31 pour le lendemain');
      return false;
    }
    if (minutes < 0 || minutes > 59) {
      notificationService.showValidationError('Minutes invalides. Utilisez 0-59');
      return false;
    }
    return true;
  }

  async function findPath() {
    if (!startStation.value || !endStation.value) {
      notificationService.showValidationError('Veuillez sélectionner une station de départ et d\'arrivée');
      return;
    }
    isLoading.value = true;
    clearResults();
    const t0 = performance.now();
    try {
      if (searchMode.value === 'temporal') {
        let response;
        if (timeType.value === 'arrival') {
          response = await api.getTemporalAlternativesArrival({
            start_station: startStation.value,
            end_station: endStation.value,
            arrival_time: departureTime.value,
            date: departureDate.value,
            max_paths: 4,
            max_wait_time: 1800,
            sort_by: sortCriterion.value,
          });
        } else {
          response = await api.getTemporalAlternatives({
            start_station: startStation.value,
            end_station: endStation.value,
            departure_time: departureTime.value,
            date: departureDate.value,
            max_paths: 4,
            max_wait_time: 1800,
            sort_by: sortCriterion.value,
          });
        }
        if (response.paths && response.paths.length > 0) {
          alternativePaths.value = response.paths;
          selectedAlternativeIndex.value = null;
          temporalData.value = null;
          pathDetails.value = [];
          pathLength.value = { duration: null, emissions: null, stationsCount: null };
          const t1 = performance.now();
          notificationService.showPathFoundSuccess(
            response.paths[0]?.total_duration || 'N/A',
            response.paths[0]?.stations_count || response.paths[0]?.segments?.reduce((total, seg) => total + (seg.stations?.length || 0), 0),
            Math.round(t1 - t0)
          );
        } else {
          notificationService.showValidationError('Aucun itinéraire trouvé.');
        }
      } else {
        if (!startStationId.value || !endStationId.value) {
          throw new Error('IDs de stations manquants. Veuillez sélectionner les stations depuis les suggestions.');
        }
        const response = await api.post('/shortest-path', {
          start: startStationId.value,
          end: endStationId.value,
        });
        const transformedSegments = response.chemin.map(segment => ({
          line: segment.Ligne,
          stations: segment.Stations.map(station => station["Nom Station"]),
          duration: segment.Duration || 0,
          stationsCount: segment.Stations.length,
          stationTimes: null,
          transferInfo: null,
          originalStations: segment.Stations
        }));
        pathDetails.value = transformedSegments;
        pathLength.value = {
          duration: response.duration,
          emissions: response.emissions,
          stationsCount: response.stations_count
        };
        const t1 = performance.now();
        notificationService.showPathFoundSuccess(
          response.duration || 'N/A',
          response.stations_count || transformedSegments.reduce((total, seg) => total + seg.stations.length, 0),
          Math.round(t1 - t0)
        );
      }
    } catch (error) {
      notificationService.handleApiError(error, 'findPath');
      if (error.responseData && error.responseData.service_info) {
        const serviceInfo = error.responseData.service_info;
        if (serviceInfo.suggested_departure) {
          notificationService.showErrorWithRetry(
            serviceInfo.message,
            () => {
              departureTime.value = serviceInfo.suggested_departure;
              findPath();
            },
            'Service indisponible'
          );
        }
      }
    } finally {
      isLoading.value = false;
    }
  }

  function selectAlternativePath(index) {
    selectedAlternativeIndex.value = index;
    const path = alternativePaths.value[index];
    if (!path) return;
    
    // Mettre à jour les données temporelles
    temporalData.value = path;
    
    // Transformer les segments temporels en pathDetails pour l'affichage
    // Le structural_path contient tous les segments structurels
    const transformedSegments = reconstructSegmentsFromTemporal(path.segments, path.structural_path);
    
    // Mettre à jour pathDetails et pathLength
    pathDetails.value = transformedSegments;
    pathLength.value = {
      duration: path.total_duration,
      emissions: path.emissions || 0,
      stationsCount: calculateTotalStations(transformedSegments)
    };
    
    // Alternative sélectionnée avec succès
  }
  
  // Fonction pour reconstituer les segments avec toutes les stations
  function reconstructSegmentsFromTemporal(temporalSegments, structuralPath) {
    if (!temporalSegments || !structuralPath) {
      // Fallback: utiliser les données temporelles telles quelles
      return temporalSegments.map(segment => ({
        line: segment.line,
        stations: [segment.from_station, segment.to_station],
        duration: segment.travel_time || 0,
        stationsCount: 2,
        // Préserver les données temporelles dans le fallback
        departure_time: segment.departure_time,
        arrival_time: segment.arrival_time,
        stationTimes: createStationTimesForSegment(segment),
        transferInfo: segment.transfer_time > 0 ? {
          transfer_time: segment.transfer_time,
          wait_time: segment.wait_time
        } : null,
        originalStations: [
          { "Nom Station": segment.from_station },
          { "Nom Station": segment.to_station }
        ]
      }));
    }

    const result = [];
    let structuralIndex = 0;
    
    for (const temporalSeg of temporalSegments) {
      const stations = [];
      const originalStations = [];
      
      // Commencer par la station de départ
      stations.push(temporalSeg.from_station);
      originalStations.push({ "Nom Station": temporalSeg.from_station });
      
      // Parcourir les segments structurels correspondants
      while (structuralIndex < structuralPath.length) {
        const structuralSeg = structuralPath[structuralIndex];
        
        // Vérifier si ce segment structurel appartient au segment temporel courant
        if (structuralSeg.line === temporalSeg.line) {
          // Ajouter la station d'arrivée du segment structurel
          if (!stations.includes(structuralSeg.to_station)) {
            stations.push(structuralSeg.to_station);
            originalStations.push({ "Nom Station": structuralSeg.to_station });
          }
          
          structuralIndex++;
          
          // Si on a atteint la station de destination du segment temporel, arrêter
          if (structuralSeg.to_station === temporalSeg.to_station) {
            break;
          }
        } else {
          // Changement de ligne, on s'arrête ici
          break;
        }
      }
      
      // S'assurer qu'on a la station de destination
      if (!stations.includes(temporalSeg.to_station)) {
        stations.push(temporalSeg.to_station);
        originalStations.push({ "Nom Station": temporalSeg.to_station });
      }
      
      // Créer l'objet segment
      const segment = {
        line: temporalSeg.line,
        stations: stations,
        duration: temporalSeg.travel_time || 0,
        stationsCount: stations.length,
        // Préserver les données temporelles importantes pour l'affichage
        departure_time: temporalSeg.departure_time,
        arrival_time: temporalSeg.arrival_time,
        stationTimes: createStationTimesForSegment(temporalSeg, stations),
        transferInfo: null, // Sera ajouté après si nécessaire
        originalStations: originalStations
      };
      
      result.push(segment);
    }
    
    // Ajouter les informations de transfert pour chaque segment qui a un transfer_time > 0
    for (let i = 0; i < result.length; i++) {
      const segment = result[i];
      const temporalSeg = temporalSegments[i];
      
      // Si ce segment a un transfer_time > 0, c'est qu'il y a eu un changement de ligne
      if (temporalSeg.transfer_time > 0 && i > 0) {
        const previousSegment = result[i - 1];
        
        // La station de correspondance est la station commune entre les deux segments
        // Elle devrait être la dernière station du segment précédent ET la première du segment actuel
        const transferStation = previousSegment.stations[previousSegment.stations.length - 1];
        
        // Vérification de cohérence
        if (transferStation !== segment.stations[0]) {
          // Incohérence de station de transfert détectée
        }
        
        segment.transferInfo = {
          transfer_time: temporalSeg.transfer_time,
          wait_time: temporalSeg.wait_time || 0,
          transferStation: transferStation, // Station commune entre les deux segments
          fromLine: previousSegment.line,
          toLine: segment.line
        };
      }
    }
    
    return result;
  }
  
  // Fonction utilitaire pour créer les horaires de station
  function createStationTimesForSegment(temporalSegment, stations = null) {
    if (!temporalSegment) return null;
    
    const stationList = stations || [temporalSegment.from_station, temporalSegment.to_station];
    const stationTimes = {};
    
    // Si on n'a qu'une ou deux stations, attribution simple
    if (stationList.length <= 2) {
      // Station de départ
      if (stationList[0]) {
        stationTimes[stationList[0]] = {
          departure: temporalSegment.departure_time,
          arrival: null
        };
      }
      
      // Station d'arrivée  
      if (stationList[stationList.length - 1] && stationList.length > 1) {
        stationTimes[stationList[stationList.length - 1]] = {
          departure: null,
          arrival: temporalSegment.arrival_time
        };
      }
    } else {
      // Pour plus de stations, interpoler les horaires
      const departureTime = temporalSegment.departure_time;
      const arrivalTime = temporalSegment.arrival_time;
      
      if (departureTime && arrivalTime) {
        try {
          const departure = new Date(`2000-01-01T${departureTime}`);
          const arrival = new Date(`2000-01-01T${arrivalTime}`);
          const totalTime = arrival - departure;
          const timePerStation = totalTime / (stationList.length - 1);
          
          for (let i = 0; i < stationList.length; i++) {
            const station = stationList[i];
            
            if (i === 0) {
              // Première station : heure de départ
              stationTimes[station] = {
                departure: departureTime,
                arrival: null
              };
            } else if (i === stationList.length - 1) {
              // Dernière station : heure d'arrivée
              stationTimes[station] = {
                departure: null,
                arrival: arrivalTime
              };
            } else {
              // Stations intermédiaires : interpoler
              const stationTime = new Date(departure.getTime() + (i * timePerStation));
              const timeStr = stationTime.toTimeString().slice(0, 8);
              stationTimes[station] = {
                departure: null,
                arrival: timeStr
              };
            }
          }
        } catch (error) {
          // Erreur lors de l'interpolation des horaires
          // Fallback vers l'attribution simple
          stationTimes[stationList[0]] = {
            departure: departureTime,
            arrival: null
          };
          if (stationList.length > 1) {
            stationTimes[stationList[stationList.length - 1]] = {
              departure: null,
              arrival: arrivalTime
            };
          }
        }
      }
    }
    
    return stationTimes;
  }
  
  // Fonction utilitaire pour obtenir la ligne précédente
  function getPreviousLine(segments) {
    if (segments.length === 0) return null;
    return segments[segments.length - 1].line;
  }
  
  // Fonction utilitaire pour calculer le nombre total de stations
  function calculateTotalStations(segments) {
    if (!segments || segments.length === 0) return 0;
    
    // Collecter toutes les stations uniques
    const allStations = new Set();
    segments.forEach(segment => {
      segment.stations.forEach(station => allStations.add(station));
    });
    
    return allStations.size;
  }

  return {
    findPath,
    alternativePaths,
    selectedAlternativeIndex,
    selectAlternativePath,
    pathDetails,
    pathLength,
    temporalData,
    sortCriterion,
    timeType,
    departureTime,
    departureDate,
    isLoading,
    validateTimeInput,
    clearResults,
    searchMode,
    notificationService
  };
} 