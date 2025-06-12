const API_URL = 'http://localhost:5050'

export const api = {
    async getStationsList() {
        const response = await fetch(`${API_URL}/stations`)
        if (!response.ok) {
            throw new Error('Erreur lors de la récupération des stations')
        }
        return response.json()
    },

    async calculateItinerary(start, end) {
        const response = await fetch(`${API_URL}/itineraire`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ start, end })
        })
        if (!response.ok) {
            const error = await response.json()
            throw new Error(error.error || 'Erreur lors du calcul de l\'itinéraire')
        }
        return response.json()
    }
}
