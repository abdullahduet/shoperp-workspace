"""Promotions router — wires HTTP paths to controller functions."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from src.core.auth import require_roles
from src.modules.promotions import controller

router = APIRouter(prefix="/promotions", tags=["promotions"])

# Static routes BEFORE parameterized /{promotion_id}
router.add_api_route(
    "",
    controller.list_promotions,
    methods=["GET"],
    dependencies=[Depends(require_roles("admin", "manager", "staff"))],
)
router.add_api_route(
    "",
    controller.create_promotion,
    methods=["POST"],
    status_code=201,
    dependencies=[Depends(require_roles("admin", "manager"))],
)
router.add_api_route(
    "/active",
    controller.get_active_promotions,
    methods=["GET"],
    dependencies=[Depends(require_roles("admin", "manager", "staff"))],
)

# Parameterized routes LAST
router.add_api_route(
    "/{promotion_id}",
    controller.get_promotion,
    methods=["GET"],
    dependencies=[Depends(require_roles("admin", "manager", "staff"))],
)
router.add_api_route(
    "/{promotion_id}",
    controller.update_promotion,
    methods=["PUT"],
    dependencies=[Depends(require_roles("admin", "manager"))],
)
router.add_api_route(
    "/{promotion_id}",
    controller.delete_promotion,
    methods=["DELETE"],
    dependencies=[Depends(require_roles("admin"))],
)
