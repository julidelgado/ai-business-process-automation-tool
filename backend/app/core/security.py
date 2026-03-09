import base64
import hashlib

from cryptography.fernet import Fernet

from app.core.config import get_settings


def _fernet() -> Fernet:
    key_material = get_settings().secret_key.encode("utf-8")
    derived = hashlib.sha256(key_material).digest()
    fernet_key = base64.urlsafe_b64encode(derived)
    return Fernet(fernet_key)


def encrypt_payload(payload: str) -> str:
    return _fernet().encrypt(payload.encode("utf-8")).decode("utf-8")


def decrypt_payload(payload: str) -> str:
    return _fernet().decrypt(payload.encode("utf-8")).decode("utf-8")
