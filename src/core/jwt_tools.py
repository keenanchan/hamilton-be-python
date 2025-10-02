import time, jwt
from typing import Optional
from src.core.config import config


def issue_access_token(sub: int, email: str, roles: list[str], perms: list[str]) -> str:
    now = int(time.time())
    payload = {
        "sub": sub,
        "email": email,
        "roles": roles,
        "perms": perms,
        "iat": now,
        "exp": now + config.ACCESS_TOKEN_EXPIRES_MIN * 60,
    }
    token = jwt.encode(payload, config.SECRET_KEY, algorithm="HS256")
    return token


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.PyJWTError:
        return None