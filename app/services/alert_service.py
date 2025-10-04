"""
Alert service for managing alerts and notifications
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from app.models import models, schemas
from app.core.config import settings
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class AlertService:
    """Service for managing alerts and notifications"""
    
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
    
    async def create_alert_from_event(self, event: models.Event) -> Optional[models.Alert]:
        """Create an alert from an event"""
        try:
            # Check if we should create an alert based on severity
            if event.severity in [models.SeverityLevel.LOW, models.SeverityLevel.MEDIUM]:
                return None
            
            # Check for recent similar alerts to avoid spam
            if await self._should_throttle_alert(event):
                logger.info(f"Throttling alert for event {event.id}")
                return None
            
            # Create alert
            alert_data = schemas.AlertCreate(
                device_id=event.device_id,
                event_id=event.id,
                alert_type=self._get_alert_type(event),
                severity=event.severity,
                message=self._generate_alert_message(event)
            )
            
            db_alert = models.Alert(**alert_data.dict())
            self.db.add(db_alert)
            self.db.commit()
            self.db.refresh(db_alert)
            
            # Send notifications
            await self.notification_service.send_alert_notifications(db_alert)
            
            logger.info(f"Created alert {db_alert.id} for event {event.id}")
            return db_alert
            
        except Exception as e:
            logger.error(f"Error creating alert from event {event.id}: {e}")
            self.db.rollback()
            return None
    
    async def _should_throttle_alert(self, event: models.Event) -> bool:
        """Check if we should throttle alert creation"""
        cooldown_time = timedelta(seconds=settings.CRITICAL_ALERT_COOLDOWN_SECONDS)
        cutoff_time = event.timestamp - cooldown_time
        
        # Check for recent alerts of same type and severity
        recent_alerts = self.db.query(models.Alert).filter(
            and_(
                models.Alert.device_id == event.device_id,
                models.Alert.alert_type == self._get_alert_type(event),
                models.Alert.severity == event.severity,
                models.Alert.created_at >= cutoff_time
            )
        ).count()
        
        return recent_alerts > 0
    
    def _get_alert_type(self, event: models.Event) -> str:
        """Get alert type based on event"""
        if event.event_type == models.EventType.TANK_LEVEL:
            return "tank_level_critical"
        elif event.event_type == models.EventType.MOTION:
            return "motion_detected"
        elif event.event_type == models.EventType.DOOR_OPEN:
            return "door_opened"
        else:
            return "sensor_event"
    
    def _generate_alert_message(self, event: models.Event) -> str:
        """Generate alert message based on event"""
        device_name = event.device_id.replace("-", " ").title()
        timestamp_str = event.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        if event.event_type == models.EventType.TANK_LEVEL:
            return f"🚨 Alerta LoRaGuard: Tanque {device_name} al {event.value}% (llenado). Acción recomendada: Programar vaciado. Timestamp: {timestamp_str}"
        
        elif event.event_type == models.EventType.MOTION:
            current_hour = event.timestamp.hour
            if current_hour < 6 or current_hour > 22:
                return f"🚨 ¡Alerta crítica! Movimiento detectado en {device_name} a las {event.timestamp.strftime('%H:%M')}. Revisar inmediatamente."
            else:
                return f"⚠️ Movimiento detectado en {device_name} a las {event.timestamp.strftime('%H:%M')}. Verificar actividad."
        
        elif event.event_type == models.EventType.DOOR_OPEN:
            return f"🚪 Puerta abierta en {device_name} a las {event.timestamp.strftime('%H:%M')}. Verificar acceso autorizado."
        
        else:
            return f"📊 Evento de sensor en {device_name}: {event.event_type.value} a las {timestamp_str}"
    
    async def get_alerts(self, query: schemas.AlertQuery) -> Tuple[List[schemas.Alert], int]:
        """Get alerts with filtering"""
        db_query = self.db.query(models.Alert)
        
        # Apply filters
        if query.device_id:
            db_query = db_query.filter(models.Alert.device_id == query.device_id)
        
        if query.severity:
            db_query = db_query.filter(models.Alert.severity == query.severity)
        
        if query.is_acknowledged is not None:
            db_query = db_query.filter(models.Alert.is_acknowledged == query.is_acknowledged)
        
        if query.start_date:
            db_query = db_query.filter(models.Alert.created_at >= query.start_date)
        
        if query.end_date:
            db_query = db_query.filter(models.Alert.created_at <= query.end_date)
        
        # Get total count
        total = db_query.count()
        
        # Apply pagination and ordering
        alerts = db_query.order_by(models.Alert.created_at.desc()).offset(query.offset).limit(query.limit).all()
        
        return [schemas.Alert.from_orm(alert) for alert in alerts], total
    
    async def acknowledge_alert(self, alert_id: int, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        try:
            alert = self.db.query(models.Alert).filter(models.Alert.id == alert_id).first()
            
            if not alert:
                return False
            
            alert.is_acknowledged = True
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.utcnow()
            
            self.db.commit()
            logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
            return True
            
        except Exception as e:
            logger.error(f"Error acknowledging alert {alert_id}: {e}")
            self.db.rollback()
            return False
    
    async def get_alert_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert statistics for the last N hours"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Total alerts
        total_alerts = self.db.query(models.Alert).filter(
            models.Alert.created_at >= start_time
        ).count()
        
        # Alerts by severity
        alerts_by_severity = self.db.query(
            models.Alert.severity,
            func.count(models.Alert.id).label('count')
        ).filter(
            models.Alert.created_at >= start_time
        ).group_by(models.Alert.severity).all()
        
        # Alerts by type
        alerts_by_type = self.db.query(
            models.Alert.alert_type,
            func.count(models.Alert.id).label('count')
        ).filter(
            models.Alert.created_at >= start_time
        ).group_by(models.Alert.alert_type).all()
        
        # Acknowledged vs unacknowledged
        acknowledged_count = self.db.query(models.Alert).filter(
            and_(
                models.Alert.created_at >= start_time,
                models.Alert.is_acknowledged == True
            )
        ).count()
        
        return {
            "total_alerts": total_alerts,
            "acknowledged_alerts": acknowledged_count,
            "unacknowledged_alerts": total_alerts - acknowledged_count,
            "time_range_hours": hours,
            "alerts_by_severity": {str(item.severity): item.count for item in alerts_by_severity},
            "alerts_by_type": {item.alert_type: item.count for item in alerts_by_type},
            "generated_at": datetime.utcnow()
        }
    
    async def retry_failed_notifications(self) -> int:
        """Retry failed notifications"""
        failed_notifications = self.db.query(models.Notification).filter(
            and_(
                models.Notification.status == models.NotificationStatus.FAILED,
                models.Notification.retry_count < settings.MAX_RETRY_ATTEMPTS
            )
        ).all()
        
        retry_count = 0
        for notification in failed_notifications:
            try:
                success = await self.notification_service.retry_notification(notification)
                if success:
                    retry_count += 1
            except Exception as e:
                logger.error(f"Error retrying notification {notification.id}: {e}")
        
        return retry_count
