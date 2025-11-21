from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import hashlib
import hmac
import base64
import json
import os

# Minimal JWT-like token using HS256 (python-only, no external deps)
# NOTE: For production, use PyJWT. This is a compact educational helper.

SECRET_KEY = os.getenv("JWT_SECRET", "dev-secret")
ALGO = "HS256"

def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def _b64urldecode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

def _sign(message: bytes, secret: str) -> str:
    sig = hmac.new(secret.encode(), message, hashlib.sha256).digest()
    return _b64url(sig)

def create_access_token(sub: str, role: str, expires_minutes: int = 60) -> str:
    header = {"alg": ALGO, "typ": "JWT"}
    payload = {
        "sub": sub,
        "role": role,
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)).timestamp())
    }
    h = _b64url(json.dumps(header, separators=(",", ":")).encode())
    p = _b64url(json.dumps(payload, separators=(",", ":")).encode())
    msg = f"{h}.{p}".encode()
    s = _sign(msg, SECRET_KEY)
    return f"{h}.{p}.{s}"

class TokenError(Exception): ...
class TokenExpired(TokenError): ...
class TokenInvalid(TokenError): ...

def verify_token(token: str) -> Dict[str, Any]:
    try:
        h, p, s = token.split(".")
        msg = f"{h}.{p}".encode()
        expected = _sign(msg, SECRET_KEY)
        if not hmac.compare_digest(s, expected):
            raise TokenInvalid("Invalid signature")
        payload = json.loads(_b64urldecode(p))
        if "exp" in payload and int(payload["exp"]) < int(datetime.now(timezone.utc).timestamp()):
            raise TokenExpired("Token expired")
        return payload
    except ValueError:
        raise TokenInvalid("Malformed token")
