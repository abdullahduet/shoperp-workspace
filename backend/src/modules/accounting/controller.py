"""Accounting controller — thin layer: validate input, call service, return response."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, Query
from fastapi.responses import JSONResponse

from src.core.auth import get_current_user
from src.core.responses import paginated_response, success_response
from src.database import get_db
from src.modules.accounting.repository import AccountingRepository
from src.modules.accounting.schemas import JournalEntryCreate
from src.modules.accounting.service import AccountingService


def _get_service(db=Depends(get_db)) -> AccountingService:
    repo = AccountingRepository(db)
    return AccountingService(repo)


async def list_accounts(
    current_user=Depends(get_current_user),
    service: AccountingService = Depends(_get_service),
) -> JSONResponse:
    accounts = await service.list_accounts()
    return success_response(
        data=[a.model_dump(mode="json") for a in accounts],
        message="Accounts retrieved",
    )


async def list_journal_entries(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    reference_type: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    service: AccountingService = Depends(_get_service),
) -> JSONResponse:
    result = await service.list_journal_entries(
        page=page,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        reference_type=reference_type,
    )
    return paginated_response(
        data=[e.model_dump(mode="json") for e in result.items],
        page=page,
        limit=limit,
        total=result.total,
    )


async def create_journal_entry(
    body: JournalEntryCreate,
    current_user=Depends(get_current_user),
    service: AccountingService = Depends(_get_service),
) -> JSONResponse:
    entry = await service.create_journal_entry(body, created_by=current_user.id)
    return success_response(
        data=entry.model_dump(mode="json"),
        message="Journal entry created",
        status_code=201,
    )
