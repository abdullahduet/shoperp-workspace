"""Inventory repository — database queries for stock movements and product stock."""
from __future__ import annotations

from typing import Optional

from prisma import Prisma
from prisma.models import Product, StockMovement


class InventoryRepository:
    def __init__(self, prisma: Prisma) -> None:
        self.prisma = prisma

    async def find_movements(
        self,
        skip: int,
        take: int,
        where: dict,
    ) -> tuple[list[StockMovement], int]:
        """Return paginated stock movements with product included."""
        items = await self.prisma.stockmovement.find_many(
            skip=skip,
            take=take,
            where=where,
            order=[{"createdAt": "desc"}],
            include={"product": True},
        )
        total = await self.prisma.stockmovement.count(where=where)
        return items, total

    async def find_product_by_id(self, product_id: str) -> Optional[Product]:
        """Return a non-deleted product by ID."""
        return await self.prisma.product.find_first(
            where={"id": product_id, "deletedAt": None}
        )

    async def create_adjustment(
        self,
        product_id: str,
        quantity: int,
        stock_before: int,
        stock_after: int,
        notes: Optional[str],
        performed_by: str,
    ) -> StockMovement:
        """Atomically create a stock movement and update product stock."""
        async with self.prisma.tx() as tx:
            movement = await tx.stockmovement.create(
                data={
                    "productId": product_id,
                    "movementType": "adjustment",
                    "quantity": quantity,
                    "stockBefore": stock_before,
                    "stockAfter": stock_after,
                    "notes": notes,
                    "performedBy": performed_by,
                    "referenceType": "manual_adjustment",
                },
                include={"product": True},
            )
            await tx.product.update(
                where={"id": product_id},
                data={"stockQuantity": stock_after},
            )
        return movement

    async def get_active_products_for_valuation(self) -> list:
        """Return all active, non-deleted products with stock > 0 for valuation calculation."""
        return await self.prisma.product.find_many(
            where={"deletedAt": None, "isActive": True, "stockQuantity": {"gt": 0}}
        )
