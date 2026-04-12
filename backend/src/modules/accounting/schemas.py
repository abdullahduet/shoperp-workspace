from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, Field


class AccountResponse(BaseModel):
    id: str
    code: str
    name: str
    type: str
    parent_id: Optional[str]
    is_active: bool
    created_at: str

    @classmethod
    def model_validate(cls, obj):  # type: ignore[override]
        return cls(
            id=obj.id,
            code=obj.code,
            name=obj.name,
            type=obj.type,
            parent_id=obj.parentId,
            is_active=obj.isActive,
            created_at=obj.createdAt.isoformat(),
        )


class JournalEntryLineCreate(BaseModel):
    account_id: str
    debit_amount: int = 0
    credit_amount: int = 0
    description: Optional[str] = None


class JournalEntryCreate(BaseModel):
    description: str
    date: Optional[str] = None  # YYYY-MM-DD, defaults to today if None
    lines: list[JournalEntryLineCreate] = Field(min_length=2)


class JournalEntryLineResponse(BaseModel):
    id: str
    account_id: str
    debit_amount: int
    credit_amount: int
    description: Optional[str]

    @classmethod
    def model_validate(cls, obj):  # type: ignore[override]
        return cls(
            id=obj.id,
            account_id=obj.accountId,
            debit_amount=obj.debitAmount,
            credit_amount=obj.creditAmount,
            description=obj.description,
        )


class JournalEntryResponse(BaseModel):
    id: str
    entry_number: str
    date: str
    description: str
    reference_type: Optional[str]
    reference_id: Optional[str]
    created_by: Optional[str]
    lines: list[JournalEntryLineResponse]
    created_at: str

    @classmethod
    def model_validate(cls, obj):  # type: ignore[override]
        return cls(
            id=obj.id,
            entry_number=obj.entryNumber,
            date=obj.date.strftime("%Y-%m-%d"),
            description=obj.description,
            reference_type=obj.referenceType,
            reference_id=obj.referenceId,
            created_by=obj.createdBy,
            lines=[
                JournalEntryLineResponse.model_validate(line)
                for line in (obj.journalEntryLines or [])
            ],
            created_at=obj.createdAt.isoformat(),
        )


@dataclass
class PaginatedJournalEntries:
    items: list[JournalEntryResponse]
    total: int
