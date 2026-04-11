"""Suppliers controller — thin layer: validate input, call service, return response."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, Query
from fastapi.responses import JSONResponse

from src.core.responses import paginated_response, success_response
from src.database import get_db
from src.modules.suppliers.repository import SupplierRepository
from src.modules.suppliers.schemas import SupplierCreate, SupplierUpdate
from src.modules.suppliers.service import SupplierService


def _get_service(db=Depends(get_db)) -> SupplierService:
    return SupplierService(SupplierRepository(db))


def _get_po_service(db=Depends(get_db)):
    from src.modules.purchase_orders.repository import PurchaseOrderRepository
    from src.modules.purchase_orders.service import PurchaseOrderService

    return PurchaseOrderService(PurchaseOrderRepository(db))


async def list_suppliers(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    service: SupplierService = Depends(_get_service),
) -> JSONResponse:
    result = await service.list(page=page, limit=limit, search=search, is_active=is_active)
    return paginated_response(
        data=[s.model_dump(mode="json") for s in result.items],
        page=page,
        limit=limit,
        total=result.total,
    )


async def get_supplier(
    supplier_id: str,
    service: SupplierService = Depends(_get_service),
) -> JSONResponse:
    supplier = await service.get_by_id(supplier_id)
    return success_response(data=supplier.model_dump(mode="json"), message="Supplier retrieved")


async def get_supplier_purchases(
    supplier_id: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    service: SupplierService = Depends(_get_service),
    po_service=Depends(_get_po_service),
) -> JSONResponse:
    # Verify the supplier exists first
    await service.get_by_id(supplier_id)
    result = await po_service.list(page=page, limit=limit, supplier_id=supplier_id, status=None)
    return paginated_response(
        data=[p.model_dump(mode="json") for p in result.items],
        page=page,
        limit=limit,
        total=result.total,
    )


async def create_supplier(
    body: SupplierCreate,
    service: SupplierService = Depends(_get_service),
) -> JSONResponse:
    supplier = await service.create(body)
    return success_response(data=supplier.model_dump(mode="json"), message="Supplier created", status_code=201)


async def update_supplier(
    supplier_id: str,
    body: SupplierUpdate,
    service: SupplierService = Depends(_get_service),
) -> JSONResponse:
    supplier = await service.update(supplier_id, body)
    return success_response(data=supplier.model_dump(mode="json"), message="Supplier updated")


async def delete_supplier(
    supplier_id: str,
    service: SupplierService = Depends(_get_service),
) -> JSONResponse:
    await service.delete(supplier_id)
    return success_response(data=None, message="Supplier deleted")
