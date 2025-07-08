"""
MetroCity - Mastercamp 2025
Auteurs: Laura Donato, Alexandre Borny, Gabriel Langlois, Rémi Desjardins
Fichier: error_handler.py
Description: Gestionnaire d'erreurs centralisé pour l'API Flask avec logging structuré
"""

from flask import jsonify
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Classe de base pour les erreurs API"""
    def __init__(self, message: str, status_code: int = 500, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code

class ValidationError(APIError):
    """Erreur de validation des données"""
    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(message, 400, "VALIDATION_ERROR")
        self.field = field

class NotFoundError(APIError):
    """Erreur 404 - Ressource non trouvée"""
    def __init__(self, message: str = "Ressource non trouvée"):
        super().__init__(message, 404, "NOT_FOUND")

class ServiceUnavailableError(APIError):
    """Erreur 503 - Service indisponible"""
    def __init__(self, message: str = "Service temporairement indisponible"):
        super().__init__(message, 503, "SERVICE_UNAVAILABLE")

def create_error_response(error: APIError) -> tuple:
    """
    Crée une réponse d'erreur standardisée
    
    Args:
        error: Instance d'APIError
        
    Returns:
        Tuple (response, status_code)
    """
    response = {
        "error": {
            "message": error.message,
            "code": error.error_code,
            "status": error.status_code
        }
    }
    
    # Ajouter des informations supplémentaires si disponibles
    if hasattr(error, 'field'):
        response["error"]["field"] = error.field
    
    logger.error(f"API Error: {error.error_code} - {error.message}")
    
    return jsonify(response), error.status_code

def handle_validation_error(error: ValidationError) -> tuple:
    """Gestionnaire spécifique pour les erreurs de validation"""
    return create_error_response(error)

def handle_not_found_error(error: NotFoundError) -> tuple:
    """Gestionnaire spécifique pour les erreurs 404"""
    return create_error_response(error)

def handle_generic_error(error: Exception) -> tuple:
    """Gestionnaire pour les erreurs génériques"""
    logger.error(f"Unexpected error: {str(error)}", exc_info=True)
    
    response = {
        "error": {
            "message": "Erreur interne du serveur",
            "code": "INTERNAL_ERROR",
            "status": 500
        }
    }
    
    return jsonify(response), 500

def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
    """
    Valide la présence des champs requis
    
    Args:
        data: Données à valider
        required_fields: Liste des champs requis
        
    Raises:
        ValidationError: Si un champ requis est manquant
    """
    if not data:
        raise ValidationError("Données JSON requises")
    
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        raise ValidationError(
            f"Champs requis manquants: {', '.join(missing_fields)}",
            field="missing_fields"
        )

def validate_station_exists(station_id: str, stations: Dict[str, Any]) -> None:
    """
    Valide l'existence d'une station
    
    Args:
        station_id: ID de la station à valider
        stations: Dictionnaire des stations
        
    Raises:
        NotFoundError: Si la station n'existe pas
    """
    if station_id not in stations:
        raise NotFoundError(f"Station avec l'ID '{station_id}' non trouvée")

def format_success_response(data: Dict[str, Any], message: str = "Succès") -> Dict[str, Any]:
    """
    Formate une réponse de succès standardisée
    
    Args:
        data: Données de la réponse
        message: Message de succès
        
    Returns:
        Réponse formatée
    """
    return {
        "success": True,
        "message": message,
        "data": data
    } 