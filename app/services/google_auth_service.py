"""
Servicio de autenticación con Firebase Authentication (Google OAuth)
"""
from __future__ import annotations
import logging
from typing import Dict

from google.oauth2 import id_token
from google.auth.transport import requests

from app.core.config import settings

logger = logging.getLogger(__name__)


class GoogleAuthService:
    """Servicio para validar tokens de Firebase y extraer información del usuario"""

    @staticmethod
    def verify_google_token(token: str) -> Dict[str, any]:
        """
        Valida un ID Token de Firebase y retorna la información del usuario.
        
        Firebase Authentication emite tokens JWT que pueden validarse
        usando las claves públicas de Google sin necesidad de credenciales de servidor.
        
        Args:
            token: ID Token JWT recibido desde el frontend (Firebase)
            
        Returns:
            Dict con información del usuario:
            - google_id: Identificador único del usuario (uid de Firebase)
            - email: Correo electrónico del usuario
            - name: Nombre completo del usuario
            - avatar: URL de la foto de perfil
            - email_verified: Si el email está verificado
            
        Raises:
            ValueError: Si el token es inválido, expirado o no verificable
        """
        if not settings.GOOGLE_CLIENT_ID:
            raise ValueError("GOOGLE_CLIENT_ID (Firebase Project ID) no configurado en el servidor")
        
        try:
            # Verificar el token de Firebase usando google.oauth2.id_token
            # Firebase tokens tienen el project ID como audience
            idinfo = id_token.verify_firebase_token(
                token,
                requests.Request(),
                audience=settings.GOOGLE_CLIENT_ID
            )
            
            # Extraer información del usuario
            user_info = {
                'google_id': idinfo.get('uid') or idinfo.get('sub') or idinfo.get('user_id'),
                'email': idinfo.get('email'),
                'name': idinfo.get('name', 'Usuario de Google'),
                'avatar': idinfo.get('picture'),
                'email_verified': idinfo.get('email_verified', False)
            }
            
            # Validar que al menos tengamos email y google_id
            if not user_info['email']:
                raise ValueError('Token no contiene email')
            if not user_info['google_id']:
                raise ValueError('Token no contiene identificador único')
            
            logger.info("Token de Firebase validado para: %s", user_info['email'])
            return user_info
            
        except ValueError as e:
            logger.warning("Token de Firebase inválido: %s", str(e))
            raise ValueError(f"Token inválido: {str(e)}") from e
        except Exception as e:
            logger.error("Error al verificar token: %s", str(e))
            raise ValueError(f"Error al verificar token: {str(e)}") from e

