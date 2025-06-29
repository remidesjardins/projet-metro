// Configuration de l'API avec variables d'environnement
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5050'

export const api = {
    async getStationsList() {
        const response = await fetch(`${API_URL}/stations`)
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
    }
}
