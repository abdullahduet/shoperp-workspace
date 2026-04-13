"""Dashboard repository — database queries only. No business logic."""
from __future__ import annotations

from datetime import datetime


class DashboardRepository:
    def __init__(self, prisma) -> None:
        self.prisma = prisma

    async def find_sales_in_range(self, start: datetime, end: datetime) -> list:
        """Return non-deleted sales whose saleDate falls in [start, end)."""
        return await self.prisma.sale.find_many(
            where={"deletedAt": None, "saleDate": {"gte": start, "lte": end}},
        )

    async def find_expenses_in_range(self, start: datetime, end: datetime) -> list:
        """Return non-deleted expenses whose date falls in [start, end].

        Expense.date is @db.Date — Prisma Client Python requires datetime
        objects (not bare date objects) for this column type.
        """
        return await self.prisma.expense.find_many(
            where={"deletedAt": None, "date": {"gte": start, "lte": end}},
        )

    async def count_low_stock_products(self) -> int:
        """Count active products where stock_quantity < min_stock_level.

        Fetches at most 10 000 rows to avoid unbounded memory use on large
        catalogues. In practice a shop with >10 000 SKUs would need a raw
        SQL count; this bound is safe for the target single-shop scale.
        """
        products = await self.prisma.product.find_many(
            where={"deletedAt": None, "isActive": True},
            take=10_000,
        )
        return sum(1 for p in products if p.stockQuantity < p.minStockLevel)

    async def find_sales_last_12_months(self, start: datetime) -> list:
        """Return non-deleted sales from *start* to now."""
        return await self.prisma.sale.find_many(
            where={"deletedAt": None, "saleDate": {"gte": start}},
        )
