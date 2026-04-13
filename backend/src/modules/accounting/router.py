"""Accounting router — wires HTTP paths to controller functions."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from src.core.auth import require_roles
from src.modules.accounting import controller

router = APIRouter(prefix="/accounting", tags=["accounting"])

router.add_api_route(
    "/seed-accounts",
    controller.seed_accounts,
    methods=["POST"],
    dependencies=[Depends(require_roles("admin"))],
)
router.add_api_route(
    "/accounts",
    controller.list_accounts,
    methods=["GET"],
    dependencies=[Depends(require_roles("admin", "manager"))],
)
router.add_api_route(
    "/journal-entries",
    controller.list_journal_entries,
    methods=["GET"],
    dependencies=[Depends(require_roles("admin", "manager"))],
)
router.add_api_route(
    "/journal-entries",
    controller.create_journal_entry,
    methods=["POST"],
    status_code=201,
    dependencies=[Depends(require_roles("admin"))],
)
