"""Purchase orders controller — thin layer: validate input, call service, return response."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, Query
from fastapi.responses import JSONResponse

from src.core.auth import get_current_user
from src.core.responses import paginated_response, success_response
from src.database import get_db
from src.modules.purchase_orders.repository import PurchaseOrderRepository
from src.modules.purchase_orders.schemas import (
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
    ReceiveRequest,
)
from src.modules.purchase_orders.service import PurchaseOrderService


def _get_service(db=Depends(get_db)) -> PurchaseOrderService:
    return PurchaseOrderService(PurchaseOrderRepository(db))


async def list_pos(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    supplier_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    service: PurchaseOrderService = Depends(_get_service),
) -> JSONResponse:
    result = await service.list(page=page, limit=limit, supplier_id=supplier_id, status=status)
    return paginated_response(
        data=[p.model_dump(mode="json") for p in result.items],
        page=page,
        limit=limit,
        total=result.total,
    )


async def get_po(
    po_id: str,
    service: PurchaseOrderService = Depends(_get_service),
) -> JSONResponse:
    po = await service.get_by_id(po_id)
    return success_response(data=po.model_dump(mode="json"), message="Purchase order retrieved")


async def create_po(
    body: PurchaseOrderCreate,
    current_user=Depends(get_current_user),
    service: PurchaseOrderService = Depends(_get_service),
) -> JSONResponse:
    po = await service.create(body, created_by=current_user.id)
    return success_response(data=po.model_dump(mode="json"), message="Purchase order created", status_code=201)


async def update_po(
    po_id: str,
    body: PurchaseOrderUpdate,
    service: PurchaseOrderService = Depends(_get_service),
) -> JSONResponse:
    po = await service.update(po_id, body)
    return success_response(data=po.model_dump(mode="json"), message="Purchase order updated")


async def delete_po(
    po_id: str,
    service: PurchaseOrderService = Depends(_get_service),
) -> JSONResponse:
    await service.delete(po_id)
    return success_response(data=None, message="Purchase order deleted")


async def submit_po(
    po_id: str,
    service: PurchaseOrderService = Depends(_get_service),
) -> JSONResponse:
    po = await service.submit(po_id)
    return success_response(data=po.model_dump(mode="json"), message="Purchase order submitted")


async def receive_po(
    po_id: str,
    body: ReceiveRequest,
    current_user=Depends(get_current_user),
    service: PurchaseOrderService = Depends(_get_service),
) -> JSONResponse:
    po = await service.receive(po_id, body, performed_by=current_user.id)
    return success_response(data=po.model_dump(mode="json"), message="Items received")


async def cancel_po(
    po_id: str,
    service: PurchaseOrderService = Depends(_get_service),
) -> JSONResponse:
    po = await service.cancel(po_id)
    return success_response(data=po.model_dump(mode="json"), message="Purchase order cancelled")
