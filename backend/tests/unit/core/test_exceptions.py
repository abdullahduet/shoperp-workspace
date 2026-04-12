"""
Unit tests for src/core/exceptions.py

Verifies the complete typed exception hierarchy:
  - Correct message construction
  - Correct error codes
  - Correct HTTP status codes
  - Subclass relationships
"""
import pytest

from src.core.exceptions import (
    AppError,
    NotFoundError,
    ConflictError,
    AuthError,
    ForbiddenError,
    ValidationError,
)


class TestAppError:
    def test_attributes_are_stored(self):
        exc = AppError("something went wrong", "SOME_CODE", 400)
        assert str(exc) == "something went wrong"
        assert exc.message == "something went wrong"
        assert exc.code == "SOME_CODE"
        assert exc.status_code == 400

    def test_default_status_code_is_400(self):
        exc = AppError("msg", "CODE")
        assert exc.status_code == 400

    def test_is_exception_subclass(self):
        assert issubclass(AppError, Exception)

    def test_can_be_raised_and_caught(self):
        with pytest.raises(AppError) as exc_info:
            raise AppError("error", "CODE", 500)
        assert exc_info.value.status_code == 500


class TestNotFoundError:
    def test_message_contains_resource_and_identifier(self):
        exc = NotFoundError("User", "123")
        assert "User" in exc.message
        assert "123" in exc.message

    def test_code_is_NOT_FOUND(self):
        exc = NotFoundError("User", "123")
        assert exc.code == "NOT_FOUND"

    def test_status_code_is_404(self):
        exc = NotFoundError("User", "123")
        assert exc.status_code == 404

    def test_message_format(self):
        exc = NotFoundError("Product", "sku-001")
        assert exc.message == "Product not found: sku-001"

    def test_is_app_error_subclass(self):
        assert issubclass(NotFoundError, AppError)

    def test_can_be_caught_as_app_error(self):
        with pytest.raises(AppError):
            raise NotFoundError("Order", "999")


class TestConflictError:
    def test_message_is_passed_through(self):
        exc = ConflictError("Email already registered")
        assert exc.message == "Email already registered"

    def test_code_is_CONFLICT(self):
        exc = ConflictError("Email already registered")
        assert exc.code == "CONFLICT"

    def test_status_code_is_409(self):
        exc = ConflictError("Email already registered")
        assert exc.status_code == 409

    def test_is_app_error_subclass(self):
        assert issubclass(ConflictError, AppError)


class TestAuthError:
    def test_default_message(self):
        exc = AuthError()
        assert exc.message == "Authentication required"

    def test_custom_message(self):
        exc = AuthError("Token expired")
        assert exc.message == "Token expired"

    def test_code_is_AUTH_ERROR(self):
        exc = AuthError()
        assert exc.code == "AUTH_ERROR"

    def test_status_code_is_401(self):
        exc = AuthError()
        assert exc.status_code == 401

    def test_is_app_error_subclass(self):
        assert issubclass(AuthError, AppError)


class TestForbiddenError:
    def test_default_message(self):
        exc = ForbiddenError()
        assert exc.message == "Insufficient permissions"

    def test_custom_message(self):
        exc = ForbiddenError("Admin only")
        assert exc.message == "Admin only"

    def test_code_is_FORBIDDEN(self):
        exc = ForbiddenError()
        assert exc.code == "FORBIDDEN"

    def test_status_code_is_403(self):
        exc = ForbiddenError()
        assert exc.status_code == 403

    def test_is_app_error_subclass(self):
        assert issubclass(ForbiddenError, AppError)


class TestValidationError:
    def test_message_is_stored(self):
        exc = ValidationError("Bad input")
        assert exc.message == "Bad input"

    def test_code_is_VALIDATION_ERROR(self):
        exc = ValidationError("Bad input")
        assert exc.code == "VALIDATION_ERROR"

    def test_status_code_is_422(self):
        exc = ValidationError("Bad input")
        assert exc.status_code == 422

    def test_has_details_attribute(self):
        exc = ValidationError("Bad input", details=["field required"])
        assert hasattr(exc, "details")
        assert exc.details == ["field required"]

    def test_details_defaults_to_empty_list(self):
        exc = ValidationError("Bad input")
        assert exc.details == []

    def test_details_none_becomes_empty_list(self):
        exc = ValidationError("Bad input", details=None)
        assert exc.details == []

    def test_is_app_error_subclass(self):
        assert issubclass(ValidationError, AppError)

    def test_does_not_shadow_builtin_validation_error(self):
        # Our ValidationError must be catchable as AppError, not just as Exception
        with pytest.raises(AppError):
            raise ValidationError("validation failed")
