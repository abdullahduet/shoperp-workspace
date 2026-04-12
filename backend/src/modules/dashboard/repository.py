from datetime import datetime, date


class DashboardRepository:
    def __init__(self, prisma) -> None:
        self.prisma = prisma

    async def find_sales_in_range(self, start: datetime, end: datetime) -> list:
        return await self.prisma.sale.find_many(
            where={"deletedAt": None, "saleDate": {"gte": start, "lte": end}},
        )

    async def find_expenses_in_range(self, start: date, end: date) -> list:
        return await self.prisma.expense.find_many(
            where={"deletedAt": None, "date": {"gte": start, "lte": end}},
        )

    async def count_low_stock_products(self) -> int:
        products = await self.prisma.product.find_many(
            where={"deletedAt": None, "isActive": True},
        )
        return sum(1 for p in products if p.stockQuantity < p.minStockLevel)

    async def find_sales_last_12_months(self, start: datetime) -> list:
        return await self.prisma.sale.find_many(
            where={"deletedAt": None, "saleDate": {"gte": start}},
        )
