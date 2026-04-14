"""Sales repository — database queries only. No business logic or calculations."""
from __future__ import annotations

from datetime import datetime


class SalesRepository:
    def __init__(self, prisma) -> None:
        self.prisma = prisma

    async def find_by_id(self, sale_id: str):
        """Return a sale with saleItems + product included, or None if not found / deleted."""
        return await self.prisma.sale.find_first(
            where={"id": sale_id, "deletedAt": None},
            include={"saleItems": {"include": {"product": True}}},
        )

    async def find_paginated(self, skip: int, take: int, where: dict) -> tuple:
        """Return (list[Sale], total_count) with saleItems + product included."""
        items = await self.prisma.sale.find_many(
            skip=skip,
            take=take,
            where=where,
            order=[{"saleDate": "desc"}],
            include={"saleItems": {"include": {"product": True}}},
        )
        total = await self.prisma.sale.count(where=where)
        return items, total

    async def count_today_sales(self, today_str: str) -> int:
        """Count sales whose saleNumber starts with SALE-{today_str}."""
        return await self.prisma.sale.count(
            where={"saleNumber": {"startsWith": f"SALE-{today_str}"}}
        )

    async def count_today_journal_entries(self, today_str: str) -> int:
        """Count journal entries whose entryNumber starts with JE-{today_str}."""
        return await self.prisma.journalentry.count(
            where={"entryNumber": {"startsWith": f"JE-{today_str}"}}
        )

    async def find_product_by_id(self, product_id: str):
        """Return a product (for validation and tax rate), or None."""
        return await self.prisma.product.find_first(
            where={"id": product_id, "deletedAt": None}
        )

    async def find_account_by_code(self, code: str):
        """Return an Account by its code, or None."""
        return await self.prisma.account.find_first(
            where={"code": code}
        )

    async def find_today_sales(self, today_start: datetime, today_end: datetime) -> list:
        """Return all non-deleted sales within [today_start, today_end)."""
        return await self.prisma.sale.find_many(
            where={
                "deletedAt": None,
                "saleDate": {"gte": today_start, "lt": today_end},
            }
        )

    async def create_sale_atomic(
        self,
        sale_data: dict,
        items_data: list[dict],
        stock_updates: list[dict],
        journal_data: dict,
    ):
        """Atomically create sale + items + stock movements + journal entry + lines."""
        async with self.prisma.tx() as tx:
            sale = await tx.sale.create(data=sale_data)

            for item in items_data:
                await tx.saleitem.create(data={"saleId": sale.id, **item})

            for su in stock_updates:
                await tx.product.update(
                    where={"id": su["product_id"]},
                    data={"stockQuantity": su["stock_after"]},
                )
                await tx.stockmovement.create(
                    data={
                        "productId": su["product_id"],
                        "movementType": "out",
                        "quantity": su["qty"],
                        "stockBefore": su["stock_before"],
                        "stockAfter": su["stock_after"],
                        "referenceType": "sale",
                        "referenceId": str(sale.id),
                        "performedBy": su["performed_by"],
                    }
                )

            entry = await tx.journalentry.create(
                data={
                    "entryNumber": journal_data["entry_number"],
                    "description": journal_data["description"],
                    "referenceType": "sale",
                    "referenceId": str(sale.id),
                    "createdBy": journal_data["created_by"],
                }
            )
            await tx.journalentryline.create(
                data={
                    "journalEntryId": entry.id,
                    "accountId": journal_data["debit_account_id"],
                    "debitAmount": journal_data["amount"],
                    "creditAmount": 0,
                    "description": "Cash received",
                }
            )
            await tx.journalentryline.create(
                data={
                    "journalEntryId": entry.id,
                    "accountId": journal_data["credit_account_id"],
                    "debitAmount": 0,
                    "creditAmount": journal_data["amount"],
                    "description": "Sales revenue",
                }
            )

        return await self.prisma.sale.find_first(
            where={"id": sale.id},
            include={"saleItems": {"include": {"product": True}}},
        )
