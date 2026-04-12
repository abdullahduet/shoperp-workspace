"""Sales controller — thin layer: validate input, call service, return response."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, Query
from fastapi.responses import JSONResponse

from src.core.auth import get_current_user
from src.core.responses import paginated_response, success_response
from src.database import get_db
from src.modules.promotions.repository import PromotionRepository
from src.modules.promotions.service import PromotionService
from src.modules.sales.repository import SalesRepository
from src.modules.sales.schemas import SaleCreate
from src.modules.sales.service import SalesService


def _get_service(db=Depends(get_db)) -> SalesService:
    promotion_repo = PromotionRepository(db)
    promotion_service = PromotionService(promotion_repo)
    repo = SalesRepository(db)
    return SalesService(repo, promotion_service)


async def list_sales(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    payment_method: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    service: SalesService = Depends(_get_service),
) -> JSONResponse:
    result = await service.list(
        page=page,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        payment_method=payment_method,
    )
    return paginated_response(
        data=[s.model_dump(mode="json") for s in result.items],
        page=page,
        limit=limit,
        total=result.total,
    )


async def get_sale(
    sale_id: str,
    current_user=Depends(get_current_user),
    service: SalesService = Depends(_get_service),
) -> JSONResponse:
    sale = await service.get_by_id(sale_id)
    return success_response(data=sale.model_dump(mode="json"), message="Sale retrieved")


async def get_daily_summary(
    current_user=Depends(get_current_user),
    service: SalesService = Depends(_get_service),
) -> JSONResponse:
    summary = await service.get_daily_summary()
    return success_response(data=summary.model_dump(mode="json"), message="Daily summary retrieved")


async def record_sale(
    body: SaleCreate,
    current_user=Depends(get_current_user),
    service: SalesService = Depends(_get_service),
) -> JSONResponse:
    sale = await service.record_sale(body, recorded_by=current_user.id)
    return success_response(
        data=sale.model_dump(mode="json"),
        message="Sale recorded successfully",
        status_code=201,
    )
