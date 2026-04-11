"""Inventory controller — thin layer: validate input, call service, return response."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, Query
from fastapi.responses import JSONResponse
from prisma.models import User

from src.core.auth import get_current_user
from src.core.responses import paginated_response, success_response
from src.database import get_db
from src.modules.inventory.repository import InventoryRepository
from src.modules.inventory.schemas import AdjustmentRequest
from src.modules.inventory.service import InventoryService


def _get_service(db=Depends(get_db)) -> InventoryService:
    return InventoryService(InventoryRepository(db))


async def list_movements(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    product_id: Optional[str] = Query(None),
    movement_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    service: InventoryService = Depends(_get_service),
) -> JSONResponse:
    result = await service.list_movements(page, limit, product_id, movement_type, start_date, end_date)
    return paginated_response(
        data=[m.model_dump(mode="json") for m in result.items],
        page=page,
        limit=limit,
        total=result.total,
    )


async def adjust(
    body: AdjustmentRequest,
    current_user: User = Depends(get_current_user),
    service: InventoryService = Depends(_get_service),
) -> JSONResponse:
    movement = await service.adjust(
        product_id=body.product_id,
        quantity=body.quantity,
        notes=body.notes,
        performed_by=current_user.id,
    )
    return success_response(data=movement.model_dump(mode="json"), message="Stock adjusted", status_code=201)


async def get_valuation(
    service: InventoryService = Depends(_get_service),
) -> JSONResponse:
    result = await service.get_valuation()
    return success_response(data=result.model_dump(), message="OK")
