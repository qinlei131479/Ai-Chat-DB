"""统一鉴权：JWT 与 API Token"""

import hashlib
import logging
import os
import secrets
from datetime import datetime

import jwt

from model.db_connection_pool import get_db_pool
from model.db_models import TApiToken, TUser

logger = logging.getLogger(__name__)

API_TOKEN_PREFIX = "aix_"
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "550e8400-e29b-41d4-a716-446655440000")


def strip_bearer_token(token: str) -> str:
    if token and token.startswith("Bearer "):
        return token.split(" ", 1)[1].strip()
    return (token or "").strip()


def hash_api_token(plain_token: str) -> str:
    return hashlib.sha256(plain_token.encode()).hexdigest()


def generate_plain_api_token() -> str:
    return f"{API_TOKEN_PREFIX}{secrets.token_urlsafe(32)}"


def _decode_jwt_payload(token: str) -> dict:
    payload = jwt.decode(token, key=JWT_SECRET, algorithms=["HS256"])
    if "exp" in payload and datetime.utcfromtimestamp(payload["exp"]) < datetime.utcnow():
        raise jwt.ExpiredSignatureError("Token has expired")
    payload["auth_type"] = "jwt"
    return payload


def _resolve_api_token(token: str) -> dict | None:
    if not token.startswith(API_TOKEN_PREFIX):
        return None

    token_hash = hash_api_token(token)
    db_pool = get_db_pool()
    with db_pool.get_session() as session:
        record = (
            session.query(TApiToken)
            .filter(TApiToken.token_hash == token_hash, TApiToken.status == 1)
            .first()
        )
        if not record:
            return None

        user = session.query(TUser).filter(TUser.id == record.user_id).first()
        if not user:
            return None

        record.last_used_at = datetime.now()
        record.updated_at = datetime.now()
        session.commit()

        return {
            "id": str(user.id),
            "username": user.userName or "",
            "role": user.role or "user",
            "auth_type": "api_token",
            "token_id": record.id,
        }


def resolve_token(token: str) -> dict | None:
    """
    解析 Bearer token，返回统一 user_payload。
    JWT 与 API Token 均支持；失败返回 None。
    """
    token = strip_bearer_token(token)
    if not token:
        return None

    if token.startswith(API_TOKEN_PREFIX):
        return _resolve_api_token(token)

    try:
        return _decode_jwt_payload(token)
    except jwt.ExpiredSignatureError:
        logger.debug("JWT token expired")
        return None
    except jwt.InvalidTokenError:
        logger.debug("Invalid JWT token")
        return None
    except Exception as e:
        logger.warning("resolve_token error: %s", e)
        return None
