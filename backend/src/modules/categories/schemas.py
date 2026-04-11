"""Pydantic schemas for the categories module."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1)
    description: Optional[str] = None
    parent_id: Optional[str] = None
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None
    parent_id: Optional[str] = None
    sort_order: Optional[int] = None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    sort_order: int
    created_at: datetime

    @classmethod
    def model_validate(cls, obj, *, strict=None, from_attributes=None, context=None, experimental_allow_partial=None):  # type: ignore[override]
        if hasattr(obj, "__dict__") and not isinstance(obj, dict):
            data = {
                "id": obj.id,
                "name": obj.name,
                "description": obj.description,
                "parent_id": obj.parentId,
                "sort_order": obj.sortOrder,
                "created_at": obj.createdAt,
            }
            return cls(**data)
        return super().model_validate(
            obj,
            strict=strict,
            from_attributes=from_attributes,
            context=context,
        )


class CategoryTreeNode(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    sort_order: int
    children: list["CategoryTreeNode"] = []
