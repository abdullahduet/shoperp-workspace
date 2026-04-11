"""Categories router — wires HTTP paths to controller functions."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from src.core.auth import get_current_user, require_roles
from src.modules.categories import controller

router = APIRouter(prefix="/categories", tags=["categories"])

# Any authenticated user — read endpoints
router.add_api_route(
    "",
    controller.list_categories,
    methods=["GET"],
    dependencies=[Depends(get_current_user)],
)
# /tree MUST come before /{category_id}
router.add_api_route(
    "/tree",
    controller.get_tree,
    methods=["GET"],
    dependencies=[Depends(get_current_user)],
)
router.add_api_route(
    "/{category_id}",
    controller.get_category,
    methods=["GET"],
    dependencies=[Depends(get_current_user)],
)

# Write endpoints — admin or manager
router.add_api_route(
    "",
    controller.create_category,
    methods=["POST"],
    status_code=201,
    dependencies=[Depends(require_roles("admin", "manager"))],
)
router.add_api_route(
    "/{category_id}",
    controller.update_category,
    methods=["PUT"],
    dependencies=[Depends(require_roles("admin", "manager"))],
)

# Delete — admin only
router.add_api_route(
    "/{category_id}",
    controller.delete_category,
    methods=["DELETE"],
    dependencies=[Depends(require_roles("admin"))],
)
