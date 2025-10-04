"""
Notification service for sending alerts via multiple channels
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import httpx
import json

from app.models import models, schemas
from app.core.config import settings

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for sending notifications via multiple channels"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def send_alert_notifications(self, alert: models.Alert) -> List[models.Notification]:
        """Send notifications for an alert via all configured channels"""
        notifications = []
        
        # Send Telegram notification
        if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID:
            telegram_notification = await self._send_telegram_notification(alert)
            if telegram_notification:
                notifications.append(telegram_notification)
        
        # Send WhatsApp notification
        if settings.WHATSAPP_ACCESS_TOKEN and settings.WHATSAPP_PHONE_NUMBER_ID:
            whatsapp_notification = await self._send_whatsapp_notification(alert)
            if whatsapp_notification:
                notifications.append(whatsapp_notification)
        
        # Send FCM notification
        if settings.FCM_SERVER_KEY:
            fcm_notification = await self._send_fcm_notification(alert)
            if fcm_notification:
                notifications.append(fcm_notification)
        
        return notifications
    
    async def _send_telegram_notification(self, alert: models.Alert) -> Optional[models.Notification]:
        """Send notification via Telegram"""
        try:
            url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            
            payload = {
                "chat_id": settings.TELEGRAM_CHAT_ID,
                "text": alert.message,
                "parse_mode": "HTML"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
            
            # Create notification record
            notification = models.Notification(
                alert_id=alert.id,
                channel="telegram",
                recipient=settings.TELEGRAM_CHAT_ID,
                message=alert.message,
                status=models.NotificationStatus.SENT,
                sent_at=datetime.utcnow()
            )
            
            self.db.add(notification)
            self.db.commit()
            
            logger.info(f"Telegram notification sent for alert {alert.id}")
            return notification
            
        except Exception as e:
            logger.error(f"Failed to send Telegram notification for alert {alert.id}: {e}")
            
            # Create failed notification record
            notification = models.Notification(
                alert_id=alert.id,
                channel="telegram",
                recipient=settings.TELEGRAM_CHAT_ID,
                message=alert.message,
                status=models.NotificationStatus.FAILED,
                error_message=str(e)
            )
            
            self.db.add(notification)
            self.db.commit()
            
            return notification
    
    async def _send_whatsapp_notification(self, alert: models.Alert) -> Optional[models.Notification]:
        """Send notification via WhatsApp Cloud API"""
        try:
            url = f"https://graph.facebook.com/v17.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
            
            headers = {
                "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": settings.TELEGRAM_CHAT_ID,  # Using Telegram chat ID as placeholder
                "type": "text",
                "text": {
                    "body": alert.message
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
            
            # Create notification record
            notification = models.Notification(
                alert_id=alert.id,
                channel="whatsapp",
                recipient=settings.TELEGRAM_CHAT_ID,  # Placeholder
                message=alert.message,
                status=models.NotificationStatus.SENT,
                sent_at=datetime.utcnow()
            )
            
            self.db.add(notification)
            self.db.commit()
            
            logger.info(f"WhatsApp notification sent for alert {alert.id}")
            return notification
            
        except Exception as e:
            logger.error(f"Failed to send WhatsApp notification for alert {alert.id}: {e}")
            
            # Create failed notification record
            notification = models.Notification(
                alert_id=alert.id,
                channel="whatsapp",
                recipient=settings.TELEGRAM_CHAT_ID,  # Placeholder
                message=alert.message,
                status=models.NotificationStatus.FAILED,
                error_message=str(e)
            )
            
            self.db.add(notification)
            self.db.commit()
            
            return notification
    
    async def _send_fcm_notification(self, alert: models.Alert) -> Optional[models.Notification]:
        """Send notification via Firebase Cloud Messaging"""
        try:
            url = "https://fcm.googleapis.com/fcm/send"
            
            headers = {
                "Authorization": f"key={settings.FCM_SERVER_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "to": "/topics/loraguard_alerts",  # Topic for all devices
                "notification": {
                    "title": "LoRaGuard Alert",
                    "body": alert.message,
                    "sound": "default"
                },
                "data": {
                    "alert_id": str(alert.id),
                    "device_id": alert.device_id,
                    "severity": alert.severity.value,
                    "alert_type": alert.alert_type
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
            
            # Create notification record
            notification = models.Notification(
                alert_id=alert.id,
                channel="fcm",
                recipient="/topics/loraguard_alerts",
                message=alert.message,
                status=models.NotificationStatus.SENT,
                sent_at=datetime.utcnow()
            )
            
            self.db.add(notification)
            self.db.commit()
            
            logger.info(f"FCM notification sent for alert {alert.id}")
            return notification
            
        except Exception as e:
            logger.error(f"Failed to send FCM notification for alert {alert.id}: {e}")
            
            # Create failed notification record
            notification = models.Notification(
                alert_id=alert.id,
                channel="fcm",
                recipient="/topics/loraguard_alerts",
                message=alert.message,
                status=models.NotificationStatus.FAILED,
                error_message=str(e)
            )
            
            self.db.add(notification)
            self.db.commit()
            
            return notification
    
    async def retry_notification(self, notification: models.Notification) -> bool:
        """Retry a failed notification"""
        try:
            notification.retry_count += 1
            
            if notification.channel == "telegram":
                success = await self._retry_telegram_notification(notification)
            elif notification.channel == "whatsapp":
                success = await self._retry_whatsapp_notification(notification)
            elif notification.channel == "fcm":
                success = await self._retry_fcm_notification(notification)
            else:
                success = False
            
            if success:
                notification.status = models.NotificationStatus.SENT
                notification.sent_at = datetime.utcnow()
                notification.error_message = None
            else:
                if notification.retry_count >= settings.MAX_RETRY_ATTEMPTS:
                    notification.status = models.NotificationStatus.FAILED
                else:
                    notification.status = models.NotificationStatus.RETRY
            
            self.db.commit()
            return success
            
        except Exception as e:
            logger.error(f"Error retrying notification {notification.id}: {e}")
            notification.error_message = str(e)
            self.db.commit()
            return False
    
    async def _retry_telegram_notification(self, notification: models.Notification) -> bool:
        """Retry Telegram notification"""
        try:
            url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            
            payload = {
                "chat_id": notification.recipient,
                "text": notification.message,
                "parse_mode": "HTML"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to retry Telegram notification {notification.id}: {e}")
            return False
    
    async def _retry_whatsapp_notification(self, notification: models.Notification) -> bool:
        """Retry WhatsApp notification"""
        try:
            url = f"https://graph.facebook.com/v17.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
            
            headers = {
                "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": notification.recipient,
                "type": "text",
                "text": {
                    "body": notification.message
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to retry WhatsApp notification {notification.id}: {e}")
            return False
    
    async def _retry_fcm_notification(self, notification: models.Notification) -> bool:
        """Retry FCM notification"""
        try:
            url = "https://fcm.googleapis.com/fcm/send"
            
            headers = {
                "Authorization": f"key={settings.FCM_SERVER_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "to": notification.recipient,
                "notification": {
                    "title": "LoRaGuard Alert",
                    "body": notification.message,
                    "sound": "default"
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to retry FCM notification {notification.id}: {e}")
            return False
