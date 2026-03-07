"""Simple symmetric encryption for secrets stored in the database."""

from __future__ import annotations

import base64
import hashlib
import os
from cryptography.fernet import Fernet, InvalidToken

from config import settings

# Derive a Fernet key from SENTINEL_SECRET (must be 32 url-safe base64 bytes)
_raw = (settings.SENTINEL_SECRET or "default-sentinel-key").encode()
_key = base64.urlsafe_b64encode(hashlib.sha256(_raw).digest())
_fernet = Fernet(_key)


def encrypt(plaintext: str) -> str:
    """Encrypt a plaintext string. Returns base64-encoded ciphertext."""
    if not plaintext:
        return ""
    return _fernet.encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt a ciphertext string. Returns plaintext."""
    if not ciphertext:
        return ""
    try:
        return _fernet.decrypt(ciphertext.encode()).decode()
    except (InvalidToken, Exception):
        # If decryption fails, assume it's stored as plaintext (pre-encryption migration)
        return ciphertext


def mask(value: str, visible_chars: int = 4) -> str:
    """Mask a secret, showing only the last N characters."""
    if not value or len(value) <= visible_chars:
        return "****"
    return "*" * 8 + value[-visible_chars:]
