"""
Pydantic schemas for API request/response models
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.models import EventType, SeverityLevel, NotificationStatus

# Base schemas
class DeviceBase(BaseModel):
    device_id: str = Field(..., description="Unique device identifier")
    device_name: str = Field(..., description="Human-readable device name")
    device_type: EventType = Field(..., description="Type of sensor")
    location_id: Optional[str] = Field(None, description="Location identifier")
    location_name: Optional[str] = Field(None, description="Location name")

class DeviceCreate(DeviceBase):
    pass

class Device(DeviceBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Event schemas
class LoRaEventPayload(BaseModel):
    """Payload for LoRaWAN events"""
    device_id: str = Field(..., description="Device identifier")
    timestamp: datetime = Field(..., description="Event timestamp")
    payload_raw: Optional[str] = Field(None, description="Raw payload data")
    decoded: Dict[str, Any] = Field(..., description="Decoded sensor data")

class EventBase(BaseModel):
    device_id: str
    timestamp: datetime
    event_type: EventType
    payload_raw: Optional[str] = None
    decoded_data: Optional[str] = None  # JSON string
    value: Optional[float] = None
    unit: Optional[str] = None
    severity: SeverityLevel = SeverityLevel.LOW

class EventCreate(EventBase):
    pass

class Event(EventBase):
    id: int
    is_processed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# Alert schemas
class AlertBase(BaseModel):
    device_id: str
    alert_type: str
    severity: SeverityLevel
    message: str

class AlertCreate(AlertBase):
    event_id: Optional[int] = None

class Alert(AlertBase):
    id: int
    event_id: Optional[int] = None
    is_acknowledged: bool
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    retry_count: int
    max_retries: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Notification schemas
class NotificationBase(BaseModel):
    alert_id: int
    channel: str
    recipient: str
    message: str

class NotificationCreate(NotificationBase):
    pass

class Notification(NotificationBase):
    id: int
    status: NotificationStatus
    sent_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# Simulation schemas
class SimulationRequest(BaseModel):
    """Request schema for simulating sensor events"""
    device_id: str = Field(..., description="Device identifier")
    event_type: EventType = Field(..., description="Type of event to simulate")
    timestamp: Optional[datetime] = Field(None, description="Event timestamp (defaults to now)")
    value: Optional[float] = Field(None, description="Sensor value")
    unit: Optional[str] = Field(None, description="Value unit")
    decoded_data: Optional[Dict[str, Any]] = Field(None, description="Additional decoded data")

class SimulationResponse(BaseModel):
    """Response schema for simulation requests"""
    success: bool
    message: str
    event_id: Optional[int] = None
    alert_id: Optional[int] = None

# Query schemas
class EventQuery(BaseModel):
    """Query parameters for events"""
    device_id: Optional[str] = None
    event_type: Optional[EventType] = None
    severity: Optional[SeverityLevel] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)

class AlertQuery(BaseModel):
    """Query parameters for alerts"""
    device_id: Optional[str] = None
    severity: Optional[SeverityLevel] = None
    is_acknowledged: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)

# Response schemas
class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
    timestamp: datetime
    version: str = "1.0.0"

# Filter rule schemas
class FilterRuleBase(BaseModel):
    rule_name: str
    event_type: EventType
    condition: Dict[str, Any]
    severity_override: Optional[SeverityLevel] = None
    is_active: bool = True

class FilterRuleCreate(FilterRuleBase):
    pass

class FilterRule(FilterRuleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
