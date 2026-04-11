from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

PaymentMethod = Literal["cash", "card", "mobile", "credit"]


class SaleItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)
    unit_price: int = Field(ge=0)  # paisa


class SaleCreate(BaseModel):
    items: list[SaleItemCreate] = Field(min_length=1)
    payment_method: PaymentMethod = "cash"
    customer_name: Optional[str] = None
    notes: Optional[str] = None


class SaleItemResponse(BaseModel):
    id: str
    product_id: str
    quantity: int
    unit_price: int
    discount: int
    total_price: int
    created_at: str

    @classmethod
    def model_validate(cls, obj):  # type: ignore[override]
        return cls(
            id=obj.id,
            product_id=obj.productId,
            quantity=obj.quantity,
            unit_price=obj.unitPrice,
            discount=obj.discount,
            total_price=obj.totalPrice,
            created_at=obj.createdAt.isoformat(),
        )


class SaleResponse(BaseModel):
    id: str
    sale_number: str
    sale_date: str
    customer_name: Optional[str]
    subtotal: int
    discount_amount: int
    tax_amount: int
    total_amount: int
    payment_method: str
    promotion_id: Optional[str]
    notes: Optional[str]
    recorded_by: Optional[str]
    items: list[SaleItemResponse]
    created_at: str

    @classmethod
    def model_validate(cls, obj):  # type: ignore[override]
        return cls(
            id=obj.id,
            sale_number=obj.saleNumber,
            sale_date=obj.saleDate.isoformat(),
            customer_name=obj.customerName,
            subtotal=obj.subtotal,
            discount_amount=obj.discountAmount,
            tax_amount=obj.taxAmount,
            total_amount=obj.totalAmount,
            payment_method=obj.paymentMethod,
            promotion_id=obj.promotionId,
            notes=obj.notes,
            recorded_by=obj.recordedBy,
            items=[SaleItemResponse.model_validate(i) for i in (obj.saleItems or [])],
            created_at=obj.createdAt.isoformat(),
        )


class DailySummaryResponse(BaseModel):
    date: str
    total_sales: int
    transaction_count: int
    payment_breakdown: dict[str, int]
