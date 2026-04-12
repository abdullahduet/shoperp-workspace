"""
Unit tests for src/modules/auth/schemas.py

Verifies Pydantic validation rules and that UserResponse never includes
password_hash in any form.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError as PydanticValidationError

from src.modules.auth.schemas import (
    LoginRequest,
    PasswordChangeRequest,
    RegisterRequest,
    UserResponse,
)


# ---------------------------------------------------------------------------
# RegisterRequest
# ---------------------------------------------------------------------------

class TestRegisterRequest:
    def test_valid_request_is_accepted(self):
        req = RegisterRequest(
            email="admin@example.com",
            password="secret123",
            name="Admin User",
            role="admin",
        )
        assert req.email == "admin@example.com"

    def test_invalid_email_raises(self):
        with pytest.raises(PydanticValidationError):
            RegisterRequest(
                email="not-an-email",
                password="secret123",
                name="Admin User",
                role="admin",
            )

    def test_invalid_role_raises(self):
        with pytest.raises(PydanticValidationError):
            RegisterRequest(
                email="admin@example.com",
                password="secret123",
                name="Admin User",
                role="superuser",
            )

    def test_all_valid_roles_accepted(self):
        for role in ("admin", "manager", "staff"):
            req = RegisterRequest(
                email="user@example.com",
                password="secret123",
                name="User",
                role=role,
            )
            assert req.role == role


# ---------------------------------------------------------------------------
# LoginRequest
# ---------------------------------------------------------------------------

class TestLoginRequest:
    def test_valid_request_is_accepted(self):
        req = LoginRequest(email="user@example.com", password="anypassword")
        assert req.email == "user@example.com"

    def test_invalid_email_raises(self):
        with pytest.raises(PydanticValidationError):
            LoginRequest(email="bad", password="password")


# ---------------------------------------------------------------------------
# PasswordChangeRequest
# ---------------------------------------------------------------------------

class TestPasswordChangeRequest:
    def test_valid_request_is_accepted(self):
        req = PasswordChangeRequest(
            current_password="oldpass", new_password="newpass123"
        )
        assert req.current_password == "oldpass"
        assert req.new_password == "newpass123"


# ---------------------------------------------------------------------------
# UserResponse
# ---------------------------------------------------------------------------

class TestUserResponse:
    def _make_prisma_user(self, **overrides) -> MagicMock:
        user = MagicMock()
        user.id = overrides.get("id", "user-uuid")
        user.email = overrides.get("email", "test@example.com")
        user.name = overrides.get("name", "Test User")
        user.role = overrides.get("role", "staff")
        user.isActive = overrides.get("isActive", True)
        user.lastLoginAt = overrides.get("lastLoginAt", None)
        user.createdAt = overrides.get(
            "createdAt", datetime(2024, 1, 1, tzinfo=timezone.utc)
        )
        user.passwordHash = "should-never-appear"
        return user

    def test_model_validate_maps_prisma_fields(self):
        prisma_user = self._make_prisma_user(email="x@x.com", role="admin")
        resp = UserResponse.model_validate(prisma_user)
        assert resp.email == "x@x.com"
        assert resp.role == "admin"

    def test_password_hash_not_in_model_dump(self):
        prisma_user = self._make_prisma_user()
        resp = UserResponse.model_validate(prisma_user)
        dumped = resp.model_dump()
        assert "password_hash" not in dumped
        assert "passwordHash" not in dumped

    def test_password_hash_not_in_json_output(self):
        prisma_user = self._make_prisma_user()
        resp = UserResponse.model_validate(prisma_user)
        json_str = resp.model_dump_json()
        assert "password" not in json_str.lower()

    def test_last_login_at_can_be_none(self):
        prisma_user = self._make_prisma_user(lastLoginAt=None)
        resp = UserResponse.model_validate(prisma_user)
        assert resp.last_login_at is None

    def test_last_login_at_can_be_datetime(self):
        dt = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        prisma_user = self._make_prisma_user(lastLoginAt=dt)
        resp = UserResponse.model_validate(prisma_user)
        assert resp.last_login_at == dt

    def test_all_required_fields_present(self):
        prisma_user = self._make_prisma_user()
        resp = UserResponse.model_validate(prisma_user)
        dumped = resp.model_dump()
        for field in ("id", "email", "name", "role", "is_active", "created_at"):
            assert field in dumped, f"Missing field: {field}"

    def test_is_active_mapped_correctly(self):
        prisma_user = self._make_prisma_user(isActive=False)
        resp = UserResponse.model_validate(prisma_user)
        assert resp.is_active is False
