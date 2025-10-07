"""
Servicio de auditoría para tracking y notificaciones de eventos de seguridad
"""
from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Any
import httpx
import logging
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import models

logger = logging.getLogger(__name__)


class AuditEventType:
    """Tipos de eventos de auditoría"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    REGISTER = "register"
    OTP_REQUEST = "otp_request"
    OTP_CONFIRM_SUCCESS = "otp_confirm_success"
    OTP_CONFIRM_FAILED = "otp_confirm_failed"
    LOGOUT = "logout"
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    FILE_VIEW = "file_view"
    FILE_DELETE = "file_delete"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"


class AuditService:
    """Servicio para auditoría y notificaciones de seguridad en tiempo real"""

    def __init__(self, db: Session):
        self.db = db

    async def log_and_notify(
        self,
        event_type: str,
        user_email: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "info",
        ip_address: Optional[str] = None
    ) -> None:
        """
        Registra un evento de auditoría y envía notificación a Telegram.
        
        Args:
            event_type: Tipo de evento (usar AuditEventType)
            user_email: Email del usuario que realizó la acción
            details: Detalles adicionales del evento (archivo, ubicación, etc)
            severity: Severidad del evento (info, warning, critical)
            ip_address: Dirección IP del cliente
        """
        try:
            # 1. Registrar en base de datos
            audit_log = models.AuditLog(
                event_type=event_type,
                user_email=user_email,
                details=str(details) if details else None,
                severity=severity,
                ip_address=ip_address,
                timestamp=datetime.utcnow()
            )
            self.db.add(audit_log)
            self.db.commit()
            
            # 2. Enviar notificación a Telegram
            await self._send_telegram_alert(
                event_type=event_type,
                user_email=user_email,
                details=details,
                severity=severity,
                timestamp=audit_log.timestamp
            )
            
            logger.info(f"Audit event logged: {event_type} by {user_email}")
            
        except Exception as e:
            logger.error(f"Error logging audit event: {e}")
            self.db.rollback()

    async def _send_telegram_alert(
        self,
        event_type: str,
        user_email: Optional[str],
        details: Optional[Dict[str, Any]],
        severity: str,
        timestamp: datetime
    ) -> None:
        """Envía alerta formateada a Telegram"""
        if not settings.TELEGRAM_BOT_TOKEN or not settings.TELEGRAM_CHAT_ID:
            logger.warning("Telegram not configured, skipping notification")
            return

        try:
            message = self._format_telegram_message(
                event_type=event_type,
                user_email=user_email,
                details=details,
                severity=severity,
                timestamp=timestamp
            )

            url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10.0)
                response.raise_for_status()
                logger.info(f"Telegram alert sent for {event_type}")

        except Exception as e:
            logger.error(f"Failed to send Telegram alert: {e}")

    def _format_telegram_message(
        self,
        event_type: str,
        user_email: Optional[str],
        details: Optional[Dict[str, Any]],
        severity: str,
        timestamp: datetime
    ) -> str:
        """Formatea el mensaje de Telegram según el tipo de evento"""
        
        # Emojis según severidad
        severity_emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "critical": "🚨"
        }
        emoji = severity_emoji.get(severity, "📋")
        
        # Timestamp formateado
        ts = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # Usuario
        user_info = f"👤 <b>Usuario:</b> {user_email}" if user_email else "👤 <b>Usuario:</b> Anónimo"
        
        # Mensajes específicos por tipo de evento
        if event_type == AuditEventType.LOGIN_SUCCESS:
            return f"""{emoji} <b>Alerta LoRaGuard - Inicio de Sesión</b>
✅ <b>Sesión iniciada exitosamente</b>
{user_info}
📍 <b>Ubicación:</b> Dashboard de Archivos Cifrados
⏰ <b>Timestamp:</b> {ts}
🔧 <b>Acción:</b> Sesión activa - Monitoreo en curso"""

        elif event_type == AuditEventType.LOGIN_FAILED:
            return f"""🚨 <b>¡ALERTA CRÍTICA! - Intento de Inicio Fallido</b>
❌ <b>Intento de login fallido</b>
{user_info}
📍 <b>Ubicación:</b> Dashboard de Archivos Cifrados
⏰ <b>Timestamp:</b> {ts}
🔧 <b>Acción recomendada:</b> Revisar intentos de acceso no autorizado"""

        elif event_type == AuditEventType.REGISTER:
            return f"""{emoji} <b>Alerta LoRaGuard - Nuevo Registro</b>
📝 <b>Nueva cuenta registrada</b>
{user_info}
📍 <b>Ubicación:</b> Sistema de Registro
⏰ <b>Timestamp:</b> {ts}
🔧 <b>Acción:</b> Usuario agregado al sistema"""

        elif event_type == AuditEventType.OTP_REQUEST:
            return f"""{emoji} <b>Alerta LoRaGuard - Solicitud OTP</b>
🔐 <b>Código OTP solicitado</b>
{user_info}
📍 <b>Ubicación:</b> Verificación de 2FA
⏰ <b>Timestamp:</b> {ts}
🔧 <b>Acción:</b> Código enviado - Esperando confirmación"""

        elif event_type == AuditEventType.OTP_CONFIRM_SUCCESS:
            return f"""{emoji} <b>Alerta LoRaGuard - OTP Confirmado</b>
✅ <b>Autenticación 2FA completada</b>
{user_info}
📍 <b>Ubicación:</b> Dashboard de Archivos Cifrados
⏰ <b>Timestamp:</b> {ts}
🔧 <b>Acción:</b> Acceso completo otorgado"""

        elif event_type == AuditEventType.OTP_CONFIRM_FAILED:
            return f"""🚨 <b>¡ALERTA! - OTP Inválido</b>
❌ <b>Intento de OTP fallido</b>
{user_info}
📍 <b>Ubicación:</b> Verificación 2FA
⏰ <b>Timestamp:</b> {ts}
🔧 <b>Acción recomendada:</b> Verificar intentos de acceso sospechosos"""

        elif event_type == AuditEventType.LOGOUT:
            return f"""{emoji} <b>Alerta LoRaGuard - Cierre de Sesión</b>
🚪 <b>Sesión cerrada</b>
{user_info}
📍 <b>Ubicación:</b> Dashboard de Archivos Cifrados
⏰ <b>Timestamp:</b> {ts}
🔧 <b>Acción:</b> Sesión terminada correctamente"""

        elif event_type == AuditEventType.FILE_UPLOAD:
            file_name = details.get("file_name", "archivo") if details else "archivo"
            file_size = details.get("file_size", 0) if details else 0
            size_kb = file_size / 1024
            return f"""{emoji} <b>Alerta LoRaGuard - Archivo Subido</b>
📤 <b>Nuevo archivo cifrado agregado</b>
{user_info}
📄 <b>Archivo:</b> {file_name}
💾 <b>Tamaño:</b> {size_kb:.2f} KB
📍 <b>Ubicación:</b> Carpeta Cifrada (/Desktop/encrypt)
🔐 <b>Algoritmo:</b> AES-256-GCM
⏰ <b>Timestamp:</b> {ts}
🔧 <b>Acción:</b> Archivo almacenado de forma segura"""

        elif event_type == AuditEventType.FILE_DOWNLOAD:
            file_name = details.get("file_name", "archivo") if details else "archivo"
            return f"""⚠️ <b>Alerta LoRaGuard - Archivo Descargado</b>
📥 <b>Archivo descifrado y descargado</b>
{user_info}
📄 <b>Archivo:</b> {file_name}
📍 <b>Ubicación:</b> Carpeta Cifrada → Dispositivo local
🔓 <b>Estado:</b> Descifrado exitosamente
⏰ <b>Timestamp:</b> {ts}
🔧 <b>Acción recomendada:</b> Monitorear uso del archivo descargado"""

        elif event_type == AuditEventType.FILE_VIEW:
            file_name = details.get("file_name", "archivo") if details else "archivo"
            return f"""{emoji} <b>Alerta LoRaGuard - Archivo Visualizado</b>
👁️ <b>Archivo descifrado para vista previa</b>
{user_info}
📄 <b>Archivo:</b> {file_name}
📍 <b>Ubicación:</b> Vista previa en Dashboard
🔓 <b>Estado:</b> Descifrado temporalmente
⏰ <b>Timestamp:</b> {ts}
🔧 <b>Acción:</b> Contenido visible en memoria (no descargado)"""

        elif event_type == AuditEventType.FILE_DELETE:
            file_name = details.get("file_name", "archivo") if details else "archivo"
            return f"""🚨 <b>Alerta LoRaGuard - Archivo Eliminado</b>
🗑️ <b>Archivo borrado permanentemente</b>
{user_info}
📄 <b>Archivo:</b> {file_name}
📍 <b>Ubicación:</b> Carpeta Cifrada
⏰ <b>Timestamp:</b> {ts}
🔧 <b>Acción recomendada:</b> Archivo eliminado - No recuperable"""

        elif event_type == AuditEventType.SUSPICIOUS_ACTIVITY:
            activity = details.get("activity", "desconocida") if details else "desconocida"
            return f"""🚨 <b>¡ALERTA CRÍTICA! - Actividad Sospechosa</b>
⚠️ <b>Actividad anómala detectada</b>
{user_info}
📋 <b>Detalle:</b> {activity}
📍 <b>Ubicación:</b> Sistema de Archivos Cifrados
⏰ <b>Timestamp:</b> {ts}
🔧 <b>Acción recomendada:</b> REVISAR INMEDIATAMENTE - Posible intrusión"""

        else:
            return f"""{emoji} <b>Alerta LoRaGuard - Evento del Sistema</b>
📋 <b>Evento:</b> {event_type}
{user_info}
⏰ <b>Timestamp:</b> {ts}"""

