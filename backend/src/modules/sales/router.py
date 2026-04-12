"""Sales router — wires HTTP paths to controller functions."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from src.core.auth import get_current_user, require_roles
from src.modules.sales import controller

router = APIRouter(prefix="/sales", tags=["sales"])

# List and create on root
router.add_api_route(
    "",
    controller.list_sales,
    methods=["GET"],
    dependencies=[Depends(get_current_user)],
)
router.add_api_route(
    "",
    controller.record_sale,
    methods=["POST"],
    status_code=201,
    dependencies=[Depends(get_current_user)],
)

# CRITICAL: /daily-summary MUST be registered BEFORE /{sale_id}
router.add_api_route(
    "/daily-summary",
    controller.get_daily_summary,
    methods=["GET"],
    dependencies=[Depends(require_roles("admin", "manager"))],
)

# Parameterized route last
router.add_api_route(
    "/{sale_id}",
    controller.get_sale,
    methods=["GET"],
    dependencies=[Depends(get_current_user)],
)
