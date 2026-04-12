"""Expenses controller — thin layer: validate input, call service, return response."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, Query
from fastapi.responses import JSONResponse

from src.core.auth import get_current_user
from src.core.responses import paginated_response, success_response
from src.database import get_db
from src.modules.expenses.repository import ExpenseRepository
from src.modules.expenses.schemas import ExpenseCreate, ExpenseUpdate
from src.modules.expenses.service import ExpenseService


def _get_service(db=Depends(get_db)) -> ExpenseService:
    repo = ExpenseRepository(db)
    return ExpenseService(repo)


async def list_expenses(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    service: ExpenseService = Depends(_get_service),
) -> JSONResponse:
    result = await service.list(
        page=page,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        category=category,
    )
    return paginated_response(
        data=[e.model_dump(mode="json") for e in result.items],
        page=page,
        limit=limit,
        total=result.total,
    )


async def create_expense(
    body: ExpenseCreate,
    current_user=Depends(get_current_user),
    service: ExpenseService = Depends(_get_service),
) -> JSONResponse:
    expense = await service.create(body, recorded_by=current_user.id)
    return success_response(
        data=expense.model_dump(mode="json"),
        message="Expense recorded successfully",
        status_code=201,
    )


async def update_expense(
    expense_id: str,
    body: ExpenseUpdate,
    current_user=Depends(get_current_user),
    service: ExpenseService = Depends(_get_service),
) -> JSONResponse:
    expense = await service.update(expense_id, body)
    return success_response(
        data=expense.model_dump(mode="json"),
        message="Expense updated",
    )


async def delete_expense(
    expense_id: str,
    current_user=Depends(get_current_user),
    service: ExpenseService = Depends(_get_service),
) -> JSONResponse:
    await service.delete(expense_id)
    return success_response(None, "Expense deleted")
