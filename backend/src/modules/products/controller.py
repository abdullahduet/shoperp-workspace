"""Products controller — thin layer: validate input, call service, return response."""
from __future__ import annotations

from typing import Literal, Optional

from fastapi import Depends, File, Query, UploadFile
from fastapi.responses import JSONResponse

from src.core.responses import paginated_response, success_response
from src.database import get_db
from src.modules.products.repository import ProductRepository
from src.modules.products.schemas import ProductCreate, ProductUpdate
from src.modules.products.service import ProductService


def _get_service(db=Depends(get_db)) -> ProductService:
    return ProductService(ProductRepository(db))


async def list_products(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    sort: str = Query("name"),
    order: Literal["asc", "desc"] = Query("asc"),
    service: ProductService = Depends(_get_service),
) -> JSONResponse:
    result = await service.list_products(
        page=page,
        limit=limit,
        search=search,
        category_id=category_id,
        is_active=is_active,
        sort=sort,
        order=order,
    )
    return paginated_response(
        data=[p.model_dump(mode="json") for p in result.items],
        page=page,
        limit=limit,
        total=result.total,
    )


async def low_stock(
    service: ProductService = Depends(_get_service),
) -> JSONResponse:
    products = await service.get_low_stock()
    return success_response(
        data=[p.model_dump(mode="json") for p in products],
        message="Low stock products retrieved",
    )


async def get_product(
    product_id: str,
    service: ProductService = Depends(_get_service),
) -> JSONResponse:
    product = await service.get_by_id(product_id)
    return success_response(
        data=product.model_dump(mode="json"),
        message="Product retrieved",
    )


async def create_product(
    body: ProductCreate,
    service: ProductService = Depends(_get_service),
) -> JSONResponse:
    product = await service.create(body)
    return success_response(
        data=product.model_dump(mode="json"),
        message="Product created",
        status_code=201,
    )


async def update_product(
    product_id: str,
    body: ProductUpdate,
    service: ProductService = Depends(_get_service),
) -> JSONResponse:
    product = await service.update(product_id, body)
    return success_response(
        data=product.model_dump(mode="json"),
        message="Product updated",
    )


async def delete_product(
    product_id: str,
    service: ProductService = Depends(_get_service),
) -> JSONResponse:
    await service.delete(product_id)
    return success_response(data=None, message="Product deleted")


async def import_products(
    file: UploadFile = File(...),
    service: ProductService = Depends(_get_service),
) -> JSONResponse:
    contents = await file.read()
    result = await service.import_from_csv(contents)
    return success_response(data=result, message="Import complete")
