"""
Core authentication utilities: JWT creation/decoding, password hashing,
FastAPI dependency for current user extraction, and role guard factory.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import Cookie, Depends
from jose import JWTError, jwt
from passlib.context import CryptContext
from prisma.models import User

from src.config import settings
from src.core.exceptions import AuthError, ForbiddenError
from src.database import get_db

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Return bcrypt hash of *password* (12 rounds)."""
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches *hashed*."""
    return _pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_access_token(data: dict[str, Any]) -> str:
    """Create a signed JWT containing *data* plus an expiry claim."""
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.JWT_EXPIRE_DAYS)
    payload["exp"] = expire
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT.  Raises AuthError on failure."""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
    except JWTError:
        raise AuthError("Authentication required")


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------

async def get_current_user(
    access_token: Optional[str] = Cookie(default=None),
    db=Depends(get_db),
) -> User:
    """FastAPI dependency: read cookie → decode JWT → fetch user from DB.

    Raises AuthError if the cookie is missing, the token is invalid/expired,
    or the user does not exist / is inactive / is soft-deleted.
    """
    if access_token is None:
        raise AuthError("Authentication required")

    payload = decode_token(access_token)

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise AuthError("Authentication required")

    user: User | None = await db.user.find_first(
        where={"id": user_id, "deletedAt": None, "isActive": True}
    )
    if user is None:
        raise AuthError("Authentication required")

    return user


def require_roles(*roles: str):
    """Factory that returns a FastAPI dependency enforcing *roles*.

    Usage::

        @router.post("/register", dependencies=[Depends(require_roles("admin"))])
    """

    async def _check_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise ForbiddenError("Insufficient permissions")
        return current_user

    return _check_role
