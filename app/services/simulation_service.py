"""
Simulation service for testing and demo purposes
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import random

from app.models import models, schemas
from app.services.event_service import EventService
from app.services.alert_service import AlertService

logger = logging.getLogger(__name__)

class SimulationService:
    """Service for simulating sensor events for testing and demo"""
    
    def __init__(self, db: Session):
        self.db = db
        self.event_service = EventService(db)
        self.alert_service = AlertService(db)
    
    async def simulate_event(self, simulation: schemas.SimulationRequest) -> schemas.SimulationResponse:
        """Simulate a sensor event"""
        try:
            # Set default timestamp if not provided
            timestamp = simulation.timestamp or datetime.utcnow()
            
            # Create decoded data based on event type
            decoded_data = self._create_decoded_data(simulation)
            
            # Create LoRaWAN payload
            payload = schemas.LoRaEventPayload(
                device_id=simulation.device_id,
                timestamp=timestamp,
                payload_raw=self._encode_payload(decoded_data),
                decoded=decoded_data
            )
            
            # Process the event
            event = await self.event_service.process_lora_event(payload)
            
            # Check if an alert was created
            alert = self.db.query(models.Alert).filter(
                models.Alert.event_id == event.id
            ).first()
            
            return schemas.SimulationResponse(
                success=True,
                message=f"Event simulated successfully",
                event_id=event.id,
                alert_id=alert.id if alert else None
            )
            
        except Exception as e:
            logger.error(f"Error simulating event: {e}")
            return schemas.SimulationResponse(
                success=False,
                message=str(e)
            )
    
    def _create_decoded_data(self, simulation: schemas.SimulationRequest) -> Dict[str, Any]:
        """Create decoded data based on simulation parameters"""
        decoded_data = {
            "type": simulation.event_type.value,
            "timestamp": simulation.timestamp.isoformat() if simulation.timestamp else datetime.utcnow().isoformat()
        }
        
        if simulation.event_type == models.EventType.TANK_LEVEL:
            decoded_data.update({
                "level": simulation.value or random.randint(0, 100),
                "unit": simulation.unit or "%",
                "temperature": random.randint(15, 35),
                "pressure": random.uniform(1.0, 3.0)
            })
        
        elif simulation.event_type == models.EventType.MOTION:
            decoded_data.update({
                "motion": simulation.value or random.choice([0, 1]),
                "confidence": random.uniform(0.7, 1.0),
                "duration": random.randint(1, 10)
            })
        
        elif simulation.event_type == models.EventType.DOOR_OPEN:
            decoded_data.update({
                "door_open": simulation.value or random.choice([0, 1]),
                "magnetic_field": random.uniform(0.1, 0.9),
                "battery_level": random.randint(20, 100)
            })
        
        elif simulation.event_type == models.EventType.TEMPERATURE:
            decoded_data.update({
                "temperature": simulation.value or random.uniform(-10, 50),
                "unit": simulation.unit or "°C",
                "humidity": random.uniform(30, 90)
            })
        
        elif simulation.event_type == models.EventType.HUMIDITY:
            decoded_data.update({
                "humidity": simulation.value or random.uniform(20, 100),
                "unit": simulation.unit or "%",
                "temperature": random.uniform(15, 35)
            })
        
        # Add any additional decoded data
        if simulation.decoded_data:
            decoded_data.update(simulation.decoded_data)
        
        return decoded_data
    
    def _encode_payload(self, decoded_data: Dict[str, Any]) -> str:
        """Encode payload data (simplified for demo)"""
        import json
        return json.dumps(decoded_data)
    
    async def simulate_tank_fill_scenario(self) -> List[schemas.SimulationResponse]:
        """Simulate tank filling scenario (Case A)"""
        scenarios = [
            schemas.SimulationRequest(
                device_id="sensor-tanque-01",
                event_type=models.EventType.TANK_LEVEL,
                value=95.0,
                unit="%"
            ),
            schemas.SimulationRequest(
                device_id="sensor-tanque-01",
                event_type=models.EventType.TANK_LEVEL,
                value=98.0,
                unit="%"
            )
        ]
        
        results = []
        for scenario in scenarios:
            result = await self.simulate_event(scenario)
            results.append(result)
        
        return results
    
    async def simulate_false_positive_scenario(self) -> List[schemas.SimulationResponse]:
        """Simulate false positive scenario (Case B) - debounce test"""
        # Send multiple motion events in quick succession
        scenarios = []
        base_time = datetime.utcnow()
        
        for i in range(5):
            scenarios.append(
                schemas.SimulationRequest(
                    device_id="sensor-mov-01",
                    event_type=models.EventType.MOTION,
                    value=1,
                    timestamp=base_time + timedelta(seconds=i*2)  # 2 seconds apart
                )
            )
        
        results = []
        for scenario in scenarios:
            result = await self.simulate_event(scenario)
            results.append(result)
        
        return results
    
    async def simulate_correlation_scenario(self) -> List[schemas.SimulationResponse]:
        """Simulate correlation scenario (Case C) - motion + door"""
        base_time = datetime.utcnow()
        
        scenarios = [
            schemas.SimulationRequest(
                device_id="sensor-mov-01",
                event_type=models.EventType.MOTION,
                value=1,
                timestamp=base_time
            ),
            schemas.SimulationRequest(
                device_id="sensor-puerta-01",
                event_type=models.EventType.DOOR_OPEN,
                value=1,
                timestamp=base_time + timedelta(seconds=30)  # 30 seconds later
            )
        ]
        
        results = []
        for scenario in scenarios:
            result = await self.simulate_event(scenario)
            results.append(result)
        
        return results
    
    async def simulate_night_movement_scenario(self) -> List[schemas.SimulationResponse]:
        """Simulate night movement scenario (Case D)"""
        # Create timestamp for 3 AM
        night_time = datetime.utcnow().replace(hour=3, minute=0, second=0, microsecond=0)
        
        scenarios = [
            schemas.SimulationRequest(
                device_id="sensor-mov-01",
                event_type=models.EventType.MOTION,
                value=1,
                timestamp=night_time
            ),
            schemas.SimulationRequest(
                device_id="sensor-mov-02",
                event_type=models.EventType.MOTION,
                value=1,
                timestamp=night_time + timedelta(minutes=5)
            )
        ]
        
        results = []
        for scenario in scenarios:
            result = await self.simulate_event(scenario)
            results.append(result)
        
        return results
    
    async def simulate_random_events(self, count: int = 10) -> List[schemas.SimulationResponse]:
        """Simulate random events for load testing"""
        device_ids = ["sensor-tanque-01", "sensor-mov-01", "sensor-puerta-01", "sensor-tanque-02", "sensor-mov-02"]
        event_types = list(models.EventType)
        
        scenarios = []
        for _ in range(count):
            device_id = random.choice(device_ids)
            event_type = random.choice(event_types)
            
            # Generate appropriate values based on event type
            if event_type == models.EventType.TANK_LEVEL:
                value = random.uniform(0, 100)
                unit = "%"
            elif event_type == models.EventType.MOTION:
                value = random.choice([0, 1])
                unit = None
            elif event_type == models.EventType.DOOR_OPEN:
                value = random.choice([0, 1])
                unit = None
            elif event_type == models.EventType.TEMPERATURE:
                value = random.uniform(-10, 50)
                unit = "°C"
            elif event_type == models.EventType.HUMIDITY:
                value = random.uniform(20, 100)
                unit = "%"
            else:
                value = random.uniform(0, 100)
                unit = None
            
            scenarios.append(
                schemas.SimulationRequest(
                    device_id=device_id,
                    event_type=event_type,
                    value=value,
                    unit=unit,
                    timestamp=datetime.utcnow() - timedelta(minutes=random.randint(0, 60))
                )
            )
        
        results = []
        for scenario in scenarios:
            result = await self.simulate_event(scenario)
            results.append(result)
        
        return results
    
    async def get_simulation_stats(self) -> Dict[str, Any]:
        """Get statistics about simulated events"""
        # Count events by device
        events_by_device = self.db.query(
            models.Event.device_id,
            func.count(models.Event.id).label('count')
        ).group_by(models.Event.device_id).all()
        
        # Count alerts by severity
        alerts_by_severity = self.db.query(
            models.Alert.severity,
            func.count(models.Alert.id).label('count')
        ).group_by(models.Alert.severity).all()
        
        # Count notifications by channel
        notifications_by_channel = self.db.query(
            models.Notification.channel,
            func.count(models.Notification.id).label('count')
        ).group_by(models.Notification.channel).all()
        
        return {
            "events_by_device": {item.device_id: item.count for item in events_by_device},
            "alerts_by_severity": {str(item.severity): item.count for item in alerts_by_severity},
            "notifications_by_channel": {item.channel: item.count for item in notifications_by_channel},
            "generated_at": datetime.utcnow()
        }
