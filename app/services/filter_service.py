"""
Filter service for applying business rules and filtering logic
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
import logging

from app.models import models, schemas
from app.core.config import settings

logger = logging.getLogger(__name__)

class FilterService:
    """Service for applying filtering rules and business logic"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def apply_filters(self, event: models.Event) -> models.Event:
        """Apply all filtering rules to an event"""
        try:
            # Apply debounce filter
            if await self._should_debounce(event):
                event.severity = models.SeverityLevel.LOW
                event.is_processed = True
                logger.info(f"Event {event.id} debounced")
                return event
            
            # Apply tank level filter
            if event.event_type == models.EventType.TANK_LEVEL:
                event = await self._apply_tank_level_filter(event)
            
            # Apply motion filter
            elif event.event_type == models.EventType.MOTION:
                event = await self._apply_motion_filter(event)
            
            # Apply door open filter
            elif event.event_type == models.EventType.DOOR_OPEN:
                event = await self._apply_door_filter(event)
            
            # Apply correlation filter
            event = await self._apply_correlation_filter(event)
            
            # Apply time-based filters
            event = await self._apply_time_filters(event)
            
            # Mark as processed
            event.is_processed = True
            
            return event
            
        except Exception as e:
            logger.error(f"Error applying filters to event {event.id}: {e}")
            return event
    
    async def _should_debounce(self, event: models.Event) -> bool:
        """Check if event should be debounced (filtered out)"""
        debounce_time = timedelta(seconds=settings.DEBOUNCE_TIME_SECONDS)
        cutoff_time = event.timestamp - debounce_time
        
        # Check for similar events within debounce window
        similar_events = self.db.query(models.Event).filter(
            and_(
                models.Event.device_id == event.device_id,
                models.Event.event_type == event.event_type,
                models.Event.timestamp >= cutoff_time,
                models.Event.timestamp < event.timestamp,
                models.Event.is_processed == True
            )
        ).count()
        
        return similar_events > 0
    
    async def _apply_tank_level_filter(self, event: models.Event) -> models.Event:
        """Apply tank level specific filtering"""
        if event.value is None:
            return event
        
        # Tank level >= 90% triggers warning
        if event.value >= 90:
            event.severity = models.SeverityLevel.HIGH
            logger.warning(f"Tank level critical: {event.device_id} at {event.value}%")
        
        # Tank level >= 80% triggers medium alert
        elif event.value >= 80:
            event.severity = models.SeverityLevel.MEDIUM
        
        return event
    
    async def _apply_motion_filter(self, event: models.Event) -> models.Event:
        """Apply motion detection specific filtering"""
        if event.value is None or event.value == 0:
            return event
        
        # Check if motion is outside safe hours
        current_hour = event.timestamp.hour
        safe_start = settings.SAFE_HOURS_START
        safe_end = settings.SAFE_HOURS_END
        
        if not (safe_start <= current_hour <= safe_end):
            event.severity = models.SeverityLevel.CRITICAL
            logger.critical(f"Motion detected outside safe hours: {event.device_id} at {event.timestamp}")
        else:
            event.severity = models.SeverityLevel.MEDIUM
        
        return event
    
    async def _apply_door_filter(self, event: models.Event) -> models.Event:
        """Apply door open detection specific filtering"""
        if event.value is None or event.value == 0:
            return event
        
        # Door open is always medium severity
        event.severity = models.SeverityLevel.MEDIUM
        logger.warning(f"Door opened: {event.device_id}")
        
        return event
    
    async def _apply_correlation_filter(self, event: models.Event) -> models.Event:
        """Apply correlation-based filtering for multiple simultaneous events"""
        correlation_window = timedelta(seconds=settings.CORRELATION_WINDOW_SECONDS)
        start_time = event.timestamp - correlation_window
        end_time = event.timestamp + correlation_window
        
        # Find other events in the correlation window
        correlated_events = self.db.query(models.Event).filter(
            and_(
                models.Event.device_id == event.device_id,
                models.Event.timestamp >= start_time,
                models.Event.timestamp <= end_time,
                models.Event.id != event.id,
                models.Event.is_processed == True
            )
        ).all()
        
        # Check for critical correlations
        motion_events = [e for e in correlated_events if e.event_type == models.EventType.MOTION]
        door_events = [e for e in correlated_events if e.event_type == models.EventType.DOOR_OPEN]
        
        # Motion + Door open = Critical High
        if (event.event_type == models.EventType.MOTION and len(door_events) > 0) or \
           (event.event_type == models.EventType.DOOR_OPEN and len(motion_events) > 0):
            event.severity = models.SeverityLevel.CRITICAL_HIGH
            logger.critical(f"Critical correlation detected: {event.device_id} - Motion + Door")
        
        # Multiple motion events = High severity
        elif event.event_type == models.EventType.MOTION and len(motion_events) > 0:
            event.severity = models.SeverityLevel.HIGH
            logger.warning(f"Multiple motion events: {event.device_id}")
        
        return event
    
    async def _apply_time_filters(self, event: models.Event) -> models.Event:
        """Apply time-based filtering rules"""
        current_hour = event.timestamp.hour
        
        # Critical events during night hours get higher priority
        if current_hour < 6 or current_hour > 22:
            if event.severity == models.SeverityLevel.MEDIUM:
                event.severity = models.SeverityLevel.HIGH
            elif event.severity == models.SeverityLevel.HIGH:
                event.severity = models.SeverityLevel.CRITICAL
        
        return event
    
    async def create_filter_rule(self, rule_data: schemas.FilterRuleCreate) -> models.FilterRule:
        """Create a new filter rule"""
        db_rule = models.FilterRule(**rule_data.dict())
        self.db.add(db_rule)
        self.db.commit()
        self.db.refresh(db_rule)
        return db_rule
    
    async def get_filter_rules(self, event_type: Optional[models.EventType] = None) -> List[models.FilterRule]:
        """Get active filter rules"""
        query = self.db.query(models.FilterRule).filter(models.FilterRule.is_active == True)
        
        if event_type:
            query = query.filter(models.FilterRule.event_type == event_type)
        
        return query.all()
    
    async def apply_custom_rules(self, event: models.Event) -> models.Event:
        """Apply custom filter rules from database"""
        rules = await self.get_filter_rules(event.event_type)
        
        for rule in rules:
            try:
                condition = json.loads(rule.condition)
                
                # Simple condition evaluation (in production, use a proper rule engine)
                if self._evaluate_condition(event, condition):
                    if rule.severity_override:
                        event.severity = rule.severity_override
                        logger.info(f"Applied custom rule {rule.rule_name} to event {event.id}")
            except Exception as e:
                logger.error(f"Error applying rule {rule.rule_name}: {e}")
        
        return event
    
    def _evaluate_condition(self, event: models.Event, condition: Dict[str, Any]) -> bool:
        """Evaluate a condition against an event (simplified implementation)"""
        try:
            field = condition.get("field")
            operator = condition.get("operator")
            value = condition.get("value")
            
            if field == "value" and operator == ">=":
                return event.value is not None and event.value >= value
            elif field == "value" and operator == "<=":
                return event.value is not None and event.value <= value
            elif field == "hour" and operator == "not_between":
                current_hour = event.timestamp.hour
                return not (value[0] <= current_hour <= value[1])
            
            return False
        except Exception:
            return False
