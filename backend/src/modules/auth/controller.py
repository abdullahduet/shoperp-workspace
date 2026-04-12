"""Auth controller — thin layer: validate input, call service, set/clear cookies."""
from __future__ import annotations

from fastapi import Depends, Response
from fastapi.responses import JSONResponse
from prisma.models import User

from src.core.auth import get_current_user
from src.core.responses import success_response
from src.database import get_db
from src.modules.auth.repository import AuthRepository
from src.modules.auth.schemas import (
    LoginRequest,
    PasswordChangeRequest,
    RegisterRequest,
    UserResponse,
)
from src.modules.auth.service import AuthService


def _get_service(db=Depends(get_db)) -> AuthService:
    return AuthService(AuthRepository(db))


async def login(
    body: LoginRequest,
    service: AuthService = Depends(_get_service),
) -> JSONResponse:
    result = await service.login(body.email, body.password)
    resp = success_response(
        data=result.user.model_dump(mode="json"),
        message="Login successful",
    )
    resp.set_cookie(
        key="access_token",
        value=result.token,
        httponly=True,
        max_age=604800,
        samesite="lax",
        secure=False,
    )
    return resp


async def register(
    body: RegisterRequest,
    service: AuthService = Depends(_get_service),
) -> JSONResponse:
    user = await service.register(
        email=body.email,
        password=body.password,
        name=body.name,
        role=body.role,
    )
    return success_response(
        data=user.model_dump(mode="json"),
        message="User created",
        status_code=201,
    )


async def logout(response: Response) -> JSONResponse:
    resp = success_response(data=None, message="Logged out")
    resp.delete_cookie(key="access_token", httponly=True, samesite="lax")
    return resp


async def me(
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    return success_response(
        data=UserResponse.model_validate(current_user).model_dump(mode="json")
    )


async def change_password(
    body: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(_get_service),
) -> JSONResponse:
    await service.change_password(
        user=current_user,
        current_password=body.current_password,
        new_password=body.new_password,
    )
    return success_response(data=None, message="Password updated")
