"""Promotions controller — thin layer: validate input, call service, return response."""
from __future__ import annotations

from typing import Optional

from fastapi import Depends, Query
from fastapi.responses import JSONResponse

from src.core.responses import paginated_response, success_response
from src.database import get_db
from src.modules.promotions.repository import PromotionRepository
from src.modules.promotions.schemas import PromotionCreate, PromotionUpdate
from src.modules.promotions.service import PromotionService


def _get_service(db=Depends(get_db)) -> PromotionService:
    return PromotionService(PromotionRepository(db))


async def list_promotions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    type: Optional[str] = Query(None),
    service: PromotionService = Depends(_get_service),
) -> JSONResponse:
    result = await service.list(page=page, limit=limit, is_active=is_active, type=type)
    return paginated_response(
        data=[p.model_dump(mode="json") for p in result.items],
        page=page,
        limit=limit,
        total=result.total,
    )


async def get_active_promotions(
    service: PromotionService = Depends(_get_service),
) -> JSONResponse:
    promotions = await service.get_active()
    return success_response(
        data=[p.model_dump(mode="json") for p in promotions],
        message="Active promotions retrieved",
    )


async def get_promotion(
    promotion_id: str,
    service: PromotionService = Depends(_get_service),
) -> JSONResponse:
    promotion = await service.get_by_id(promotion_id)
    return success_response(data=promotion.model_dump(mode="json"), message="Promotion retrieved")


async def create_promotion(
    body: PromotionCreate,
    service: PromotionService = Depends(_get_service),
) -> JSONResponse:
    promotion = await service.create(body)
    return success_response(
        data=promotion.model_dump(mode="json"),
        message="Promotion created",
        status_code=201,
    )


async def update_promotion(
    promotion_id: str,
    body: PromotionUpdate,
    service: PromotionService = Depends(_get_service),
) -> JSONResponse:
    promotion = await service.update(promotion_id, body)
    return success_response(data=promotion.model_dump(mode="json"), message="Promotion updated")


async def delete_promotion(
    promotion_id: str,
    service: PromotionService = Depends(_get_service),
) -> JSONResponse:
    await service.delete(promotion_id)
    return success_response(data=None, message="Promotion deleted")
