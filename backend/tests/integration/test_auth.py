"""
Integration tests for auth endpoints:
  POST   /api/auth/login
  POST   /api/auth/register
  GET    /api/auth/me
  POST   /api/auth/logout
  PUT    /api/auth/me/password

Tests run against the FastAPI TestClient with the Prisma DB layer mocked.
No live database is required.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from src.core.auth import create_access_token, hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def body(response) -> dict:
    return json.loads(response.content)


def _make_user(
    *,
    user_id: str = "550e8400-e29b-41d4-a716-446655440000",
    email: str = "admin@test.com",
    name: str = "Admin User",
    role: str = "admin",
    password: str = "password123",
    is_active: bool = True,
    last_login_at: datetime | None = None,
) -> MagicMock:
    """Create a MagicMock that mimics a Prisma User model."""
    user = MagicMock()
    user.id = user_id
    user.email = email
    user.name = name
    user.role = role
    user.isActive = is_active
    user.passwordHash = hash_password(password)
    user.lastLoginAt = last_login_at
    user.createdAt = datetime(2024, 1, 1, tzinfo=timezone.utc)
    user.deletedAt = None
    return user


def _make_db(find_first_return=None) -> MagicMock:
    """Build a mock Prisma client with common method stubs."""
    db = MagicMock()
    db.user.find_first = AsyncMock(return_value=find_first_return)
    db.user.create = AsyncMock(return_value=find_first_return)
    db.user.update = AsyncMock(return_value=None)
    return db


def _make_client(mock_db: MagicMock) -> TestClient:
    """Return a FastAPI TestClient with the given mock DB injected."""
    with patch("src.database._db", mock_db), \
         patch("src.database.connect", new_callable=AsyncMock), \
         patch("src.database.disconnect", new_callable=AsyncMock):
        import src.main as main_module
        return TestClient(main_module.app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_user():
    return _make_user(role="admin")


@pytest.fixture
def staff_user():
    return _make_user(
        user_id="660e8400-e29b-41d4-a716-446655440000",
        email="staff@test.com",
        name="Staff User",
        role="staff",
    )


@pytest.fixture
def admin_token(admin_user):
    return create_access_token({"sub": admin_user.id, "role": "admin"})


@pytest.fixture
def staff_token(staff_user):
    return create_access_token({"sub": staff_user.id, "role": "staff"})


# ---------------------------------------------------------------------------
# POST /api/auth/login
# ---------------------------------------------------------------------------

class TestLogin:
    def test_valid_credentials_returns_200(self, admin_user):
        db = _make_db(find_first_return=admin_user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/auth/login",
                json={"email": admin_user.email, "password": "password123"},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert b["data"]["email"] == admin_user.email

    def test_valid_credentials_sets_httponly_cookie(self, admin_user):
        db = _make_db(find_first_return=admin_user)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.post(
                "/api/auth/login",
                json={"email": admin_user.email, "password": "password123"},
            )

        set_cookie = resp.headers.get("set-cookie", "")
        assert "access_token=" in set_cookie
        assert "HttpOnly" in set_cookie

    def test_response_contains_no_password_hash(self, admin_user):
        db = _make_db(find_first_return=admin_user)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.post(
                "/api/auth/login",
                json={"email": admin_user.email, "password": "password123"},
            )

        content = resp.content.decode()
        assert "password" not in content.lower() or "password123" not in content

    def test_response_user_data_fields(self, admin_user):
        db = _make_db(find_first_return=admin_user)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.post(
                "/api/auth/login",
                json={"email": admin_user.email, "password": "password123"},
            )

        b = body(resp)
        data = b["data"]
        for field in ("id", "email", "name", "role"):
            assert field in data, f"Missing field: {field}"
        assert "password_hash" not in data
        assert "passwordHash" not in data

    def test_invalid_email_returns_401_auth_error(self):
        db = _make_db(find_first_return=None)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.post(
                "/api/auth/login",
                json={"email": "nobody@test.com", "password": "password123"},
            )

        assert resp.status_code == 401
        assert body(resp)["code"] == "AUTH_ERROR"

    def test_wrong_password_returns_401_auth_error(self, admin_user):
        db = _make_db(find_first_return=admin_user)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.post(
                "/api/auth/login",
                json={"email": admin_user.email, "password": "wrongpassword"},
            )

        assert resp.status_code == 401
        assert body(resp)["code"] == "AUTH_ERROR"

    def test_inactive_user_returns_401(self):
        # Repository filters isActive=True, so inactive user returns None from find_by_email
        db = _make_db(find_first_return=None)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.post(
                "/api/auth/login",
                json={"email": "inactive@test.com", "password": "password123"},
            )

        assert resp.status_code == 401
        assert body(resp)["code"] == "AUTH_ERROR"

    def test_missing_password_field_returns_422(self):
        db = _make_db(find_first_return=None)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.post("/api/auth/login", json={"email": "admin@test.com"})

        assert resp.status_code == 422

    def test_missing_email_field_returns_422(self):
        db = _make_db(find_first_return=None)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.post("/api/auth/login", json={"password": "password123"})

        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/auth/register
# ---------------------------------------------------------------------------

class TestRegister:
    def _make_register_db(self, admin_user, new_user, email_exists: bool = False):
        """
        Build a mock DB that handles:
          - get_current_user: find_first by id → admin_user
          - require_roles: same (deduped by FastAPI)
          - email_exists: find_first by email without isActive → None or admin_user
          - create: returns new_user
        """
        async def find_first(where=None, **kwargs):
            if where and "id" in where:
                return admin_user
            # email_exists check: has email key, has deletedAt key, no isActive key
            if where and "email" in where and "deletedAt" in where and "isActive" not in where:
                return admin_user if email_exists else None
            return None

        db = MagicMock()
        db.user.find_first = AsyncMock(side_effect=find_first)
        db.user.create = AsyncMock(return_value=new_user)
        db.user.update = AsyncMock(return_value=None)
        return db

    def test_no_auth_cookie_returns_401(self):
        db = _make_db(find_first_return=None)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.post(
                "/api/auth/register",
                json={
                    "email": "new@test.com",
                    "password": "password123",
                    "name": "New User",
                    "role": "staff",
                },
            )

        assert resp.status_code == 401
        assert body(resp)["code"] == "AUTH_ERROR"

    def test_non_admin_role_returns_403(self, staff_user, staff_token):
        db = _make_db(find_first_return=staff_user)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.post(
                "/api/auth/register",
                json={
                    "email": "new@test.com",
                    "password": "password123",
                    "name": "New User",
                    "role": "staff",
                },
                cookies={"access_token": staff_token},
            )

        assert resp.status_code == 403
        assert body(resp)["code"] == "FORBIDDEN"

    def test_valid_admin_token_creates_user_returns_201(self, admin_user, admin_token):
        new_user = _make_user(
            user_id="660e8400-e29b-41d4-a716-446655440000",
            email="new@test.com",
            name="New User",
            role="staff",
        )
        db = self._make_register_db(admin_user, new_user, email_exists=False)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.post(
                "/api/auth/register",
                json={
                    "email": "new@test.com",
                    "password": "password123",
                    "name": "New User",
                    "role": "staff",
                },
                cookies={"access_token": admin_token},
            )

        assert resp.status_code == 201
        b = body(resp)
        assert b["success"] is True
        assert b["data"]["email"] == "new@test.com"

    def test_response_has_no_password_hash(self, admin_user, admin_token):
        new_user = _make_user(
            user_id="660e8400-e29b-41d4-a716-446655440000",
            email="new@test.com",
            name="New User",
            role="staff",
        )
        db = self._make_register_db(admin_user, new_user, email_exists=False)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.post(
                "/api/auth/register",
                json={
                    "email": "new@test.com",
                    "password": "password123",
                    "name": "New User",
                    "role": "staff",
                },
                cookies={"access_token": admin_token},
            )

        b = body(resp)
        assert "password_hash" not in b["data"]
        assert "passwordHash" not in b["data"]

    def test_response_user_response_shape(self, admin_user, admin_token):
        new_user = _make_user(
            user_id="660e8400-e29b-41d4-a716-446655440000",
            email="new@test.com",
            name="New User",
            role="staff",
        )
        db = self._make_register_db(admin_user, new_user, email_exists=False)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.post(
                "/api/auth/register",
                json={
                    "email": "new@test.com",
                    "password": "password123",
                    "name": "New User",
                    "role": "staff",
                },
                cookies={"access_token": admin_token},
            )

        data = body(resp)["data"]
        for field in ("id", "email", "name", "role", "is_active", "created_at"):
            assert field in data, f"Missing field: {field}"

    def test_duplicate_email_returns_409_conflict(self, admin_user, admin_token):
        db = self._make_register_db(admin_user, None, email_exists=True)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.post(
                "/api/auth/register",
                json={
                    "email": "existing@test.com",
                    "password": "password123",
                    "name": "User",
                    "role": "staff",
                },
                cookies={"access_token": admin_token},
            )

        assert resp.status_code == 409
        assert body(resp)["code"] == "CONFLICT"

    def test_invalid_role_value_returns_422(self, admin_user, admin_token):
        db = _make_db(find_first_return=admin_user)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.post(
                "/api/auth/register",
                json={
                    "email": "new@test.com",
                    "password": "password123",
                    "name": "User",
                    "role": "superuser",
                },
                cookies={"access_token": admin_token},
            )

        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/auth/me
# ---------------------------------------------------------------------------

class TestMe:
    def test_valid_cookie_returns_200_with_user_data(self, admin_user, admin_token):
        db = _make_db(find_first_return=admin_user)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.get("/api/auth/me", cookies={"access_token": admin_token})

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert b["data"]["email"] == admin_user.email

    def test_me_response_has_no_password_hash(self, admin_user, admin_token):
        db = _make_db(find_first_return=admin_user)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.get("/api/auth/me", cookies={"access_token": admin_token})

        data = body(resp)["data"]
        assert "password_hash" not in data
        assert "passwordHash" not in data

    def test_me_response_fields(self, admin_user, admin_token):
        db = _make_db(find_first_return=admin_user)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.get("/api/auth/me", cookies={"access_token": admin_token})

        data = body(resp)["data"]
        for field in ("id", "email", "name", "role", "is_active", "created_at"):
            assert field in data, f"Missing field: {field}"

    def test_no_cookie_returns_401(self):
        db = _make_db(find_first_return=None)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.get("/api/auth/me")

        assert resp.status_code == 401
        assert body(resp)["code"] == "AUTH_ERROR"

    def test_tampered_jwt_returns_401(self):
        db = _make_db(find_first_return=None)
        bad_token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyLWlkIn0.invalidsig"

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.get("/api/auth/me", cookies={"access_token": bad_token})

        assert resp.status_code == 401
        assert body(resp)["code"] == "AUTH_ERROR"

    def test_expired_jwt_returns_401(self):
        from src.config import settings

        db = _make_db(find_first_return=None)
        expired_payload = {
            "sub": "user-id",
            "role": "admin",
            "exp": int(time.time()) - 10,
        }
        expired_token = jwt.encode(
            expired_payload, settings.JWT_SECRET, algorithm="HS256"
        )

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.get("/api/auth/me", cookies={"access_token": expired_token})

        assert resp.status_code == 401
        assert body(resp)["code"] == "AUTH_ERROR"


# ---------------------------------------------------------------------------
# POST /api/auth/logout
# ---------------------------------------------------------------------------

class TestLogout:
    def test_valid_cookie_returns_200(self, admin_user, admin_token):
        db = _make_db(find_first_return=admin_user)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.post("/api/auth/logout", cookies={"access_token": admin_token})

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert b["message"] == "Logged out"

    def test_logout_clears_access_token_cookie(self, admin_user, admin_token):
        db = _make_db(find_first_return=admin_user)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.post("/api/auth/logout", cookies={"access_token": admin_token})

        set_cookie = resp.headers.get("set-cookie", "")
        # Cookie is cleared: either Max-Age=0 or value is empty
        assert "access_token" in set_cookie
        assert "Max-Age=0" in set_cookie or 'access_token=""' in set_cookie

    def test_logout_without_cookie_returns_401(self):
        db = _make_db(find_first_return=None)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.post("/api/auth/logout")

        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# PUT /api/auth/me/password
# ---------------------------------------------------------------------------

class TestChangePassword:
    def test_correct_current_password_returns_200(self, admin_user, admin_token):
        db = _make_db(find_first_return=admin_user)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.put(
                "/api/auth/me/password",
                json={
                    "current_password": "password123",
                    "new_password": "newpassword123",
                },
                cookies={"access_token": admin_token},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert b["message"] == "Password updated"

    def test_wrong_current_password_returns_401(self, admin_user, admin_token):
        db = _make_db(find_first_return=admin_user)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.put(
                "/api/auth/me/password",
                json={
                    "current_password": "wrongpassword",
                    "new_password": "newpassword123",
                },
                cookies={"access_token": admin_token},
            )

        assert resp.status_code == 401
        assert body(resp)["code"] == "AUTH_ERROR"

    def test_no_cookie_returns_401(self):
        db = _make_db(find_first_return=None)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.put(
                "/api/auth/me/password",
                json={
                    "current_password": "password123",
                    "new_password": "newpassword123",
                },
            )

        assert resp.status_code == 401

    def test_missing_fields_returns_422(self, admin_user, admin_token):
        db = _make_db(find_first_return=admin_user)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            import src.main as main_module
            client = TestClient(main_module.app, raise_server_exceptions=False)
            resp = client.put(
                "/api/auth/me/password",
                json={"current_password": "password123"},
                cookies={"access_token": admin_token},
            )

        assert resp.status_code == 422
