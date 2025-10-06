"""
User and session management. Includes an in-memory demo service and a DB-backed service.
Password hashing uses PBKDF2-HMAC (sha256). Not for production.
"""
from __future__ import annotations

import base64
import os
import secrets
import hashlib
from dataclasses import dataclass
from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.models import models


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
        self._pending_login_op: Dict[str, str] = {}  # token -> op_id

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

    def set_pending_login_op(self, token: str, op_id: str) -> None:
        self._pending_login_op[token] = op_id

    def pop_pending_login_op(self, token: str) -> Optional[str]:
        return self._pending_login_op.pop(token, None)


class DbUserService:
    """DB-backed user/session service (SQLite via SQLAlchemy)."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def register(self, email: str, password: str, full_name: str, telegram_chat_id: str) -> bool:
        exists = self.db.query(models.User).filter(models.User.email == email).first()
        if exists:
            return False
        salt = os.urandom(16)
        ph = _hash_password(password, salt)
        user = models.User(email=email, password_hash=ph, full_name=full_name, telegram_chat_id=telegram_chat_id)
        self.db.add(user)
        self.db.commit()
        return True

    def login(self, email: str, password: str) -> Optional[str]:
        user = self.db.query(models.User).filter(models.User.email == email).first()
        if not user:
            return None
        if not _verify_password(password, user.password_hash):
            return None
        token = secrets.token_urlsafe(24)
        sess = models.SessionToken(token=token, user_id=user.id, otp_valid=False)
        self.db.add(sess)
        self.db.commit()
        return token

    def get_user_by_token(self, token: str) -> Optional[models.User]:
        sess = self.db.query(models.SessionToken).filter(models.SessionToken.token == token).first()
        if not sess:
            return None
        return self.db.query(models.User).filter(models.User.id == sess.user_id).first()

    def mark_otp_valid(self, token: str) -> None:
        sess = self.db.query(models.SessionToken).filter(models.SessionToken.token == token).first()
        if not sess:
            return
        sess.otp_valid = True
        self.db.commit()

    def is_otp_valid(self, token: str) -> bool:
        sess = self.db.query(models.SessionToken).filter(models.SessionToken.token == token).first()
        return bool(sess and sess.otp_valid)

    def set_pending_login_op(self, token: str, op_id: str) -> None:
        sess = self.db.query(models.SessionToken).filter(models.SessionToken.token == token).first()
        if not sess:
            return
        sess.pending_login_op = op_id
        self.db.commit()

    def pop_pending_login_op(self, token: str) -> Optional[str]:
        sess = self.db.query(models.SessionToken).filter(models.SessionToken.token == token).first()
        if not sess:
            return None
        op = sess.pending_login_op
        sess.pending_login_op = None
        self.db.commit()
        return op


