"""Categories repository — database queries for the categories table only."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from prisma import Prisma
from prisma.models import Category


class CategoryRepository:
    def __init__(self, prisma: Prisma) -> None:
        self.prisma = prisma

    async def find_all(self) -> list[Category]:
        """Return all non-deleted categories ordered by sortOrder then name."""
        return await self.prisma.category.find_many(
            where={"deletedAt": None},
            order=[{"sortOrder": "asc"}, {"name": "asc"}],
        )

    async def find_by_id(self, category_id: str) -> Optional[Category]:
        """Return a non-deleted category by id, or None."""
        return await self.prisma.category.find_first(
            where={"id": category_id, "deletedAt": None}
        )

    async def create(self, data: dict) -> Category:
        """Insert a new category and return it."""
        return await self.prisma.category.create(data=data)

    async def update(self, category_id: str, data: dict) -> Category:
        """Update a category by id and return the updated record."""
        return await self.prisma.category.update(
            where={"id": category_id},
            data=data,
        )

    async def soft_delete(self, category_id: str) -> Category:
        """Set deletedAt to now, effectively removing the category from active queries."""
        return await self.prisma.category.update(
            where={"id": category_id},
            data={"deletedAt": datetime.now(timezone.utc)},
        )

    async def has_active_products(self, category_id: str) -> bool:
        """Return True if this category has at least one active (isActive=True, deletedAt=None) product."""
        count = await self.prisma.product.count(
            where={"categoryId": category_id, "isActive": True, "deletedAt": None}
        )
        return count > 0
