"""
Integration tests for GET /api/health

The Prisma client is mocked at the module level so tests run without a live
database and without `prisma generate` having been run.

Two scenarios are tested:
  1. DB reachable: expects 200 with {success: true, data: {status: "ok", db: "connected"}}
  2. DB unreachable: expects 503 with {success: false, code: "DB_ERROR"}
"""
import json
import sys
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Inject a fake `prisma` package BEFORE any src.* imports so that
# `from prisma import Prisma` in src/database.py succeeds without
# `prisma generate` having been run.
# ---------------------------------------------------------------------------

def _install_prisma_stub():
    """Insert a minimal prisma stub into sys.modules if needed."""
    if "prisma" in sys.modules and not isinstance(sys.modules["prisma"], ModuleType):
        return  # already a real module (e.g. generated client present)

    if "prisma" not in sys.modules or getattr(sys.modules["prisma"], "_is_stub", False):
        stub = ModuleType("prisma")
        stub._is_stub = True

        class FakePrisma:
            """Stub that will be replaced per-test via patch."""
            pass

        stub.Prisma = FakePrisma
        sys.modules["prisma"] = stub


_install_prisma_stub()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def body(response) -> dict:
    return json.loads(response.content)


# ---------------------------------------------------------------------------
# Build fixtures using patches that avoid real DB I/O
# ---------------------------------------------------------------------------

@pytest.fixture
def connected_db_client():
    """Mock Prisma client whose execute_raw succeeds."""
    mock = MagicMock()
    mock.execute_raw = AsyncMock(return_value=None)
    return mock


@pytest.fixture
def disconnected_db_client():
    """Mock Prisma client whose execute_raw raises."""
    mock = MagicMock()
    mock.execute_raw = AsyncMock(side_effect=RuntimeError("connection refused"))
    return mock


def _make_test_client(db_mock):
    """
    Build a FastAPI TestClient with the health router and all Prisma calls
    patched out.  Importing src.main is deferred inside the patch context
    to avoid import-time Prisma errors.
    """
    from fastapi.testclient import TestClient

    # Patch database._db so get_client() returns our mock
    # Patch connect/disconnect so the lifespan does nothing
    with patch("src.database._db", db_mock), \
         patch("src.database.connect", new_callable=AsyncMock), \
         patch("src.database.disconnect", new_callable=AsyncMock):
        # src.main may already be imported; that's fine — the patches
        # above affect the module-level _db reference at call time.
        import src.main as main_module

        # Force the lifespan not to call real connect by patching at module level
        client = TestClient(main_module.app, raise_server_exceptions=False)
        # We need the patches active during the actual HTTP call too,
        # so we return a callable that creates the client inside the patches.
        return client


@pytest.fixture
def app_connected(connected_db_client):
    """TestClient wired to a working mock DB."""
    with patch("src.database._db", connected_db_client), \
         patch("src.database.connect", new_callable=AsyncMock), \
         patch("src.database.disconnect", new_callable=AsyncMock):
        from fastapi.testclient import TestClient
        import src.main as main_module
        yield TestClient(main_module.app, raise_server_exceptions=False)


@pytest.fixture
def app_disconnected(disconnected_db_client):
    """TestClient wired to an unreachable mock DB."""
    with patch("src.database._db", disconnected_db_client), \
         patch("src.database.connect", new_callable=AsyncMock), \
         patch("src.database.disconnect", new_callable=AsyncMock):
        from fastapi.testclient import TestClient
        import src.main as main_module
        yield TestClient(main_module.app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# Tests: DB connected
# ---------------------------------------------------------------------------

class TestHealthEndpointConnected:
    def test_status_code_is_200(self, app_connected):
        resp = app_connected.get("/api/health")
        assert resp.status_code == 200

    def test_success_is_true(self, app_connected):
        b = body(app_connected.get("/api/health"))
        assert b["success"] is True

    def test_data_status_is_ok(self, app_connected):
        b = body(app_connected.get("/api/health"))
        assert b["data"]["status"] == "ok"

    def test_data_db_is_connected(self, app_connected):
        b = body(app_connected.get("/api/health"))
        assert b["data"]["db"] == "connected"

    def test_response_shape_matches_contract(self, app_connected):
        """
        API contract (acceptance criterion exit signal):
        {"success": true, "data": {"status": "ok", "db": "connected"}}
        The success_response wrapper also includes a "message" key.
        """
        b = body(app_connected.get("/api/health"))
        assert b["success"] is True
        assert b["data"] == {"status": "ok", "db": "connected"}
        assert "message" in b  # success_response always includes message

    def test_content_type_is_json(self, app_connected):
        resp = app_connected.get("/api/health")
        assert "application/json" in resp.headers.get("content-type", "")

    def test_no_auth_required(self, app_connected):
        """Health check must be accessible without an Authorization header."""
        resp = app_connected.get("/api/health")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Tests: DB unreachable
# ---------------------------------------------------------------------------

class TestHealthEndpointDisconnected:
    def test_status_code_is_503(self, app_disconnected):
        resp = app_disconnected.get("/api/health")
        assert resp.status_code == 503

    def test_success_is_false(self, app_disconnected):
        b = body(app_disconnected.get("/api/health"))
        assert b["success"] is False

    def test_code_is_DB_ERROR(self, app_disconnected):
        b = body(app_disconnected.get("/api/health"))
        assert b["code"] == "DB_ERROR"

    def test_error_field_present(self, app_disconnected):
        b = body(app_disconnected.get("/api/health"))
        assert "error" in b

    def test_no_data_field_on_error(self, app_disconnected):
        b = body(app_disconnected.get("/api/health"))
        assert "data" not in b
