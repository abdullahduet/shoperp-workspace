"""Pydantic schemas for the inventory module."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class AdjustmentRequest(BaseModel):
    product_id: str
    quantity: int
    notes: Optional[str] = None

    @field_validator('quantity')
    @classmethod
    def quantity_nonzero(cls, v: int) -> int:
        if v == 0:
            raise ValueError('quantity must be non-zero')
        return v


class StockMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    product_id: str
    product_name: str
    product_sku: str
    movement_type: str
    quantity: int
    stock_before: int
    stock_after: int
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    notes: Optional[str] = None
    performed_by: Optional[str] = None
    created_at: datetime

    @classmethod
    def model_validate(cls, obj, *, strict=None, from_attributes=None, context=None, experimental_allow_partial=None):  # type: ignore[override]
        if hasattr(obj, "__dict__") and not isinstance(obj, dict):
            data = {
                "id": obj.id,
                "product_id": obj.productId,
                "product_name": obj.product.name if obj.product else "",
                "product_sku": obj.product.sku if obj.product else "",
                "movement_type": obj.movementType,
                "quantity": obj.quantity,
                "stock_before": obj.stockBefore,
                "stock_after": obj.stockAfter,
                "reference_type": obj.referenceType,
                "reference_id": obj.referenceId,
                "notes": obj.notes,
                "performed_by": obj.performedBy,
                "created_at": obj.createdAt,
            }
            return cls(**data)
        return super().model_validate(obj, strict=strict, from_attributes=from_attributes, context=context)


class ValuationResponse(BaseModel):
    total_value: int
    product_count: int
    currency: str = "BDT"
