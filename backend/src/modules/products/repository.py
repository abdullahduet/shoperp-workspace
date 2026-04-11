"""Products repository — database queries for the products table only."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from prisma import Prisma
from prisma.models import Product


class ProductRepository:
    def __init__(self, prisma: Prisma) -> None:
        self.prisma = prisma

    async def find_paginated(
        self,
        skip: int,
        take: int,
        where: dict,
        order_by: dict,
    ) -> tuple[list[Product], int]:
        """Return paginated products and total count matching *where*."""
        items = await self.prisma.product.find_many(
            skip=skip,
            take=take,
            where=where,
            order=[order_by],
        )
        total = await self.prisma.product.count(where=where)
        return items, total

    async def find_low_stock(self) -> list[Product]:
        """Return active products where stockQuantity < minStockLevel (filtered in Python)."""
        products = await self.prisma.product.find_many(
            where={"deletedAt": None, "isActive": True},
        )
        return [p for p in products if p.stockQuantity < p.minStockLevel]

    async def find_by_id(self, product_id: str) -> Optional[Product]:
        """Return a non-deleted product by id, or None."""
        return await self.prisma.product.find_first(
            where={"id": product_id, "deletedAt": None}
        )

    async def find_by_sku(self, sku: str) -> Optional[Product]:
        """Return a non-deleted product matching *sku*, or None."""
        return await self.prisma.product.find_first(
            where={"sku": sku, "deletedAt": None}
        )

    async def find_by_barcode(self, barcode: str) -> Optional[Product]:
        """Return a non-deleted product matching *barcode*, or None."""
        return await self.prisma.product.find_first(
            where={"barcode": barcode, "deletedAt": None}
        )

    async def create(self, data: dict) -> Product:
        """Insert a new product and return it."""
        return await self.prisma.product.create(data=data)

    async def update(self, product_id: str, data: dict) -> Product:
        """Update a product by id and return the updated record."""
        return await self.prisma.product.update(
            where={"id": product_id},
            data=data,
        )

    async def soft_delete(self, product_id: str) -> Product:
        """Set deletedAt to now, effectively removing the product from active queries."""
        return await self.prisma.product.update(
            where={"id": product_id},
            data={"deletedAt": datetime.now(timezone.utc)},
        )
