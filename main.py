"""
LoRaGuard - Main Application Entry Point
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.api_v1.api import api_router
from app.core.database import engine
from app.models import models

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="LoRaGuard API",
    description="Prototipo de Sistema de Seguridad IoT con LoRaWAN",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
async def root():
    """Root endpoint with basic API information"""
    return {
        "message": "LoRaGuard API - Sistema de Seguridad IoT con LoRaWAN",
        "version": "1.0.0",
        "docs": f"{settings.API_V1_STR}/docs",
        "health": f"{settings.API_V1_STR}/health"
    }

@app.get(f"{settings.API_V1_STR}/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "LoRaGuard API"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
