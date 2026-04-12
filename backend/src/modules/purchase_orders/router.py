"""Purchase orders router — wires HTTP paths to controller functions."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from src.core.auth import require_roles
from src.modules.purchase_orders import controller

router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])

# Static GET/POST first
router.add_api_route(
    "",
    controller.list_pos,
    methods=["GET"],
    dependencies=[Depends(require_roles("admin", "manager"))],
)
router.add_api_route(
    "",
    controller.create_po,
    methods=["POST"],
    status_code=201,
    dependencies=[Depends(require_roles("admin", "manager"))],
)

# Action routes BEFORE bare /{po_id}
router.add_api_route(
    "/{po_id}/submit",
    controller.submit_po,
    methods=["POST"],
    dependencies=[Depends(require_roles("admin", "manager"))],
)
router.add_api_route(
    "/{po_id}/receive",
    controller.receive_po,
    methods=["POST"],
    dependencies=[Depends(require_roles("admin", "manager"))],
)
router.add_api_route(
    "/{po_id}/cancel",
    controller.cancel_po,
    methods=["POST"],
    dependencies=[Depends(require_roles("admin"))],
)

# Bare /{po_id} routes LAST
router.add_api_route(
    "/{po_id}",
    controller.get_po,
    methods=["GET"],
    dependencies=[Depends(require_roles("admin", "manager"))],
)
router.add_api_route(
    "/{po_id}",
    controller.update_po,
    methods=["PUT"],
    dependencies=[Depends(require_roles("admin", "manager"))],
)
router.add_api_route(
    "/{po_id}",
    controller.delete_po,
    methods=["DELETE"],
    dependencies=[Depends(require_roles("admin"))],
)
