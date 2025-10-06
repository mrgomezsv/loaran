"""
Configuration settings for LoRaGuard application
"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./loraguard.db"
    
    # LoRaWAN Configuration
    LORA_SERVER_URL: str = "http://localhost:8080"
    LORA_WEBHOOK_SECRET: Optional[str] = None
    
    # Notification Services
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    
    WHATSAPP_ACCESS_TOKEN: Optional[str] = None
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = None
    WHATSAPP_WEBHOOK_VERIFY_TOKEN: Optional[str] = None
    
    # Twilio Configuration
    TWILIO_ACCOUNT_SID: Optional[str] = None
    TWILIO_AUTH_TOKEN: Optional[str] = None
    TWILIO_WHATSAPP_NUMBER: str = "whatsapp:+14155238886"
    
    # Firebase Cloud Messaging
    FCM_SERVER_KEY: Optional[str] = None
    FCM_PROJECT_ID: Optional[str] = None

    # Encryption master key (base64, 32 bytes)
    MASTER_KEY_B64: Optional[str] = None
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Application Settings
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    MAX_EVENTS_PER_PAGE: int = 100
    
    # Filter Settings
    DEBOUNCE_TIME_SECONDS: int = 30
    CORRELATION_WINDOW_SECONDS: int = 60
    SAFE_HOURS_START: int = 7
    SAFE_HOURS_END: int = 21
    
    # Alert Settings
    MAX_RETRY_ATTEMPTS: int = 3
    RETRY_DELAY_SECONDS: int = 300
    CRITICAL_ALERT_COOLDOWN_SECONDS: int = 1800
    
    class Config:
        env_file = "config.env"
        case_sensitive = True

# Create settings instance
settings = Settings()
