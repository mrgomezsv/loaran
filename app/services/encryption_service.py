"""
Encryption service implementing envelope encryption using AES-GCM.
"""
from __future__ import annotations

import base64
import secrets
from typing import Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.core.config import settings


class EncryptionService:
    """Provides envelope encryption helpers using a master key from settings."""

    NONCE_SIZE_BYTES = 12  # Recommended size for AES-GCM
    DATA_KEY_SIZE_BYTES = 32  # AES-256

    @staticmethod
    def _get_master_key() -> bytes:
        if not settings.MASTER_KEY_B64:
            raise ValueError("MASTER_KEY_B64 not configured")
        try:
            master_key = base64.b64decode(settings.MASTER_KEY_B64)
        except Exception as exc:
            raise ValueError("MASTER_KEY_B64 is not valid base64") from exc
        if len(master_key) != 32:
            raise ValueError("MASTER_KEY_B64 must decode to 32 bytes (AES-256)")
        return master_key

    @classmethod
    def encrypt_bytes(cls, plaintext: bytes) -> Tuple[bytes, bytes, str]:
        """Encrypts bytes using a fresh data key wrapped by the master key.

        Returns (encrypted_data, wrapped_data_key, algo_tag)
        """
        data_key = secrets.token_bytes(cls.DATA_KEY_SIZE_BYTES)

        # Encrypt data
        data_nonce = secrets.token_bytes(cls.NONCE_SIZE_BYTES)
        data_aesgcm = AESGCM(data_key)
        ciphertext = data_aesgcm.encrypt(data_nonce, plaintext, None)
        encrypted_data = data_nonce + ciphertext

        # Wrap data key with master key
        master_key = cls._get_master_key()
        wrap_nonce = secrets.token_bytes(cls.NONCE_SIZE_BYTES)
        wrap_aesgcm = AESGCM(master_key)
        wrapped = wrap_aesgcm.encrypt(wrap_nonce, data_key, None)
        wrapped_key = wrap_nonce + wrapped

        return encrypted_data, wrapped_key, "AES-256-GCM"

    @classmethod
    def decrypt_bytes(cls, encrypted_data: bytes, wrapped_data_key: bytes) -> bytes:
        """Decrypts bytes using the wrapped data key and master key."""
        master_key = cls._get_master_key()

        # Unwrap data key
        wrap_nonce, wrap_ct = wrapped_data_key[: cls.NONCE_SIZE_BYTES], wrapped_data_key[cls.NONCE_SIZE_BYTES :]
        wrap_aesgcm = AESGCM(master_key)
        data_key = wrap_aesgcm.decrypt(wrap_nonce, wrap_ct, None)

        # Decrypt data
        data_nonce, ct = encrypted_data[: cls.NONCE_SIZE_BYTES], encrypted_data[cls.NONCE_SIZE_BYTES :]
        data_aesgcm = AESGCM(data_key)
        return data_aesgcm.decrypt(data_nonce, ct, None)


