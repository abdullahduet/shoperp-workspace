"""Products router — wires HTTP paths to controller functions."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from src.core.auth import get_current_user, require_roles
from src.modules.products import controller

router = APIRouter(prefix="/products", tags=["products"])

# Static paths MUST come before parameterized paths
router.add_api_route(
    "",
    controller.list_products,
    methods=["GET"],
    dependencies=[Depends(get_current_user)],
)
router.add_api_route(
    "/low-stock",
    controller.low_stock,
    methods=["GET"],
    dependencies=[Depends(get_current_user)],
)
router.add_api_route(
    "/import",
    controller.import_products,
    methods=["POST"],
    dependencies=[Depends(require_roles("admin"))],
)
router.add_api_route(
    "/{product_id}",
    controller.get_product,
    methods=["GET"],
    dependencies=[Depends(get_current_user)],
)
router.add_api_route(
    "",
    controller.create_product,
    methods=["POST"],
    status_code=201,
    dependencies=[Depends(require_roles("admin", "manager"))],
)
router.add_api_route(
    "/{product_id}",
    controller.update_product,
    methods=["PUT"],
    dependencies=[Depends(require_roles("admin", "manager"))],
)
router.add_api_route(
    "/{product_id}",
    controller.delete_product,
    methods=["DELETE"],
    dependencies=[Depends(require_roles("admin"))],
)
