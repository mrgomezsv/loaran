"""
Database models for LoRaGuard application
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum
from datetime import datetime

class EventType(str, enum.Enum):
    """Types of sensor events"""
    TANK_LEVEL = "tank_level"
    MOTION = "motion"
    DOOR_OPEN = "door_open"
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"

class SeverityLevel(str, enum.Enum):
    """Severity levels for events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    CRITICAL_HIGH = "critical-high"

class NotificationStatus(str, enum.Enum):
    """Status of notifications"""
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    RETRY = "retry"

class Device(Base):
    """Device model for LoRaWAN sensors"""
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), unique=True, index=True, nullable=False)
    device_name = Column(String(200), nullable=False)
    device_type = Column(Enum(EventType), nullable=False)
    location_id = Column(String(100), nullable=True)
    location_name = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    events = relationship("Event", back_populates="device")
    alerts = relationship("Alert", back_populates="device")

class Event(Base):
    """Event model for LoRaWAN sensor data"""
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), ForeignKey("devices.device_id"), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    event_type = Column(Enum(EventType), nullable=False)
    payload_raw = Column(Text, nullable=True)
    decoded_data = Column(Text, nullable=True)  # JSON string
    value = Column(Float, nullable=True)
    unit = Column(String(20), nullable=True)
    severity = Column(Enum(SeverityLevel), default=SeverityLevel.LOW)
    is_processed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    device = relationship("Device", back_populates="events")
    alerts = relationship("Alert", back_populates="event")

class Alert(Base):
    """Alert model for notifications"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(100), ForeignKey("devices.device_id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    alert_type = Column(String(50), nullable=False)
    severity = Column(Enum(SeverityLevel), nullable=False)
    message = Column(Text, nullable=False)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(100), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    device = relationship("Device", back_populates="alerts")
    event = relationship("Event", back_populates="alerts")
    notifications = relationship("Notification", back_populates="alert")

class Notification(Base):
    """Notification model for tracking sent notifications"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id"), nullable=False)
    channel = Column(String(50), nullable=False)  # telegram, whatsapp, fcm
    recipient = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    alert = relationship("Alert", back_populates="notifications")

class User(Base):
    """User accounts for authentication and Telegram linkage"""
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
    )

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    telegram_chat_id = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SessionToken(Base):
    """Session tokens persisted to avoid loss on reloads"""
    __tablename__ = "session_tokens"
    __table_args__ = (
        UniqueConstraint("token", name="uq_session_token_token"),
    )

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), nullable=False, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    otp_valid = Column(Boolean, default=False)
    pending_login_op = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
class FilterRule(Base):
    """Filter rules for event processing"""
    __tablename__ = "filter_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(100), unique=True, nullable=False)
    event_type = Column(Enum(EventType), nullable=False)
    condition = Column(Text, nullable=False)  # JSON string with conditions
    severity_override = Column(Enum(SeverityLevel), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
