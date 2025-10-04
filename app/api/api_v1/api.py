"""
API endpoints for LoRaGuard application
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models import schemas, models
from app.services.event_service import EventService
from app.services.alert_service import AlertService
from app.services.device_service import DeviceService
from app.services.simulation_service import SimulationService

# Create API router
api_router = APIRouter()

# Event endpoints
@api_router.post("/events/lora", response_model=schemas.Event)
async def receive_lora_event(
    payload: schemas.LoRaEventPayload,
    db: Session = Depends(get_db)
):
    """Receive LoRaWAN event from gateway/server"""
    try:
        event_service = EventService(db)
        event = await event_service.process_lora_event(payload)
        return event
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/events", response_model=schemas.PaginatedResponse)
async def get_events(
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    event_type: Optional[schemas.EventType] = Query(None, description="Filter by event type"),
    severity: Optional[schemas.SeverityLevel] = Query(None, description="Filter by severity"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(100, ge=1, le=1000, description="Number of events to return"),
    offset: int = Query(0, ge=0, description="Number of events to skip"),
    db: Session = Depends(get_db)
):
    """Get events with optional filtering"""
    event_service = EventService(db)
    query = schemas.EventQuery(
        device_id=device_id,
        event_type=event_type,
        severity=severity,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    
    events, total = await event_service.get_events(query)
    
    return schemas.PaginatedResponse(
        items=events,
        total=total,
        page=offset // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )

# Alert endpoints
@api_router.get("/alerts", response_model=schemas.PaginatedResponse)
async def get_alerts(
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    severity: Optional[schemas.SeverityLevel] = Query(None, description="Filter by severity"),
    is_acknowledged: Optional[bool] = Query(None, description="Filter by acknowledgment status"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(100, ge=1, le=1000, description="Number of alerts to return"),
    offset: int = Query(0, ge=0, description="Number of alerts to skip"),
    db: Session = Depends(get_db)
):
    """Get alerts with optional filtering"""
    alert_service = AlertService(db)
    query = schemas.AlertQuery(
        device_id=device_id,
        severity=severity,
        is_acknowledged=is_acknowledged,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        offset=offset
    )
    
    alerts, total = await alert_service.get_alerts(query)
    
    return schemas.PaginatedResponse(
        items=alerts,
        total=total,
        page=offset // limit + 1,
        size=limit,
        pages=(total + limit - 1) // limit
    )

@api_router.post("/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    acknowledged_by: str = Query(..., description="User acknowledging the alert"),
    db: Session = Depends(get_db)
):
    """Acknowledge an alert"""
    alert_service = AlertService(db)
    success = await alert_service.acknowledge_alert(alert_id, acknowledged_by)
    
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    return {"success": True, "message": "Alert acknowledged successfully"}

# Device endpoints
@api_router.get("/devices", response_model=List[schemas.Device])
async def get_devices(
    active_only: bool = Query(True, description="Return only active devices"),
    db: Session = Depends(get_db)
):
    """Get all devices"""
    device_service = DeviceService(db)
    devices = await device_service.get_devices(active_only=active_only)
    return devices

@api_router.post("/devices", response_model=schemas.Device)
async def create_device(
    device: schemas.DeviceCreate,
    db: Session = Depends(get_db)
):
    """Create a new device"""
    device_service = DeviceService(db)
    try:
        new_device = await device_service.create_device(device)
        return new_device
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/devices/{device_id}", response_model=schemas.Device)
async def get_device(
    device_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific device"""
    device_service = DeviceService(db)
    device = await device_service.get_device(device_id)
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return device

# Simulation endpoints
@api_router.post("/admin/simulate", response_model=schemas.SimulationResponse)
async def simulate_event(
    simulation: schemas.SimulationRequest,
    db: Session = Depends(get_db)
):
    """Simulate a sensor event for testing"""
    simulation_service = SimulationService(db)
    try:
        result = await simulation_service.simulate_event(simulation)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.post("/admin/simulate/bulk")
async def simulate_bulk_events(
    simulations: List[schemas.SimulationRequest],
    db: Session = Depends(get_db)
):
    """Simulate multiple events for testing"""
    simulation_service = SimulationService(db)
    results = []
    
    for simulation in simulations:
        try:
            result = await simulation_service.simulate_event(simulation)
            results.append(result)
        except Exception as e:
            results.append(schemas.SimulationResponse(
                success=False,
                message=str(e)
            ))
    
    return {"results": results}

# Statistics endpoints
@api_router.get("/stats/events")
async def get_event_stats(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    db: Session = Depends(get_db)
):
    """Get event statistics"""
    event_service = EventService(db)
    stats = await event_service.get_event_stats(hours)
    return stats

@api_router.get("/stats/alerts")
async def get_alert_stats(
    hours: int = Query(24, ge=1, le=168, description="Hours to look back"),
    db: Session = Depends(get_db)
):
    """Get alert statistics"""
    alert_service = AlertService(db)
    stats = await alert_service.get_alert_stats(hours)
    return stats

# Health check
@api_router.get("/health", response_model=schemas.HealthResponse)
async def health_check():
    """Health check endpoint"""
    return schemas.HealthResponse(
        status="healthy",
        service="LoRaGuard API",
        timestamp=datetime.utcnow()
    )
