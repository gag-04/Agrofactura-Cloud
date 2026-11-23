"""Security utilities: password hashing and JWT token management."""

import base64
import hashlib
import hmac
import json
import time
from typing import Any, Dict, Optional

from src.core.config import settings


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64decode(data: str) -> bytes:
    padding = "=" * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data + padding)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a salt$hash format using PBKDF2-HMAC-SHA256."""
    try:
        salt, expected_hash = hashed_password.split("$", 1)
        computed = hashlib.pbkdf2_hmac(
            "sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100_000
        ).hex()
        return hmac.compare_digest(computed, expected_hash)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hashes a password using PBKDF2-HMAC-SHA256 with a unique random salt."""
    salt = hashlib.sha256(str(time.time_ns()).encode("utf-8")).hexdigest()[:16]
    derived = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000
    ).hex()
    return f"{salt}${derived}"


def create_access_token(data: Dict[str, Any], expires_delta_seconds: Optional[int] = None) -> str:
    """Creates a signed JWT-compliant token."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = data.copy()

    exp = time.time() + (expires_delta_seconds or (settings.JWT_EXPIRATION_HOURS * 3600))
    payload["exp"] = int(exp)
    payload["iat"] = int(time.time())

    encoded_header = _b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    encoded_payload = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))

    signature_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    signature = hmac.new(
        settings.JWT_SECRET.encode("utf-8"), signature_input, hashlib.sha256
    ).digest()
    encoded_signature = _b64encode(signature)

    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and verifies a JWT-compliant token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        encoded_header, encoded_payload, encoded_signature = parts

        signature_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
        expected_sig = hmac.new(
            settings.JWT_SECRET.encode("utf-8"), signature_input, hashlib.sha256
        ).digest()
        actual_sig = _b64decode(encoded_signature)

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        payload = json.loads(_b64decode(encoded_payload).decode("utf-8"))
        if payload.get("exp", 0) < time.time():
            return None  # Token expired

        return payload
    except Exception:
        return None
