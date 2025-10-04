"""
Device service for managing IoT devices
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.models import models, schemas

logger = logging.getLogger(__name__)

class DeviceService:
    """Service for managing IoT devices"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_device(self, device_data: schemas.DeviceCreate) -> models.Device:
        """Create a new device"""
        try:
            # Check if device already exists
            existing_device = self.db.query(models.Device).filter(
                models.Device.device_id == device_data.device_id
            ).first()
            
            if existing_device:
                raise ValueError(f"Device with ID {device_data.device_id} already exists")
            
            # Create new device
            db_device = models.Device(**device_data.dict())
            self.db.add(db_device)
            self.db.commit()
            self.db.refresh(db_device)
            
            logger.info(f"Created device: {device_data.device_id}")
            return db_device
            
        except Exception as e:
            logger.error(f"Error creating device {device_data.device_id}: {e}")
            self.db.rollback()
            raise
    
    async def get_device(self, device_id: str) -> Optional[models.Device]:
        """Get a device by ID"""
        return self.db.query(models.Device).filter(
            models.Device.device_id == device_id
        ).first()
    
    async def get_devices(self, active_only: bool = True) -> List[models.Device]:
        """Get all devices"""
        query = self.db.query(models.Device)
        
        if active_only:
            query = query.filter(models.Device.is_active == True)
        
        return query.order_by(models.Device.device_name).all()
    
    async def update_device(self, device_id: str, device_data: schemas.DeviceCreate) -> Optional[models.Device]:
        """Update a device"""
        try:
            device = await self.get_device(device_id)
            
            if not device:
                return None
            
            # Update device fields
            device.device_name = device_data.device_name
            device.device_type = device_data.device_type
            device.location_id = device_data.location_id
            device.location_name = device_data.location_name
            
            self.db.commit()
            self.db.refresh(device)
            
            logger.info(f"Updated device: {device_id}")
            return device
            
        except Exception as e:
            logger.error(f"Error updating device {device_id}: {e}")
            self.db.rollback()
            raise
    
    async def deactivate_device(self, device_id: str) -> bool:
        """Deactivate a device"""
        try:
            device = await self.get_device(device_id)
            
            if not device:
                return False
            
            device.is_active = False
            self.db.commit()
            
            logger.info(f"Deactivated device: {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deactivating device {device_id}: {e}")
            self.db.rollback()
            return False
    
    async def activate_device(self, device_id: str) -> bool:
        """Activate a device"""
        try:
            device = await self.get_device(device_id)
            
            if not device:
                return False
            
            device.is_active = True
            self.db.commit()
            
            logger.info(f"Activated device: {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error activating device {device_id}: {e}")
            self.db.rollback()
            return False
    
    async def get_device_stats(self, device_id: str) -> Dict[str, Any]:
        """Get statistics for a specific device"""
        device = await self.get_device(device_id)
        
        if not device:
            return {}
        
        # Count events by type
        events_by_type = self.db.query(
            models.Event.event_type,
            func.count(models.Event.id).label('count')
        ).filter(
            models.Event.device_id == device_id
        ).group_by(models.Event.event_type).all()
        
        # Count events by severity
        events_by_severity = self.db.query(
            models.Event.severity,
            func.count(models.Event.id).label('count')
        ).filter(
            models.Event.device_id == device_id
        ).group_by(models.Event.severity).all()
        
        # Count alerts
        total_alerts = self.db.query(models.Alert).filter(
            models.Alert.device_id == device_id
        ).count()
        
        # Count unacknowledged alerts
        unacknowledged_alerts = self.db.query(models.Alert).filter(
            and_(
                models.Alert.device_id == device_id,
                models.Alert.is_acknowledged == False
            )
        ).count()
        
        # Last event timestamp
        last_event = self.db.query(models.Event).filter(
            models.Event.device_id == device_id
        ).order_by(models.Event.timestamp.desc()).first()
        
        return {
            "device_id": device_id,
            "device_name": device.device_name,
            "device_type": device.device_type.value,
            "location": device.location_name,
            "is_active": device.is_active,
            "events_by_type": {str(item.event_type): item.count for item in events_by_type},
            "events_by_severity": {str(item.severity): item.count for item in events_by_severity},
            "total_alerts": total_alerts,
            "unacknowledged_alerts": unacknowledged_alerts,
            "last_event_timestamp": last_event.timestamp if last_event else None,
            "generated_at": datetime.utcnow()
        }
    
    async def create_default_devices(self) -> List[models.Device]:
        """Create default devices for demo purposes"""
        default_devices = [
            {
                "device_id": "sensor-tanque-01",
                "device_name": "Sensor Tanque Principal",
                "device_type": models.EventType.TANK_LEVEL,
                "location_id": "zona-a",
                "location_name": "Zona A - Tanque Principal"
            },
            {
                "device_id": "sensor-mov-01",
                "device_name": "Sensor Movimiento Entrada",
                "device_type": models.EventType.MOTION,
                "location_id": "zona-a",
                "location_name": "Zona A - Entrada Principal"
            },
            {
                "device_id": "sensor-puerta-01",
                "device_name": "Sensor Puerta Principal",
                "device_type": models.EventType.DOOR_OPEN,
                "location_id": "zona-a",
                "location_name": "Zona A - Puerta Principal"
            },
            {
                "device_id": "sensor-tanque-02",
                "device_name": "Sensor Tanque Secundario",
                "device_type": models.EventType.TANK_LEVEL,
                "location_id": "zona-b",
                "location_name": "Zona B - Tanque Secundario"
            },
            {
                "device_id": "sensor-mov-02",
                "device_name": "Sensor Movimiento Patio",
                "device_type": models.EventType.MOTION,
                "location_id": "zona-b",
                "location_name": "Zona B - Patio Trasero"
            }
        ]
        
        created_devices = []
        
        for device_data in default_devices:
            try:
                existing_device = await self.get_device(device_data["device_id"])
                if not existing_device:
                    device = models.Device(**device_data)
                    self.db.add(device)
                    created_devices.append(device)
            except Exception as e:
                logger.error(f"Error creating default device {device_data['device_id']}: {e}")
        
        if created_devices:
            self.db.commit()
            for device in created_devices:
                self.db.refresh(device)
            logger.info(f"Created {len(created_devices)} default devices")
        
        return created_devices
