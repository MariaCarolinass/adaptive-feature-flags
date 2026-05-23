from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_jwt(*, secret: str, subject: str, expires_in_seconds: int) -> str:
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": subject, "iat": now, "exp": now + max(1, expires_in_seconds)}

    header_part = _b64url_encode(json.dumps(header, separators=(",", ":"), ensure_ascii=True).encode())
    payload_part = _b64url_encode(json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode())
    signing_input = f"{header_part}.{payload_part}".encode()
    signature = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    signature_part = _b64url_encode(signature)
    return f"{header_part}.{payload_part}.{signature_part}"


def verify_jwt(*, token: str, secret: str) -> dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid token format.")

    header_part, payload_part, signature_part = parts
    signing_input = f"{header_part}.{payload_part}".encode()
    expected = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    provided = _b64url_decode(signature_part)
    if not hmac.compare_digest(provided, expected):
        raise ValueError("Invalid token signature.")

    header = json.loads(_b64url_decode(header_part))
    if header.get("alg") != "HS256":
        raise ValueError("Unsupported token algorithm.")

    payload = json.loads(_b64url_decode(payload_part))
    exp = payload.get("exp")
    if not isinstance(exp, int):
        raise ValueError("Invalid token payload.")
    if int(time.time()) >= exp:
        raise ValueError("Token expired.")
    return payload
