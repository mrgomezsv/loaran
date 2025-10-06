"""
API endpoints for LoRaGuard application
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models import schemas
from app.services.event_service import EventService
from app.services.alert_service import AlertService
from app.services.device_service import DeviceService
from app.services.simulation_service import SimulationService
from app.services.otp_service import OtpService
from app.services.encryption_service import EncryptionService
from app.core.config import settings
from app.services.user_service import UserService, DbUserService
from app.services.file_service import FileService

# Create API router
api_router = APIRouter()
otp_service = OtpService()
user_service = UserService()
file_service = FileService()

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

# Auth (demo)
@api_router.post("/auth/register")
async def register_user(req: schemas.RegisterRequest, db: Session = Depends(get_db)):
    created = DbUserService(db).register(req.email, req.password, req.full_name, req.telegram_chat_id)
    if not created:
        raise HTTPException(status_code=400, detail="Email ya registrado")
    return {"success": True}

@api_router.post("/auth/login", response_model=schemas.LoginResponse)
async def login_user(req: schemas.LoginRequest, db: Session = Depends(get_db)):
    token = DbUserService(db).login(req.email, req.password)
    if not token:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    return schemas.LoginResponse(token=token)

@api_router.post("/auth/request-otp", response_model=schemas.RequestOtpResponse)
async def auth_request_otp(token: str, db: Session = Depends(get_db)):
    db_users = DbUserService(db)
    user = db_users.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Token inválido")
    op_id = f"login_{int(datetime.utcnow().timestamp())}"
    try:
        await otp_service.create_and_send(user_id=user.email, op_id=op_id, chat_id=user.telegram_chat_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Error enviando OTP por Telegram: {e}")
    db_users.set_pending_login_op(token, op_id)
    return schemas.RequestOtpResponse(message="OTP enviado por Telegram")

@api_router.post("/auth/confirm-otp")
async def auth_confirm_otp(token: str, otp_code: str, db: Session = Depends(get_db)):
    db_users = DbUserService(db)
    user = db_users.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Token inválido")
    op_id = db_users.pop_pending_login_op(token)
    if not op_id:
        raise HTTPException(status_code=400, detail="No hay OTP pendiente para este token")
    valid = otp_service.validate_and_consume(user_id=user.email, op_id=op_id, code=otp_code)
    if not valid:
        raise HTTPException(status_code=401, detail="OTP inválido o expirado")
    db_users.mark_otp_valid(token)
    return {"success": True}

# Files (require OTP validated session token)
@api_router.get("/files")
async def list_files(token: str, db: Session = Depends(get_db)):
    if not DbUserService(db).is_otp_valid(token):
        raise HTTPException(status_code=401, detail="OTP requerido")
    return {"items": file_service.list_files()}

@api_router.get("/files/{file_id}")
async def download_file(file_id: str, token: str, db: Session = Depends(get_db)):
    if not DbUserService(db).is_otp_valid(token):
        raise HTTPException(status_code=401, detail="OTP requerido")
    try:
        data = file_service.get_file_plain(file_id)
        return {"file_id": file_id, "content": data.decode("utf-8", errors="replace")}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

# Security: critical operations with OTP
@api_router.post("/security/critical/request", response_model=schemas.CriticalOpInitResponse)
async def request_critical_operation(
    req: schemas.CriticalOpRequest,
):
    """Initiate a critical operation: generate and send OTP via Telegram.
    Demo: if op_type == 'download_file', we prepare an encrypted blob.
    The actual data is only returned upon confirmation.
    """
    # For demo purposes, derive a simple op_id
    op_id = f"op_{int(datetime.utcnow().timestamp())}"

    # Optional: prepare demo encrypted data for 'download_file'
    if req.op_type == "download_file":
        plaintext = (req.payload.get("content") or "Demo secreto LoRaGuard").encode("utf-8")
        enc_data, wrapped_key, algo = EncryptionService.encrypt_bytes(plaintext)
        # Store minimal state in DB or memory; here we attach to OTP store payload-free,
        # but return metadata later after OTP.
        _db_op_payload = {
            "enc_data": enc_data,
            "wrapped_key": wrapped_key,
            "algo": algo,
        }
        # In real code you'd persist db_op_payload tied to op_id and user.
        # For demo, we keep only OTP state and reconstruct result on confirm.
        # We serialize minimally via memory store (not implemented here).

    # Resolve user's Telegram chat id. Demo: single global chat from settings.
    chat_id = settings.TELEGRAM_CHAT_ID
    user_id = "demo-user"  # Replace with real authenticated user id

    record = await otp_service.create_and_send(user_id=user_id, op_id=op_id, chat_id=chat_id)
    return schemas.CriticalOpInitResponse(
        op_id=op_id,
        expires_at=record.expires_at,
        message="OTP enviado por Telegram"
    )

@api_router.post("/security/critical/confirm", response_model=schemas.CriticalOpResult)
async def confirm_critical_operation(
    req: schemas.CriticalOpConfirmRequest,
):
    """Confirm a critical operation by validating OTP. For demo returns sample data."""
    user_id = "demo-user"
    valid = otp_service.validate_and_consume(user_id=user_id, op_id=req.op_id, code=req.otp_code)
    if not valid:
        raise HTTPException(status_code=401, detail="OTP inválido o expirado")

    # In a real system, load op payload (e.g., encrypted file), decrypt and return.
    # Here just return a demo payload.
    return schemas.CriticalOpResult(
        success=True,
        message="Operación crítica confirmada",
        data={"note": "Ejemplo: autorizado para descargar recurso sensible"}
    )
