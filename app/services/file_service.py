"""
In-memory encrypted file store using EncryptionService for demo purposes.
"""
from __future__ import annotations

from typing import Dict, List
import base64

from app.services.encryption_service import EncryptionService


class FileService:
    def __init__(self) -> None:
        # Prepare a few demo files encrypted at startup
        self._store: Dict[str, Dict[str, bytes | str]] = {}
        self._add_demo("reporte-1.txt", b"Reporte 1: Sensor tanque OK.")
        self._add_demo("reporte-2.txt", b"Reporte 2: Movimiento nocturno detectado.")
        self._add_demo("credenciales.txt", b"Acceso interno: solo para demostracion.")

    def _add_demo(self, name: str, content: bytes) -> None:
        enc_data, wrapped_key, algo = EncryptionService.encrypt_bytes(content)
        file_id = base64.urlsafe_b64encode(name.encode("utf-8")).decode("utf-8").rstrip("=")
        self._store[file_id] = {
            "id": file_id,
            "name": name,
            "algo": algo,
            "enc_data": enc_data,
            "wrapped_key": wrapped_key,
        }

    def list_files(self) -> List[Dict[str, str]]:
        return [
            {"id": meta["id"], "name": meta["name"], "algo": meta["algo"]}
            for meta in self._store.values()
        ]

    def get_file_plain(self, file_id: str) -> bytes:
        meta = self._store.get(file_id)
        if not meta:
            raise FileNotFoundError("file not found")
        return EncryptionService.decrypt_bytes(meta["enc_data"], meta["wrapped_key"])  # type: ignore[arg-type]


