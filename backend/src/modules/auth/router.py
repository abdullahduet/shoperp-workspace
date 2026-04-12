"""Auth router — wires HTTP paths to controller functions."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from src.core.auth import get_current_user, require_roles
from src.modules.auth import controller

router = APIRouter(prefix="/auth", tags=["auth"])

# Public
router.add_api_route("/login", controller.login, methods=["POST"])

# Any authenticated user
router.add_api_route(
    "/logout",
    controller.logout,
    methods=["POST"],
    dependencies=[Depends(get_current_user)],
)
router.add_api_route("/me", controller.me, methods=["GET"])
router.add_api_route(
    "/me/password",
    controller.change_password,
    methods=["PUT"],
)

# Admin only
router.add_api_route(
    "/register",
    controller.register,
    methods=["POST"],
    status_code=201,
    dependencies=[Depends(require_roles("admin"))],
)
