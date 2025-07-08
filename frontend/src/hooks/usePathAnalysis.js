/*
 * MetroCity - Mastercamp 2025
 * Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
 * Fichier: usePathAnalysis.js
 * Description: Hook Vue pour l'analyse des chemins (transferts, stations, statistiques)
 */

export function usePathAnalysis() {
  
  // Détecte si la station courante est une correspondance de changement de ligne
  function isInterchange(segmentIndex, stationIndex, pathDetails) {
    if (
      segmentIndex < pathDetails.length - 1 &&
      stationIndex === pathDetails[segmentIndex].stations.length - 1
    ) {
      // Vérifier si les lignes sont différentes
      const currentLine = pathDetails[segmentIndex].line;
      const nextLine = pathDetails[segmentIndex + 1].line;
      return currentLine !== nextLine;
    }
    return false;
  }

  // Calcule le nombre réel de correspondances (changements de ligne)
  function getTransferCount(pathDetails) {
    if (!pathDetails || pathDetails.length === 0) return 0;
    
    // Compter les segments qui ont des informations de transfert
    return pathDetails.filter(segment => segment.transferInfo).length;
  }

  // Calcule le nombre total de stations
  function getTotalStations(pathLength, pathDetails) {
    // Utiliser d'abord pathLength.stationsCount si disponible
    if (pathLength?.stationsCount) {
      return pathLength.stationsCount;
    }
    
    // Fallback sur l'ancien calcul si pathLength.stationsCount n'est pas disponible
    if (!pathDetails || pathDetails.length === 0) return 0;

    const allStations = pathDetails.flatMap(segment => segment.stations);
    const uniqueStations = [...new Set(allStations)];
    return uniqueStations.length;
  }

  // Obtient les stations pour une ligne donnée à partir d'un chemin structurel
  function getStationsForLine(structuralPath, line, fromStation, toStation) {
    if (!structuralPath || structuralPath.length === 0) {
      return [fromStation, toStation];
    }
    
    // Filtrer les segments de la ligne spécifiée
    const lineSegments = structuralPath.filter(segment => segment.line === line);
    
    if (lineSegments.length === 0) {
      return [fromStation, toStation];
    }
    
    // Extraire toutes les stations de cette ligne dans l'ordre
    const stations = [];
    const seenStations = new Set();
    
    for (const segment of lineSegments) {
      // Ajouter la station de départ si pas déjà vue
      if (!seenStations.has(segment.from_station)) {
        stations.push(segment.from_station);
        seenStations.add(segment.from_station);
      }
      
      // Ajouter la station d'arrivée si pas déjà vue
      if (!seenStations.has(segment.to_station)) {
        stations.push(segment.to_station);
        seenStations.add(segment.to_station);
      }
    }
    
    // Si les stations de départ et d'arrivée ne sont pas dans la liste,
    // les ajouter aux bonnes positions
    if (!stations.includes(fromStation)) {
      // Trouver la position appropriée pour fromStation
      const fromIndex = lineSegments.findIndex(seg => 
        seg.from_station === fromStation || seg.to_station === fromStation
      );
      if (fromIndex >= 0) {
        stations.splice(fromIndex, 0, fromStation);
      } else {
        stations.unshift(fromStation);
      }
    }
    
    if (!stations.includes(toStation)) {
      // Trouver la position appropriée pour toStation
      const toIndex = lineSegments.findIndex(seg => 
        seg.from_station === toStation || seg.to_station === toStation
      );
      if (toIndex >= 0) {
        stations.splice(toIndex + 1, 0, toStation);
      } else {
        stations.push(toStation);
      }
    }
    
    return stations;
  }

  // Calcule les temps de station pour un segment donné
  function calculateStationTimes(stations, segment) {
    if (!stations || stations.length === 0) {
      return [];
    }
    
    const stationTimes = [];
    const departureTime = new Date(`2000-01-01T${segment.departure_time}`);
    const arrivalTime = new Date(`2000-01-01T${segment.arrival_time}`);
    const totalTravelTime = (arrivalTime - departureTime) / 1000; // en secondes
    
    // Calculer le temps de trajet par station (approximation linéaire)
    const timePerStation = totalTravelTime / (stations.length - 1);
    
    for (let i = 0; i < stations.length; i++) {
      const station = stations[i];
      const stationTime = new Date(departureTime.getTime() + (i * timePerStation * 1000));
      
      stationTimes.push({
        station: station,
        departure_time: i === 0 ? segment.departure_time : null, // Seule la première station a un départ
        arrival_time: stationTime.toTimeString().slice(0, 8), // Format HH:MM:SS
        wait_time: i === 0 ? segment.wait_time : 0 // Seule la première station a un temps d'attente
      });
    }
    
    return stationTimes;
  }

  // Crée les temps de station pour un segment
  function createStationTimesForSegment(stations, segment) {
    if (!stations || stations.length === 0) {
      return {};
    }
    
    const stationTimes = {};
    
    for (let i = 0; i < stations.length; i++) {
      const station = stations[i];
      
      // Calculer les horaires basés sur les données GTFS du segment
      let departureTime = null;
      let arrivalTime = null;
      
      if (i === 0) {
        // Première station : heure de départ du segment
        departureTime = segment.departure_time;
      }
      
      if (i === stations.length - 1) {
        // Dernière station : heure d'arrivée du segment
        arrivalTime = segment.arrival_time;
      } else {
        // Stations intermédiaires : calculer l'heure d'arrivée approximative
        if (segment.departure_time && segment.arrival_time) {
          const departure = new Date(`2000-01-01T${segment.departure_time}`);
          const arrival = new Date(`2000-01-01T${segment.arrival_time}`);
          const totalTime = arrival - departure;
          const timePerStation = totalTime / (stations.length - 1);
          const stationArrival = new Date(departure.getTime() + (i * timePerStation));
          arrivalTime = stationArrival.toTimeString().slice(0, 8);
        }
      }
      
      stationTimes[station] = {
        departure: departureTime,
        arrival: arrivalTime
      };
    }
    
    return stationTimes;
  }

  // Met à jour les temps de station avec un nouveau segment
  function updateStationTimes(existingTimes, newSegment) {
    if (!existingTimes || Object.keys(existingTimes).length === 0) {
      return createStationTimesForSegment([newSegment.from_station, newSegment.to_station], newSegment);
    }
    
    // Mettre à jour l'heure d'arrivée de la station de correspondance
    if (existingTimes[newSegment.from_station]) {
      existingTimes[newSegment.from_station].arrival = newSegment.departure_time;
    }
    
    // Ajouter la nouvelle station d'arrivée
    existingTimes[newSegment.to_station] = {
      departure: null,
      arrival: newSegment.arrival_time
    };
    
    return existingTimes;
  }

  return {
    isInterchange,
    getTransferCount,
    getTotalStations,
    getStationsForLine,
    calculateStationTimes,
    createStationTimesForSegment,
    updateStationTimes
  }
} 