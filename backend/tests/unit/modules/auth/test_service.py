"""
Unit tests for src/modules/auth/service.py

All Prisma/repository calls are mocked. Tests verify business logic only.
bcrypt rounds are kept at the default (passlib chooses based on context);
we mock verify_password and hash_password where timing matters.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.core.exceptions import AuthError, ConflictError
from src.modules.auth.repository import AuthRepository
from src.modules.auth.schemas import UserResponse
from src.modules.auth.service import AuthService, LoginResult


def _make_fake_user(
    *,
    user_id: str = "user-uuid",
    email: str = "test@example.com",
    name: str = "Test User",
    role: str = "staff",
    password_hash: str = "$2b$12$fakehash",
    is_active: bool = True,
    created_at: datetime | None = None,
    last_login_at: datetime | None = None,
) -> MagicMock:
    user = MagicMock()
    user.id = user_id
    user.email = email
    user.name = name
    user.role = role
    user.passwordHash = password_hash
    user.isActive = is_active
    user.createdAt = created_at or datetime(2024, 1, 1, tzinfo=timezone.utc)
    user.lastLoginAt = last_login_at
    user.deletedAt = None
    return user


def _make_service() -> tuple[AuthService, AsyncMock]:
    repo = AsyncMock(spec=AuthRepository)
    service = AuthService(repo)
    return service, repo


# ---------------------------------------------------------------------------
# login
# ---------------------------------------------------------------------------

class TestLogin:
    @pytest.mark.asyncio
    async def test_successful_login_returns_login_result(self):
        service, repo = _make_service()
        fake_user = _make_fake_user(role="admin")
        repo.find_by_email.return_value = fake_user
        repo.update_last_login.return_value = None

        with patch("src.modules.auth.service.verify_password", return_value=True):
            result = await service.login("admin@example.com", "password123")

        assert isinstance(result, LoginResult)
        assert isinstance(result.user, UserResponse)
        assert isinstance(result.token, str)
        assert len(result.token) > 0

    @pytest.mark.asyncio
    async def test_login_calls_update_last_login(self):
        service, repo = _make_service()
        fake_user = _make_fake_user()
        repo.find_by_email.return_value = fake_user
        repo.update_last_login.return_value = None

        with patch("src.modules.auth.service.verify_password", return_value=True):
            await service.login("test@example.com", "password123")

        repo.update_last_login.assert_awaited_once_with(fake_user.id)

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_user_not_found(self):
        service, repo = _make_service()
        repo.find_by_email.return_value = None

        with pytest.raises(AuthError) as exc_info:
            await service.login("nobody@example.com", "password")

        assert exc_info.value.message == "Invalid email or password"

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_password_wrong(self):
        service, repo = _make_service()
        fake_user = _make_fake_user()
        repo.find_by_email.return_value = fake_user

        with patch("src.modules.auth.service.verify_password", return_value=False):
            with pytest.raises(AuthError) as exc_info:
                await service.login("test@example.com", "wrongpassword")

        assert exc_info.value.message == "Invalid email or password"

    @pytest.mark.asyncio
    async def test_returned_user_response_has_no_password_field(self):
        service, repo = _make_service()
        fake_user = _make_fake_user(role="manager")
        repo.find_by_email.return_value = fake_user
        repo.update_last_login.return_value = None

        with patch("src.modules.auth.service.verify_password", return_value=True):
            result = await service.login("test@example.com", "password")

        user_dict = result.user.model_dump()
        assert "password_hash" not in user_dict
        assert "passwordHash" not in user_dict

    @pytest.mark.asyncio
    async def test_token_encodes_user_id_and_role(self):
        from jose import jwt
        from src.config import settings

        service, repo = _make_service()
        fake_user = _make_fake_user(user_id="abc-123", role="admin")
        repo.find_by_email.return_value = fake_user
        repo.update_last_login.return_value = None

        with patch("src.modules.auth.service.verify_password", return_value=True):
            result = await service.login("admin@example.com", "pass")

        payload = jwt.decode(result.token, settings.JWT_SECRET, algorithms=["HS256"])
        assert payload["sub"] == "abc-123"
        assert payload["role"] == "admin"


# ---------------------------------------------------------------------------
# register
# ---------------------------------------------------------------------------

class TestRegister:
    @pytest.mark.asyncio
    async def test_successful_registration_returns_user_response(self):
        service, repo = _make_service()
        repo.email_exists.return_value = False
        fake_user = _make_fake_user(email="new@example.com", role="staff")
        repo.create.return_value = fake_user

        with patch("src.modules.auth.service.hash_password", return_value="$2b$12$hashed"):
            result = await service.register(
                email="new@example.com",
                password="password123",
                name="New User",
                role="staff",
            )

        assert isinstance(result, UserResponse)
        assert result.email == "new@example.com"

    @pytest.mark.asyncio
    async def test_raises_conflict_when_email_already_exists(self):
        service, repo = _make_service()
        repo.email_exists.return_value = True

        with pytest.raises(ConflictError) as exc_info:
            await service.register(
                email="existing@example.com",
                password="password123",
                name="User",
                role="staff",
            )

        assert "already registered" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_password_is_hashed_before_storage(self):
        service, repo = _make_service()
        repo.email_exists.return_value = False
        fake_user = _make_fake_user()
        repo.create.return_value = fake_user

        with patch("src.modules.auth.service.hash_password", return_value="$2b$12$hashed") as mock_hash:
            await service.register(
                email="new@example.com",
                password="plaintext",
                name="User",
                role="staff",
            )

        mock_hash.assert_called_once_with("plaintext")
        call_kwargs = repo.create.call_args.kwargs
        assert call_kwargs["password_hash"] == "$2b$12$hashed"

    @pytest.mark.asyncio
    async def test_response_has_no_password_field(self):
        service, repo = _make_service()
        repo.email_exists.return_value = False
        repo.create.return_value = _make_fake_user()

        with patch("src.modules.auth.service.hash_password", return_value="$hash"):
            result = await service.register(
                email="x@example.com",
                password="password1",
                name="X",
                role="staff",
            )

        user_dict = result.model_dump()
        assert "password_hash" not in user_dict
        assert "passwordHash" not in user_dict

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_password_too_short(self):
        service, repo = _make_service()
        repo.email_exists.return_value = False

        with pytest.raises(AuthError):
            await service.register(
                email="x@example.com",
                password="short",
                name="X",
                role="staff",
            )


# ---------------------------------------------------------------------------
# change_password
# ---------------------------------------------------------------------------

class TestChangePassword:
    @pytest.mark.asyncio
    async def test_successful_password_change_calls_update(self):
        service, repo = _make_service()
        fake_user = _make_fake_user()
        repo.update_password.return_value = None

        with patch("src.modules.auth.service.verify_password", return_value=True):
            with patch("src.modules.auth.service.hash_password", return_value="$2b$new"):
                await service.change_password(
                    user=fake_user,
                    current_password="oldpassword",
                    new_password="newpassword123",
                )

        repo.update_password.assert_awaited_once_with(fake_user.id, "$2b$new")

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_current_password_wrong(self):
        service, repo = _make_service()
        fake_user = _make_fake_user()

        with patch("src.modules.auth.service.verify_password", return_value=False):
            with pytest.raises(AuthError) as exc_info:
                await service.change_password(
                    user=fake_user,
                    current_password="wrongpassword",
                    new_password="newpassword123",
                )

        assert exc_info.value.message == "Invalid email or password"

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_new_password_too_short(self):
        service, repo = _make_service()
        fake_user = _make_fake_user()

        with pytest.raises(AuthError):
            await service.change_password(
                user=fake_user,
                current_password="oldpassword",
                new_password="short",
            )

    @pytest.mark.asyncio
    async def test_does_not_call_update_when_current_password_wrong(self):
        service, repo = _make_service()
        fake_user = _make_fake_user()

        with patch("src.modules.auth.service.verify_password", return_value=False):
            with pytest.raises(AuthError):
                await service.change_password(
                    user=fake_user,
                    current_password="wrong",
                    new_password="newpassword123",
                )

        repo.update_password.assert_not_awaited()
