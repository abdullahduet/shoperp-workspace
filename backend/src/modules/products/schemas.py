"""Pydantic schemas for the products module."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    name: str
    sku: str
    barcode: Optional[str] = None
    category_id: Optional[str] = None
    description: Optional[str] = None
    unit_price: int = Field(default=0, ge=0)
    cost_price: int = Field(default=0, ge=0)
    tax_rate: float = Field(default=0.0, ge=0, le=100)
    stock_quantity: int = Field(default=0, ge=0)
    min_stock_level: int = Field(default=0, ge=0)
    unit_of_measure: str = "pcs"
    image_url: Optional[str] = None
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    category_id: Optional[str] = None
    description: Optional[str] = None
    unit_price: Optional[int] = Field(default=None, ge=0)
    cost_price: Optional[int] = Field(default=None, ge=0)
    tax_rate: Optional[float] = Field(default=None, ge=0, le=100)
    stock_quantity: Optional[int] = Field(default=None, ge=0)
    min_stock_level: Optional[int] = Field(default=None, ge=0)
    unit_of_measure: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    sku: str
    barcode: Optional[str] = None
    category_id: Optional[str] = None
    description: Optional[str] = None
    unit_price: int
    cost_price: int
    tax_rate: float
    stock_quantity: int
    min_stock_level: int
    unit_of_measure: str
    image_url: Optional[str] = None
    is_active: bool
    created_at: datetime

    @classmethod
    def model_validate(cls, obj, *, strict=None, from_attributes=None, context=None, experimental_allow_partial=None):  # type: ignore[override]
        if hasattr(obj, "__dict__") and not isinstance(obj, dict):
            data = {
                "id": obj.id,
                "name": obj.name,
                "sku": obj.sku,
                "barcode": obj.barcode,
                "category_id": obj.categoryId,
                "description": obj.description,
                "unit_price": obj.unitPrice,
                "cost_price": obj.costPrice,
                "tax_rate": float(obj.taxRate),
                "stock_quantity": obj.stockQuantity,
                "min_stock_level": obj.minStockLevel,
                "unit_of_measure": obj.unitOfMeasure,
                "image_url": obj.imageUrl,
                "is_active": obj.isActive,
                "created_at": obj.createdAt,
            }
            return cls(**data)
        return super().model_validate(
            obj,
            strict=strict,
            from_attributes=from_attributes,
            context=context,
        )


class ImportResult(BaseModel):
    created: int
    skipped: int
    errors: list[dict]
