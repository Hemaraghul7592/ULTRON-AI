from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import get_settings


def _derive_key(password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    if salt is None:
        salt = hashlib.sha256(password.encode()).digest()[:16]
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt


def encrypt_value(plaintext: str) -> str:
    settings = get_settings()
    key, salt = _derive_key(settings.ENCRYPTION_KEY)
    f = Fernet(key)
    encrypted = f.encrypt(plaintext.encode())
    return base64.urlsafe_b64encode(salt + encrypted).decode()


def decrypt_value(ciphertext: str) -> str:
    settings = get_settings()
    raw = base64.urlsafe_b64decode(ciphertext.encode())
    salt = raw[:16]
    token = raw[16:]
    key, _ = _derive_key(settings.ENCRYPTION_KEY, salt)
    f = Fernet(key)
    return f.decrypt(token).decode()
