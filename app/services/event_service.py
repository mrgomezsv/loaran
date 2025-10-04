"""
Event processing service with filtering and business logic
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import logging

from app.models import models, schemas
from app.core.config import settings
from app.services.filter_service import FilterService
from app.services.alert_service import AlertService

logger = logging.getLogger(__name__)

class EventService:
    """Service for handling event processing and filtering"""
    
    def __init__(self, db: Session):
        self.db = db
        self.filter_service = FilterService(db)
        self.alert_service = AlertService(db)
    
    async def process_lora_event(self, payload: schemas.LoRaEventPayload) -> schemas.Event:
        """Process incoming LoRaWAN event"""
        try:
            # Create event record
            event_data = schemas.EventCreate(
                device_id=payload.device_id,
                timestamp=payload.timestamp,
                event_type=self._determine_event_type(payload.decoded),
                payload_raw=payload.payload_raw,
                decoded_data=json.dumps(payload.decoded),  # Convert to JSON string
                value=self._extract_value(payload.decoded),
                unit=self._extract_unit(payload.decoded)
            )
            
            # Save event to database
            db_event = models.Event(**event_data.dict())
            self.db.add(db_event)
            self.db.commit()
            self.db.refresh(db_event)
            
            # Apply filtering rules
            processed_event = await self.filter_service.apply_filters(db_event)
            
            # Create alerts if necessary
            if processed_event.severity in [models.SeverityLevel.HIGH, models.SeverityLevel.CRITICAL, models.SeverityLevel.CRITICAL_HIGH]:
                await self.alert_service.create_alert_from_event(processed_event)
            
            return schemas.Event.from_orm(processed_event)
            
        except Exception as e:
            logger.error(f"Error processing LoRa event: {e}")
            self.db.rollback()
            raise
    
    def _determine_event_type(self, decoded_data: Dict[str, Any]) -> models.EventType:
        """Determine event type from decoded data"""
        event_type = decoded_data.get("type", "").lower()
        
        if event_type in ["nivel", "level", "tank"]:
            return models.EventType.TANK_LEVEL
        elif event_type in ["movimiento", "motion", "mov"]:
            return models.EventType.MOTION
        elif event_type in ["puerta", "door", "apertura"]:
            return models.EventType.DOOR_OPEN
        elif event_type in ["temperatura", "temperature", "temp"]:
            return models.EventType.TEMPERATURE
        elif event_type in ["humedad", "humidity", "hum"]:
            return models.EventType.HUMIDITY
        else:
            # Default fallback
            return models.EventType.MOTION
    
    def _extract_value(self, decoded_data: Dict[str, Any]) -> Optional[float]:
        """Extract numeric value from decoded data"""
        value_fields = ["value", "level", "temperature", "humidity", "motion", "door_open"]
        
        for field in value_fields:
            if field in decoded_data:
                try:
                    return float(decoded_data[field])
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _extract_unit(self, decoded_data: Dict[str, Any]) -> Optional[str]:
        """Extract unit from decoded data"""
        return decoded_data.get("unit", "%")
    
    async def get_events(self, query: schemas.EventQuery) -> Tuple[List[schemas.Event], int]:
        """Get events with filtering"""
        db_query = self.db.query(models.Event)
        
        # Apply filters
        if query.device_id:
            db_query = db_query.filter(models.Event.device_id == query.device_id)
        
        if query.event_type:
            db_query = db_query.filter(models.Event.event_type == query.event_type)
        
        if query.severity:
            db_query = db_query.filter(models.Event.severity == query.severity)
        
        if query.start_date:
            db_query = db_query.filter(models.Event.timestamp >= query.start_date)
        
        if query.end_date:
            db_query = db_query.filter(models.Event.timestamp <= query.end_date)
        
        # Get total count
        total = db_query.count()
        
        # Apply pagination and ordering
        events = db_query.order_by(models.Event.timestamp.desc()).offset(query.offset).limit(query.limit).all()
        
        return [schemas.Event.from_orm(event) for event in events], total
    
    async def get_event_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get event statistics for the last N hours"""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Total events
        total_events = self.db.query(models.Event).filter(
            models.Event.timestamp >= start_time
        ).count()
        
        # Events by type
        events_by_type = self.db.query(
            models.Event.event_type,
            func.count(models.Event.id).label('count')
        ).filter(
            models.Event.timestamp >= start_time
        ).group_by(models.Event.event_type).all()
        
        # Events by severity
        events_by_severity = self.db.query(
            models.Event.severity,
            func.count(models.Event.id).label('count')
        ).filter(
            models.Event.timestamp >= start_time
        ).group_by(models.Event.severity).all()
        
        # Events by device
        events_by_device = self.db.query(
            models.Event.device_id,
            func.count(models.Event.id).label('count')
        ).filter(
            models.Event.timestamp >= start_time
        ).group_by(models.Event.device_id).all()
        
        return {
            "total_events": total_events,
            "time_range_hours": hours,
            "events_by_type": {str(item.event_type): item.count for item in events_by_type},
            "events_by_severity": {str(item.severity): item.count for item in events_by_severity},
            "events_by_device": {item.device_id: item.count for item in events_by_device},
            "generated_at": datetime.utcnow()
        }
    
    async def get_recent_events(self, device_id: str, limit: int = 10) -> List[schemas.Event]:
        """Get recent events for a specific device"""
        events = self.db.query(models.Event).filter(
            models.Event.device_id == device_id
        ).order_by(models.Event.timestamp.desc()).limit(limit).all()
        
        return [schemas.Event.from_orm(event) for event in events]
    
    async def get_correlated_events(self, device_id: str, window_seconds: int = 60) -> List[schemas.Event]:
        """Get events that might be correlated within a time window"""
        # This is a simplified correlation - in production you'd want more sophisticated logic
        recent_events = await self.get_recent_events(device_id, limit=50)
        
        if len(recent_events) < 2:
            return []
        
        # Group events by time windows
        correlated_groups = []
        current_group = [recent_events[0]]
        
        for event in recent_events[1:]:
            time_diff = (current_group[-1].timestamp - event.timestamp).total_seconds()
            
            if time_diff <= window_seconds:
                current_group.append(event)
            else:
                if len(current_group) > 1:
                    correlated_groups.extend(current_group)
                current_group = [event]
        
        if len(current_group) > 1:
            correlated_groups.extend(current_group)
        
        return correlated_groups
