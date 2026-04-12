from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

from pydantic import BaseModel, Field

PaymentMethod = Literal["cash", "card", "mobile", "credit"]


class ExpenseCreate(BaseModel):
    category: str
    description: str
    amount: int = Field(gt=0)  # paisa
    payment_method: PaymentMethod = "cash"
    date: Optional[str] = None  # YYYY-MM-DD, defaults to today
    receipt_url: Optional[str] = None
    notes: Optional[str] = None


class ExpenseUpdate(BaseModel):
    category: Optional[str] = None
    description: Optional[str] = None
    amount: Optional[int] = None
    payment_method: Optional[str] = None
    date: Optional[str] = None
    receipt_url: Optional[str] = None
    notes: Optional[str] = None


class ExpenseResponse(BaseModel):
    id: str
    date: str
    category: str
    description: str
    amount: int
    payment_method: str
    receipt_url: Optional[str]
    notes: Optional[str]
    recorded_by: Optional[str]
    created_at: str

    @classmethod
    def model_validate(cls, obj):  # type: ignore[override]
        return cls(
            id=obj.id,
            date=obj.date.strftime("%Y-%m-%d"),
            category=obj.category,
            description=obj.description,
            amount=obj.amount,
            payment_method=obj.paymentMethod,
            receipt_url=obj.receiptUrl,
            notes=obj.notes,
            recorded_by=obj.recordedBy,
            created_at=obj.createdAt.isoformat(),
        )


@dataclass
class PaginatedExpenses:
    items: list[ExpenseResponse]
    total: int
