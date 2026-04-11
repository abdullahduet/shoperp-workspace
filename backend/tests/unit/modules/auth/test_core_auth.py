"""
Unit tests for src/core/auth.py

Tests JWT creation/decoding, password hashing/verification, and the
get_current_user + require_roles FastAPI dependencies (with mocked DB).
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from jose import jwt

from src.core.auth import (
    create_access_token,
    decode_token,
    hash_password,
    require_roles,
    verify_password,
)
from src.core.exceptions import AuthError, ForbiddenError
from src.config import settings


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

class TestHashPassword:
    def test_returns_string(self):
        h = hash_password("secret123")
        assert isinstance(h, str)

    def test_hash_is_not_plain_text(self):
        h = hash_password("secret123")
        assert h != "secret123"

    def test_different_calls_produce_different_hashes(self):
        # bcrypt salts each hash, so identical inputs differ
        h1 = hash_password("secret123")
        h2 = hash_password("secret123")
        assert h1 != h2

    def test_hash_starts_with_bcrypt_prefix(self):
        h = hash_password("secret123")
        assert h.startswith("$2b$") or h.startswith("$2a$")


class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        h = hash_password("mypassword")
        assert verify_password("mypassword", h) is True

    def test_wrong_password_returns_false(self):
        h = hash_password("mypassword")
        assert verify_password("wrongpassword", h) is False

    def test_empty_string_vs_hash_of_empty(self):
        h = hash_password("")
        assert verify_password("", h) is True

    def test_case_sensitive(self):
        h = hash_password("Password")
        assert verify_password("password", h) is False


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

class TestCreateAccessToken:
    def test_returns_string(self):
        token = create_access_token({"sub": "abc123", "role": "admin"})
        assert isinstance(token, str)

    def test_token_decodes_to_correct_payload(self):
        token = create_access_token({"sub": "abc123", "role": "admin"})
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        assert payload["sub"] == "abc123"
        assert payload["role"] == "admin"

    def test_token_contains_exp_claim(self):
        token = create_access_token({"sub": "abc123"})
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        assert "exp" in payload

    def test_exp_is_in_the_future(self):
        import time
        token = create_access_token({"sub": "abc123"})
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        assert payload["exp"] > time.time()


class TestDecodeToken:
    def test_decodes_valid_token(self):
        token = create_access_token({"sub": "user-id", "role": "staff"})
        payload = decode_token(token)
        assert payload["sub"] == "user-id"
        assert payload["role"] == "staff"

    def test_raises_auth_error_on_garbage_input(self):
        with pytest.raises(AuthError):
            decode_token("not.a.valid.token")

    def test_raises_auth_error_on_wrong_secret(self):
        bad_token = jwt.encode({"sub": "x"}, "wrong_secret", algorithm="HS256")
        with pytest.raises(AuthError):
            decode_token(bad_token)

    def test_raises_auth_error_on_expired_token(self):
        from jose import jwt as jose_jwt
        import time

        expired_payload = {"sub": "x", "exp": int(time.time()) - 10}
        expired_token = jose_jwt.encode(
            expired_payload, settings.JWT_SECRET, algorithm="HS256"
        )
        with pytest.raises(AuthError):
            decode_token(expired_token)


# ---------------------------------------------------------------------------
# get_current_user dependency
# ---------------------------------------------------------------------------

class TestGetCurrentUser:
    @pytest.mark.asyncio
    async def test_raises_auth_error_when_no_cookie(self):
        from src.core.auth import get_current_user

        mock_db = AsyncMock()
        with pytest.raises(AuthError):
            await get_current_user(access_token=None, db=mock_db)

    @pytest.mark.asyncio
    async def test_raises_auth_error_on_invalid_token(self):
        from src.core.auth import get_current_user

        mock_db = AsyncMock()
        with pytest.raises(AuthError):
            await get_current_user(access_token="bad_token", db=mock_db)

    @pytest.mark.asyncio
    async def test_raises_auth_error_when_user_not_found_in_db(self):
        from src.core.auth import get_current_user

        token = create_access_token({"sub": "nonexistent-id", "role": "admin"})
        mock_db = AsyncMock()
        mock_db.user.find_first = AsyncMock(return_value=None)

        with pytest.raises(AuthError):
            await get_current_user(access_token=token, db=mock_db)

    @pytest.mark.asyncio
    async def test_returns_user_when_token_valid_and_user_found(self):
        from src.core.auth import get_current_user

        fake_user = MagicMock()
        fake_user.id = "user-uuid"
        fake_user.role = "admin"

        token = create_access_token({"sub": "user-uuid", "role": "admin"})
        mock_db = AsyncMock()
        mock_db.user.find_first = AsyncMock(return_value=fake_user)

        result = await get_current_user(access_token=token, db=mock_db)
        assert result is fake_user

    @pytest.mark.asyncio
    async def test_queries_db_with_correct_user_id(self):
        from src.core.auth import get_current_user

        fake_user = MagicMock()
        fake_user.id = "specific-id"
        fake_user.role = "staff"

        token = create_access_token({"sub": "specific-id", "role": "staff"})
        mock_db = AsyncMock()
        mock_db.user.find_first = AsyncMock(return_value=fake_user)

        await get_current_user(access_token=token, db=mock_db)

        call_kwargs = mock_db.user.find_first.call_args.kwargs
        assert call_kwargs["where"]["id"] == "specific-id"


# ---------------------------------------------------------------------------
# require_roles dependency factory
# ---------------------------------------------------------------------------

class TestRequireRoles:
    @pytest.mark.asyncio
    async def test_allows_user_with_matching_role(self):
        admin_user = MagicMock()
        admin_user.role = "admin"

        guard = require_roles("admin", "manager")
        # Directly call the inner dependency with a mocked get_current_user
        with patch("src.core.auth.get_current_user", return_value=admin_user):
            result = await guard(current_user=admin_user)
        assert result is admin_user

    @pytest.mark.asyncio
    async def test_raises_forbidden_for_disallowed_role(self):
        staff_user = MagicMock()
        staff_user.role = "staff"

        guard = require_roles("admin")
        with pytest.raises(ForbiddenError):
            await guard(current_user=staff_user)

    @pytest.mark.asyncio
    async def test_allows_multiple_roles(self):
        manager_user = MagicMock()
        manager_user.role = "manager"

        guard = require_roles("admin", "manager")
        result = await guard(current_user=manager_user)
        assert result is manager_user
