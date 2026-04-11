"""Suppliers repository — database queries for the suppliers table only."""
from __future__ import annotations

from datetime import datetime, timezone


class SupplierRepository:
    def __init__(self, prisma) -> None:
        self.prisma = prisma

    async def find_paginated(self, skip: int, take: int, where: dict, order_by: dict) -> tuple:
        """Return paginated suppliers and total count matching *where*."""
        items = await self.prisma.supplier.find_many(
            skip=skip,
            take=take,
            where=where,
            order=[order_by],
        )
        total = await self.prisma.supplier.count(where=where)
        return items, total

    async def find_by_id(self, supplier_id: str):
        """Return a non-deleted supplier by id, or None."""
        return await self.prisma.supplier.find_first(
            where={"id": supplier_id, "deletedAt": None}
        )

    async def create(self, data: dict):
        """Insert a new supplier and return it."""
        return await self.prisma.supplier.create(data=data)

    async def update(self, supplier_id: str, data: dict):
        """Update a supplier by id and return the updated record."""
        return await self.prisma.supplier.update(
            where={"id": supplier_id},
            data=data,
        )

    async def soft_delete(self, supplier_id: str):
        """Set deletedAt to now, effectively removing the supplier from active queries."""
        return await self.prisma.supplier.update(
            where={"id": supplier_id},
            data={"deletedAt": datetime.now(timezone.utc)},
        )
