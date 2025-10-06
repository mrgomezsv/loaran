"""
OTP service for generating, sending, and validating time-bound one-time passwords via Telegram.
Stores OTP state in-memory for demo purposes; can be replaced by DB later.
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

import httpx

from app.core.config import settings


OTP_TTL_SECONDS = 120


@dataclass
class OtpRecord:
    user_id: str
    op_id: str
    code: str
    expires_at: datetime
    used_at: Optional[datetime] = None


class OtpService:
    """Simple in-memory OTP store and Telegram sender."""

    def __init__(self) -> None:
        self._store: Dict[Tuple[str, str], OtpRecord] = {}

    @staticmethod
    def _generate_code() -> str:
        return f"{secrets.randbelow(1_000_000):06d}"

    async def _send_telegram(self, chat_id: str, message: str) -> None:
        if not settings.TELEGRAM_BOT_TOKEN or not chat_id:
            raise ValueError("Telegram not configured")
        url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json={"chat_id": chat_id, "text": message})

    async def create_and_send(self, user_id: str, op_id: str, chat_id: str) -> OtpRecord:
        code = self._generate_code()
        record = OtpRecord(
            user_id=user_id,
            op_id=op_id,
            code=code,
            expires_at=datetime.utcnow() + timedelta(seconds=OTP_TTL_SECONDS),
        )
        self._store[(user_id, op_id)] = record
        await self._send_telegram(chat_id, f"Tu OTP LoRaGuard: {code} (expira en {OTP_TTL_SECONDS}s)")
        return record

    def validate_and_consume(self, user_id: str, op_id: str, code: str) -> bool:
        record = self._store.get((user_id, op_id))
        if not record:
            return False
        if record.used_at is not None:
            return False
        if datetime.utcnow() > record.expires_at:
            return False
        if record.code != code:
            return False
        record.used_at = datetime.utcnow()
        return True


