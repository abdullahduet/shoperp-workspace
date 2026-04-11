"""Pydantic schemas for the purchase_orders module."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class POItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0)
    unit_cost: int = Field(..., ge=0)


class POItemUpdate(BaseModel):
    product_id: Optional[str] = None
    quantity: Optional[int] = Field(None, gt=0)
    unit_cost: Optional[int] = Field(None, ge=0)


class PurchaseOrderCreate(BaseModel):
    supplier_id: str
    expected_date: Optional[str] = None  # ISO date string "YYYY-MM-DD"
    notes: Optional[str] = None
    items: list[POItemCreate] = Field(..., min_length=1)


class PurchaseOrderUpdate(BaseModel):
    supplier_id: Optional[str] = None
    expected_date: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[list[POItemCreate]] = None


class ReceiveItemInput(BaseModel):
    item_id: str
    received_quantity: int = Field(..., gt=0)


class ReceiveRequest(BaseModel):
    items: list[ReceiveItemInput] = Field(..., min_length=1)


class POItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    purchase_order_id: str
    product_id: str
    product_name: str
    product_sku: str
    quantity: int
    received_quantity: int
    unit_cost: int
    total_cost: int

    @classmethod
    def model_validate(cls, obj, *, strict=None, from_attributes=None, context=None, experimental_allow_partial=None):  # type: ignore[override]
        if hasattr(obj, "__dict__") and not isinstance(obj, dict):
            data = {
                "id": obj.id,
                "purchase_order_id": obj.purchaseOrderId,
                "product_id": obj.productId,
                "product_name": obj.product.name if obj.product else "",
                "product_sku": obj.product.sku if obj.product else "",
                "quantity": obj.quantity,
                "received_quantity": obj.receivedQuantity,
                "unit_cost": obj.unitCost,
                "total_cost": obj.totalCost,
            }
            return cls(**data)
        return super().model_validate(
            obj,
            strict=strict,
            from_attributes=from_attributes,
            context=context,
        )


class PurchaseOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    po_number: str
    supplier_id: str
    supplier_name: str
    order_date: str          # ISO date string
    expected_date: Optional[str] = None
    status: str
    subtotal: int
    tax_amount: int
    total_amount: int
    notes: Optional[str] = None
    created_by: Optional[str] = None
    created_at: str          # ISO datetime string
    items: list[POItemResponse] = []

    @classmethod
    def model_validate(cls, obj, *, strict=None, from_attributes=None, context=None, experimental_allow_partial=None):  # type: ignore[override]
        if hasattr(obj, "__dict__") and not isinstance(obj, dict):
            items = []
            if obj.purchaseOrderItems:
                items = [POItemResponse.model_validate(i) for i in obj.purchaseOrderItems]
            data = {
                "id": obj.id,
                "po_number": obj.poNumber,
                "supplier_id": obj.supplierId,
                "supplier_name": obj.supplier.name if obj.supplier else "",
                "order_date": obj.orderDate.isoformat() if obj.orderDate else "",
                "expected_date": obj.expectedDate.isoformat() if obj.expectedDate else None,
                "status": obj.status,
                "subtotal": obj.subtotal,
                "tax_amount": obj.taxAmount,
                "total_amount": obj.totalAmount,
                "notes": obj.notes,
                "created_by": obj.createdBy,
                "created_at": obj.createdAt.isoformat() if obj.createdAt else "",
                "items": items,
            }
            return cls(**data)
        return super().model_validate(
            obj,
            strict=strict,
            from_attributes=from_attributes,
            context=context,
        )
