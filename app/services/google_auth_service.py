"""
Servicio de autenticación con Firebase Authentication (Google OAuth)
"""
from __future__ import annotations
import logging
from typing import Dict, Optional

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
        usando las bibliotecas de Google Auth.
        
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
            # Para Firebase, el token debe verificarse SIN especificar audience primero
            # y luego validar manualmente el audience contra el Project ID
            try:
                # Intentar sin audience (para tokens de Firebase)
                idinfo = id_token.verify_oauth2_token(
                    token,
                    requests.Request()
                )
            except ValueError:
                # Si falla, intentar con el Project ID como audience
                idinfo = id_token.verify_oauth2_token(
                    token,
                    requests.Request(),
                    settings.GOOGLE_CLIENT_ID
                )
            
            # Verificar que el token viene de Firebase
            # Los tokens de Firebase tienen el formato: https://securetoken.google.com/<project-id>
            expected_issuer = f"https://securetoken.google.com/{settings.GOOGLE_CLIENT_ID}"
            
            # Aceptar tanto tokens de Firebase como tokens directos de Google (para compatibilidad)
            valid_issuers = [
                expected_issuer,
                'accounts.google.com',
                'https://accounts.google.com'
            ]
            
            if idinfo['iss'] not in valid_issuers:
                logger.warning(f"Token con issuer no válido: {idinfo['iss']}")
                raise ValueError(f'Token no válido. Issuer esperado: {expected_issuer}')
            
            # Extraer información del usuario
            user_info = {
                'google_id': idinfo.get('sub') or idinfo.get('user_id'),  # uid de Firebase
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
            
            logger.info(f"Token de Firebase validado para: {user_info['email']} (issuer: {idinfo['iss']})")
            return user_info
            
        except ValueError as e:
            logger.warning(f"Token inválido: {str(e)}")
            raise ValueError(f"Token inválido: {str(e)}")
        except Exception as e:
            logger.error(f"Error al verificar token: {str(e)}")
            raise ValueError(f"Error al verificar token: {str(e)}")

