"""Suppliers router — wires HTTP paths to controller functions."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from src.core.auth import get_current_user, require_roles
from src.modules.suppliers import controller

router = APIRouter(prefix="/suppliers", tags=["suppliers"])

router.add_api_route(
    "",
    controller.list_suppliers,
    methods=["GET"],
    dependencies=[Depends(get_current_user)],
)
router.add_api_route(
    "/{supplier_id}",
    controller.get_supplier,
    methods=["GET"],
    dependencies=[Depends(get_current_user)],
)
router.add_api_route(
    "/{supplier_id}/purchases",
    controller.get_supplier_purchases,
    methods=["GET"],
    dependencies=[Depends(require_roles("admin", "manager"))],
)
router.add_api_route(
    "",
    controller.create_supplier,
    methods=["POST"],
    status_code=201,
    dependencies=[Depends(require_roles("admin", "manager"))],
)
router.add_api_route(
    "/{supplier_id}",
    controller.update_supplier,
    methods=["PUT"],
    dependencies=[Depends(require_roles("admin", "manager"))],
)
router.add_api_route(
    "/{supplier_id}",
    controller.delete_supplier,
    methods=["DELETE"],
    dependencies=[Depends(require_roles("admin"))],
)
