"""
Servicio de autenticación con Firebase Authentication (Google OAuth)
"""
from __future__ import annotations
import logging
from typing import Dict

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials

from app.core.config import settings

logger = logging.getLogger(__name__)

# Inicializar Firebase Admin SDK (solo una vez)
try:
    firebase_admin.get_app()
except ValueError:
    # Si no existe una app, inicializar sin credenciales
    # (funciona para validar tokens sin necesidad de service account)
    cred = credentials.ApplicationDefault() if settings.GOOGLE_CLIENT_ID else None
    firebase_admin.initialize_app(cred)


class GoogleAuthService:
    """Servicio para validar tokens de Firebase y extraer información del usuario"""

    @staticmethod
    def verify_google_token(token: str) -> Dict[str, any]:
        """
        Valida un ID Token de Firebase y retorna la información del usuario.
        
        Firebase Authentication emite tokens JWT que pueden validarse
        usando Firebase Admin SDK.
        
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
            # Verificar el token usando Firebase Admin SDK
            decoded_token = firebase_auth.verify_id_token(token)
            
            # Extraer información del usuario
            user_info = {
                'google_id': decoded_token.get('uid') or decoded_token.get('sub'),
                'email': decoded_token.get('email'),
                'name': decoded_token.get('name', 'Usuario de Google'),
                'avatar': decoded_token.get('picture'),
                'email_verified': decoded_token.get('email_verified', False)
            }
            
            # Validar que al menos tengamos email y google_id
            if not user_info['email']:
                raise ValueError('Token no contiene email')
            if not user_info['google_id']:
                raise ValueError('Token no contiene identificador único')
            
            logger.info("Token de Firebase validado para: %s", user_info['email'])
            return user_info
            
        except firebase_auth.ExpiredIdTokenError as e:
            logger.warning("Token de Firebase expirado: %s", str(e))
            raise ValueError(f"Token expirado: {str(e)}") from e
        except firebase_auth.RevokedIdTokenError as e:
            logger.warning("Token de Firebase revocado: %s", str(e))
            raise ValueError(f"Token revocado: {str(e)}") from e
        except firebase_auth.CertificateFetchError as e:
            logger.error("Error al obtener certificados de Firebase: %s", str(e))
            raise ValueError(f"Error de certificados: {str(e)}") from e
        except firebase_auth.InvalidIdTokenError as e:
            logger.warning("Token de Firebase inválido: %s", str(e))
            raise ValueError(f"Token inválido: {str(e)}") from e
        except Exception as e:
            logger.error("Error al verificar token: %s", str(e))
            raise ValueError(f"Error al verificar token: {str(e)}") from e

