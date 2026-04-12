# auth — Context

## Purpose
Handles all authentication and user-management concerns: login (JWT cookie), logout, current-user retrieval, user registration (admin only), and password change. The JWT is stored as an HTTP-only cookie (`access_token`, 7-day expiry, SameSite=lax).

## Key Files
- `router.py`     → Declares the five `/auth/*` routes and applies auth/role dependencies.
- `controller.py` → Thin layer: parses request bodies, calls the service, sets/clears cookies.
- `service.py`    → ALL business logic: credential verification, user creation, password change.
- `repository.py` → Prisma queries only: `find_by_email`, `find_by_id`, `email_exists`, `create`, `update_last_login`, `update_password`.
- `schemas.py`    → Pydantic models: `RegisterRequest`, `LoginRequest`, `PasswordChangeRequest`, `UserResponse` (never includes `password_hash`).

## Patterns
- Controller calls `service.*`, never touches the DB directly.
- Service raises typed errors from `src.core.exceptions` (`AuthError`, `ConflictError`, `ForbiddenError`).
- `UserResponse.model_validate(prisma_user)` translates camelCase Prisma fields to snake_case.
- `get_current_user` (in `src/core/auth.py`) is the reusable FastAPI dependency for all protected routes in ANY module.
- `require_roles(*roles)` (in `src/core/auth.py`) is the role guard factory used across the app.

## Last Updated
2026-04-11 — Task 0002: initial implementation
