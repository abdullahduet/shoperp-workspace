"""Pydantic schemas for the auth module."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1)
    role: Literal["admin", "manager", "staff"]


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class UserResponse(BaseModel):
    """Serialised user returned to API callers.  NEVER includes password_hash."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    name: str
    role: str
    is_active: bool
    last_login_at: Optional[datetime] = None
    created_at: datetime

    # Map camelCase Prisma field names → snake_case schema names
    @classmethod
    def model_validate(cls, obj, *, strict=None, from_attributes=None, context=None, experimental_allow_partial=None):  # type: ignore[override]
        # Prisma model uses camelCase attributes; translate before validation.
        if hasattr(obj, "__dict__") and not isinstance(obj, dict):
            data = {
                "id": obj.id,
                "email": obj.email,
                "name": obj.name,
                "role": obj.role,
                "is_active": obj.isActive,
                "last_login_at": obj.lastLoginAt,
                "created_at": obj.createdAt,
            }
            return cls(**data)
        return super().model_validate(
            obj,
            strict=strict,
            from_attributes=from_attributes,
            context=context,
        )
