"""
Simple in-memory user and session management for demo purposes.
Password hashing uses PBKDF2-HMAC (sha256). Not for production.
"""
from __future__ import annotations

import base64
import os
import secrets
import hashlib
from dataclasses import dataclass
from typing import Dict, Optional


def _hash_password(password: str, salt: bytes) -> str:
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return base64.b64encode(salt + dk).decode("utf-8")


def _verify_password(password: str, stored: str) -> bool:
    raw = base64.b64decode(stored.encode("utf-8"))
    salt, dk = raw[:16], raw[16:]
    new_dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return secrets.compare_digest(dk, new_dk)


@dataclass
class User:
    email: str
    password_hash: str
    full_name: str
    telegram_chat_id: str


class UserService:
    def __init__(self) -> None:
        self._users: Dict[str, User] = {}
        self._sessions: Dict[str, str] = {}  # token -> email
        self._otp_ok: Dict[str, bool] = {}   # token -> otp validated

    def register(self, email: str, password: str, full_name: str, telegram_chat_id: str) -> bool:
        if email in self._users:
            return False
        salt = os.urandom(16)
        ph = _hash_password(password, salt)
        self._users[email] = User(email=email, password_hash=ph, full_name=full_name, telegram_chat_id=telegram_chat_id)
        return True

    def login(self, email: str, password: str) -> Optional[str]:
        user = self._users.get(email)
        if not user:
            return None
        if not _verify_password(password, user.password_hash):
            return None
        token = secrets.token_urlsafe(24)
        self._sessions[token] = email
        self._otp_ok[token] = False
        return token

    def get_user_by_token(self, token: str) -> Optional[User]:
        email = self._sessions.get(token)
        if not email:
            return None
        return self._users.get(email)

    def mark_otp_valid(self, token: str) -> None:
        if token in self._otp_ok:
            self._otp_ok[token] = True

    def is_otp_valid(self, token: str) -> bool:
        return self._otp_ok.get(token, False)


