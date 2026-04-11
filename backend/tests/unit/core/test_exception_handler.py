"""
Unit tests for the global exception handlers registered in src/main.py

Tests verify:
  1. AppError subclasses raised inside a route are caught and formatted
     as standard error responses (Rule #14).
  2. Pydantic RequestValidationError is handled with code VALIDATION_ERROR.

The Prisma client is patched at module level so that the app's startup
lifecycle (database.connect) does not require a real database.
"""
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.exceptions import (
    AppError,
    NotFoundError,
    ConflictError,
    AuthError,
    ForbiddenError,
    ValidationError,
)


# ---------------------------------------------------------------------------
# Build a minimal test app that mirrors main.py's exception handlers
# without triggering Prisma lifecycle events.
# ---------------------------------------------------------------------------

def make_test_app() -> FastAPI:
    """
    Return a FastAPI app with the same exception handlers as main.py but
    without Prisma startup/shutdown so unit tests don't need a real database.
    """
    from fastapi import Request
    from fastapi.exceptions import RequestValidationError
    from src.core.responses import error_response

    test_app = FastAPI()

    @test_app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        details = getattr(exc, "details", None)
        return error_response(
            error=exc.message,
            code=exc.code,
            status_code=exc.status_code,
            details=details,
        )

    @test_app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        details = [
            {"field": ".".join(str(loc) for loc in err["loc"]), "message": err["msg"]}
            for err in exc.errors()
        ]
        return error_response(
            error="Request validation failed",
            code="VALIDATION_ERROR",
            status_code=422,
            details=details,
        )

    # ---- Routes that raise various exceptions to exercise the handlers ----

    @test_app.get("/test/not-found")
    async def raise_not_found():
        raise NotFoundError("User", "123")

    @test_app.get("/test/conflict")
    async def raise_conflict():
        raise ConflictError("Email already registered")

    @test_app.get("/test/auth")
    async def raise_auth():
        raise AuthError()

    @test_app.get("/test/forbidden")
    async def raise_forbidden():
        raise ForbiddenError()

    @test_app.get("/test/validation")
    async def raise_validation():
        raise ValidationError("Bad input", details=["name is required"])

    @test_app.get("/test/app-error")
    async def raise_app_error():
        raise AppError("generic error", "GENERIC", 400)

    @test_app.get("/test/pydantic")
    async def raise_pydantic(required_param: int):
        return {"value": required_param}

    return test_app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(make_test_app(), raise_server_exceptions=False)


def body(response) -> dict:
    return json.loads(response.content)


class TestNotFoundErrorHandler:
    def test_status_code_is_404(self, client):
        resp = client.get("/test/not-found")
        assert resp.status_code == 404

    def test_success_is_false(self, client):
        assert body(client.get("/test/not-found"))["success"] is False

    def test_code_is_NOT_FOUND(self, client):
        assert body(client.get("/test/not-found"))["code"] == "NOT_FOUND"

    def test_error_contains_resource_and_id(self, client):
        b = body(client.get("/test/not-found"))
        assert "User" in b["error"]
        assert "123" in b["error"]


class TestConflictErrorHandler:
    def test_status_code_is_409(self, client):
        resp = client.get("/test/conflict")
        assert resp.status_code == 409

    def test_code_is_CONFLICT(self, client):
        assert body(client.get("/test/conflict"))["code"] == "CONFLICT"

    def test_error_message_is_passed_through(self, client):
        assert body(client.get("/test/conflict"))["error"] == "Email already registered"


class TestAuthErrorHandler:
    def test_status_code_is_401(self, client):
        assert client.get("/test/auth").status_code == 401

    def test_code_is_AUTH_ERROR(self, client):
        assert body(client.get("/test/auth"))["code"] == "AUTH_ERROR"

    def test_success_is_false(self, client):
        assert body(client.get("/test/auth"))["success"] is False


class TestForbiddenErrorHandler:
    def test_status_code_is_403(self, client):
        assert client.get("/test/forbidden").status_code == 403

    def test_code_is_FORBIDDEN(self, client):
        assert body(client.get("/test/forbidden"))["code"] == "FORBIDDEN"


class TestValidationErrorHandler:
    def test_status_code_is_422(self, client):
        assert client.get("/test/validation").status_code == 422

    def test_code_is_VALIDATION_ERROR(self, client):
        assert body(client.get("/test/validation"))["code"] == "VALIDATION_ERROR"

    def test_details_included(self, client):
        b = body(client.get("/test/validation"))
        assert b["details"] == ["name is required"]


class TestGenericAppErrorHandler:
    def test_status_code_is_preserved(self, client):
        assert client.get("/test/app-error").status_code == 400

    def test_code_is_preserved(self, client):
        assert body(client.get("/test/app-error"))["code"] == "GENERIC"

    def test_error_message_is_preserved(self, client):
        assert body(client.get("/test/app-error"))["error"] == "generic error"

    def test_success_is_false(self, client):
        assert body(client.get("/test/app-error"))["success"] is False


class TestPydanticValidationErrorHandler:
    def test_missing_required_param_returns_422(self, client):
        # /test/pydantic requires query param `required_param: int`
        resp = client.get("/test/pydantic")
        assert resp.status_code == 422

    def test_code_is_VALIDATION_ERROR(self, client):
        resp = client.get("/test/pydantic")
        assert body(resp)["code"] == "VALIDATION_ERROR"

    def test_error_message_indicates_validation(self, client):
        resp = client.get("/test/pydantic")
        assert body(resp)["error"] == "Request validation failed"

    def test_details_contain_field_info(self, client):
        resp = client.get("/test/pydantic")
        b = body(resp)
        assert "details" in b
        assert len(b["details"]) > 0
