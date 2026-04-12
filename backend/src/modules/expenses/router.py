"""Expenses router — wires HTTP paths to controller functions."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from src.core.auth import require_roles
from src.modules.expenses import controller

router = APIRouter(prefix="/expenses", tags=["expenses"])

router.add_api_route(
    "",
    controller.list_expenses,
    methods=["GET"],
    dependencies=[Depends(require_roles("admin", "manager"))],
)
router.add_api_route(
    "",
    controller.create_expense,
    methods=["POST"],
    status_code=201,
    dependencies=[Depends(require_roles("admin", "manager"))],
)
router.add_api_route(
    "/{expense_id}",
    controller.update_expense,
    methods=["PUT"],
    dependencies=[Depends(require_roles("admin", "manager"))],
)
router.add_api_route(
    "/{expense_id}",
    controller.delete_expense,
    methods=["DELETE"],
    dependencies=[Depends(require_roles("admin"))],
)
