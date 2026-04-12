from __future__ import annotations


class AppError(Exception):
    def __init__(self, message: str, code: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


class NotFoundError(AppError):
    def __init__(self, resource: str, identifier: str) -> None:
        super().__init__(f"{resource} not found: {identifier}", "NOT_FOUND", 404)


class ConflictError(AppError):
    def __init__(self, message: str) -> None:
        super().__init__(message, "CONFLICT", 409)


class AuthError(AppError):
    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(message, "AUTH_ERROR", 401)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message, "FORBIDDEN", 403)


class ValidationError(AppError):
    def __init__(self, message: str, details: list | None = None) -> None:
        super().__init__(message, "VALIDATION_ERROR", 422)
        self.details = details or []
