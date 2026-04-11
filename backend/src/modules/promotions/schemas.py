"""Pydantic schemas for the promotions module."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class PromotionCreate(BaseModel):
    name: str = Field(..., min_length=1)
    type: Literal["percentage", "fixed", "bogo"]
    value: int = Field(..., ge=0)
    start_date: str  # ISO datetime string
    end_date: str    # ISO datetime string
    min_purchase_amount: int = Field(0, ge=0)
    applies_to: Literal["all", "specific"] = "all"
    is_active: bool = True
    product_ids: list[str] = []


class PromotionUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[Literal["percentage", "fixed", "bogo"]] = None
    value: Optional[int] = Field(None, ge=0)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    min_purchase_amount: Optional[int] = Field(None, ge=0)
    applies_to: Optional[Literal["all", "specific"]] = None
    is_active: Optional[bool] = None
    product_ids: Optional[list[str]] = None  # None = don't touch; [] = clear all


class PromotionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: str
    value: int
    start_date: str
    end_date: str
    min_purchase_amount: int
    applies_to: str
    is_active: bool
    product_ids: list[str]
    created_at: str

    @classmethod
    def model_validate(  # type: ignore[override]
        cls,
        obj,
        *,
        strict=None,
        from_attributes=None,
        context=None,
        experimental_allow_partial=None,
    ):
        if hasattr(obj, "__dict__") and not isinstance(obj, dict):
            data = {
                "id": obj.id,
                "name": obj.name,
                "type": obj.type,
                "value": obj.value,
                "start_date": obj.startDate.isoformat() if obj.startDate else "",
                "end_date": obj.endDate.isoformat() if obj.endDate else "",
                "min_purchase_amount": obj.minPurchaseAmount,
                "applies_to": obj.appliesTo,
                "is_active": obj.isActive,
                "product_ids": (
                    [pp.productId for pp in obj.promotionProducts]
                    if obj.promotionProducts
                    else []
                ),
                "created_at": obj.createdAt.isoformat() if obj.createdAt else "",
            }
            return cls(**data)
        return super().model_validate(
            obj,
            strict=strict,
            from_attributes=from_attributes,
            context=context,
        )
