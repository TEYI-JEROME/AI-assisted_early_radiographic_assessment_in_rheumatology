from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt

from app.core.config import settings


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(user_id: str, roles: list[str]) -> str:
    exp = now_utc() + timedelta(minutes=480)
    payload = {
        "iss": "rheumaassist-local",
        "sub": user_id,
        "roles": roles,
        "type": "access",
        "jti": str(uuid4()),
        "iat": int(now_utc().timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"], issuer="rheumaassist-local")