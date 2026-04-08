from __future__ import annotations
from jose import JWTError, jwt

import logging
from functools import lru_cache
from uuid import UUID

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import create_client

from app.config import settings

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer()


@lru_cache(maxsize=1)
def _get_jwks() -> dict:
    """Fetch Supabase JWKS once and cache for the process lifetime.

    Supabase now uses ES256 (asymmetric) by default, so we verify tokens
    using the public key from the JWKS endpoint instead of the shared secret.
    """
    resp = httpx.get(
        f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json",
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> dict:
    token = credentials.credentials
    try:
        jwks = _get_jwks()
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["ES256", "HS256"],
            audience="authenticated",
        )
        user_id = UUID(payload.get("sub"))
        email = payload.get("email")
        phone = payload.get("phone")
        return {"id": user_id, "email": email, "phone": phone}
    except (JWTError, ValueError, TypeError) as exc:
        logger.debug("JWT validation failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {e}",
        )


def get_current_user_id(current_user: dict = Depends(get_current_user)) -> UUID:
    return current_user["id"]