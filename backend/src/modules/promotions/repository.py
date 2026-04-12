"""Promotions repository — database queries for promotions and promotion_products."""
from __future__ import annotations

from datetime import datetime, timezone


class PromotionRepository:
    def __init__(self, prisma) -> None:
        self.prisma = prisma

    async def find_paginated(self, skip: int, take: int, where: dict) -> tuple:
        """Return paginated promotions with promotionProducts included."""
        include = {"promotionProducts": True}
        items = await self.prisma.promotion.find_many(
            skip=skip,
            take=take,
            where=where,
            order=[{"createdAt": "desc"}],
            include=include,
        )
        total = await self.prisma.promotion.count(where=where)
        return items, total

    async def find_active(self, now: datetime) -> list:
        """Return all currently active promotions (is_active=True, within date range, not deleted)."""
        where = {
            "isActive": True,
            "deletedAt": None,
            "startDate": {"lte": now},
            "endDate": {"gte": now},
        }
        return await self.prisma.promotion.find_many(
            where=where,
            include={"promotionProducts": True},
        )

    async def find_by_id(self, promotion_id: str):
        """Return a non-deleted promotion with promotionProducts included, or None."""
        return await self.prisma.promotion.find_first(
            where={"id": promotion_id, "deletedAt": None},
            include={"promotionProducts": True},
        )

    async def create_with_products(self, promo_data: dict, product_ids: list[str]):
        """Create a promotion and its product associations in a transaction."""
        async with self.prisma.tx() as tx:
            promotion = await tx.promotion.create(data=promo_data)
            for product_id in product_ids:
                await tx.promotionproduct.create(
                    data={
                        "promotionId": promotion.id,
                        "productId": product_id,
                    }
                )
        return await self.prisma.promotion.find_first(
            where={"id": promotion.id},
            include={"promotionProducts": True},
        )

    async def update_with_products(
        self,
        promotion_id: str,
        promo_data: dict,
        product_ids: list[str] | None,
    ):
        """Update promotion fields and optionally replace product associations.

        product_ids=None → leave existing products unchanged
        product_ids=[]   → clear all product associations
        product_ids=[..] → replace with new list
        """
        async with self.prisma.tx() as tx:
            if promo_data:
                await tx.promotion.update(where={"id": promotion_id}, data=promo_data)
            if product_ids is not None:
                await tx.promotionproduct.delete_many(
                    where={"promotionId": promotion_id}
                )
                for product_id in product_ids:
                    await tx.promotionproduct.create(
                        data={
                            "promotionId": promotion_id,
                            "productId": product_id,
                        }
                    )
        return await self.prisma.promotion.find_first(
            where={"id": promotion_id},
            include={"promotionProducts": True},
        )

    async def soft_delete(self, promotion_id: str) -> None:
        """Set deletedAt to now, effectively removing the promotion from active queries."""
        await self.prisma.promotion.update(
            where={"id": promotion_id},
            data={"deletedAt": datetime.now(timezone.utc)},
        )
