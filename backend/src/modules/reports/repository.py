from datetime import datetime, date


class ReportsRepository:
    def __init__(self, prisma) -> None:
        self.prisma = prisma

    async def find_sales_in_range(self, start: datetime, end: datetime) -> list:
        """Return non-deleted sales in [start, end] (saleDate range)."""
        return await self.prisma.sale.find_many(
            where={"deletedAt": None, "saleDate": {"gte": start, "lte": end}},
            order=[{"saleDate": "asc"}],
        )

    async def find_sales_with_items_in_range(self, start: datetime, end: datetime) -> list:
        """Return sales with saleItems + product included (for COGS and top products)."""
        return await self.prisma.sale.find_many(
            where={"deletedAt": None, "saleDate": {"gte": start, "lte": end}},
            include={"saleItems": {"include": {"product": True}}},
        )

    async def find_expenses_in_range(self, start: date, end: date) -> list:
        """Return non-deleted expenses in [start, end] (date range)."""
        return await self.prisma.expense.find_many(
            where={"deletedAt": None, "date": {"gte": start, "lte": end}},
            order=[{"date": "asc"}],
        )

    async def find_pos_in_range(self, start: date, end: date) -> list:
        """Return non-deleted, non-cancelled POs in [start, end] (orderDate range)."""
        return await self.prisma.purchaseorder.find_many(
            where={
                "deletedAt": None,
                "status": {"not": "cancelled"},
                "orderDate": {"gte": start, "lte": end},
            },
            order=[{"orderDate": "asc"}],
        )

    async def find_low_stock_products(self) -> list:
        """Return active products where stockQuantity < minStockLevel."""
        products = await self.prisma.product.find_many(
            where={"deletedAt": None, "isActive": True},
        )
        return [p for p in products if p.stockQuantity < p.minStockLevel]

    async def find_active_products_with_stock(self) -> list:
        """Return all active non-deleted products (for valuation)."""
        return await self.prisma.product.find_many(
            where={"deletedAt": None, "isActive": True},
        )
