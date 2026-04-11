"""Inventory router — wires HTTP paths to controller functions."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from src.core.auth import get_current_user, require_roles
from src.modules.inventory import controller

router = APIRouter(prefix="/inventory", tags=["inventory"])

router.add_api_route(
    "/movements",
    controller.list_movements,
    methods=["GET"],
    dependencies=[Depends(get_current_user)],
)
router.add_api_route(
    "/adjust",
    controller.adjust,
    methods=["POST"],
    status_code=201,
    dependencies=[Depends(require_roles("admin", "manager"))],
)
router.add_api_route(
    "/valuation",
    controller.get_valuation,
    methods=["GET"],
    dependencies=[Depends(require_roles("admin", "manager"))],
)
