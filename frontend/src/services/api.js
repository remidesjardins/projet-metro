// Configuration de l'API avec variables d'environnement
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5050'

export const api = {
    async getStationsList(includeRER = true) {
        const url = new URL(`${API_URL}/stations`)
        url.searchParams.append('include_rer', includeRER.toString())
        const response = await fetch(url)
        if (!response.ok) {
            throw new Error('Erreur lors de la récupération des stations')
        }
        return response.json()
    },

    async calculateItinerary(start, end) {
        const response = await fetch(`${API_URL}/shortest-path`, {
            method: 'POST',
            headers: {
            'Content-Type': 'application/json'
            },
            body: JSON.stringify({ start: start.toString(), end: end.toString() })
        })
        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.error || 'Erreur lors du calcul de l\'itinéraire')
        }
        return response.json()
    },

    async testConnexity() {
        const response = await fetch(`${API_URL}/connexity`)
        if (!response.ok) {
            throw new Error('Erreur lors du test de connexité')
        }
        return response.json()
    },

    async get(endpoint) {
        const response = await fetch(`${API_URL}${endpoint}`)
        if (!response.ok) {
            throw new Error(`Erreur lors du GET ${endpoint}`)
        }
        return response.json()
    },

    async post(endpoint, data) {
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        })
        if (!response.ok) {
            let errorData = null
            try {
                errorData = await response.json()
            } catch {}
            
            // Créer une erreur avec les données détaillées
            const error = new Error(errorData?.error || 'Erreur lors du POST ' + endpoint)
            error.responseData = errorData // Conserver toutes les données de la réponse
            throw error
        }
        return response.json()
    },

    async getTemporalAlternatives({ start_station, end_station, departure_time, arrival_time, date, max_paths = 4, max_wait_time = 1800, include_rer = true, sort_by = 'duration' }) {
        // N'inclure que le champ d'heure fourni
        const data = {
            start_station,
            end_station,
            date,
            max_paths,
            max_wait_time,
            include_rer,
            sort_by
        };
        if (departure_time) data.departure_time = departure_time;
        if (arrival_time) data.arrival_time = arrival_time;
        const response = await this.post('/temporal/alternatives', data);
        return response;
    },

    async getTemporalAlternativesArrival({ start_station, end_station, arrival_time, date, max_paths = 4, max_wait_time = 1800, include_rer = true, sort_by = 'duration' }) {
        const response = await this.post('/temporal/alternatives-arrival', {
            start_station,
            end_station,
            arrival_time,
            date,
            max_paths,
            max_wait_time,
            include_rer,
            sort_by
        });
        return response;
    }
}
