"""
Disk-based encrypted file storage using EncryptionService.
Stores for each original filename:
  - <name>.enc  -> encrypted data bytes
  - <name>.key  -> wrapped data key bytes
"""
from __future__ import annotations

import os
from typing import Dict, List

from app.services.encryption_service import EncryptionService


class DiskFileService:
    def __init__(self, base_path: str) -> None:
        self.base_path = base_path

    def ensure_base(self) -> None:
        os.makedirs(self.base_path, exist_ok=True)

    def _enc_path(self, name: str) -> str:
        return os.path.join(self.base_path, f"{name}.enc")

    def _key_path(self, name: str) -> str:
        return os.path.join(self.base_path, f"{name}.key")

    def list_files(self) -> Dict[str, object]:
        items: List[Dict[str, object]] = []
        total_size = 0
        if not os.path.isdir(self.base_path):
            return {"items": items, "total_size_bytes": 0}
        for entry in os.listdir(self.base_path):
            if entry.endswith(".enc"):
                name = entry[:-4]
                enc_path = self._enc_path(name)
                size = os.path.getsize(enc_path)
                total_size += size
                items.append({
                    "id": name,
                    "name": name,
                    "algo": "AES-256-GCM",
                    "size_bytes": size,
                })
        return {"items": items, "total_size_bytes": total_size}

    def save_and_encrypt(self, name: str, content: bytes) -> None:
        self.ensure_base()
        enc_data, wrapped_key, _algo = EncryptionService.encrypt_bytes(content)
        with open(self._enc_path(name), "wb") as f:
            f.write(enc_data)
        with open(self._key_path(name), "wb") as f:
            f.write(wrapped_key)

    def load_and_decrypt(self, name: str) -> bytes:
        enc_path = self._enc_path(name)
        key_path = self._key_path(name)
        if not (os.path.exists(enc_path) and os.path.exists(key_path)):
            raise FileNotFoundError("file parts not found")
        with open(enc_path, "rb") as f:
            enc_data = f.read()
        with open(key_path, "rb") as f:
            wrapped_key = f.read()
        return EncryptionService.decrypt_bytes(enc_data, wrapped_key)


