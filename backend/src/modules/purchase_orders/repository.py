"""Purchase orders repository — database queries for purchase orders and related tables."""
from __future__ import annotations

from datetime import datetime, timezone


class PurchaseOrderRepository:
    def __init__(self, prisma) -> None:
        self.prisma = prisma

    async def find_paginated(self, skip: int, take: int, where: dict) -> tuple:
        """Return paginated purchase orders with items and supplier included."""
        include = {"purchaseOrderItems": {"include": {"product": True}}, "supplier": True}
        items = await self.prisma.purchaseorder.find_many(
            skip=skip,
            take=take,
            where=where,
            order=[{"createdAt": "desc"}],
            include=include,
        )
        total = await self.prisma.purchaseorder.count(where=where)
        return items, total

    async def find_by_id(self, po_id: str):
        """Return a non-deleted purchase order with full includes, or None."""
        include = {"purchaseOrderItems": {"include": {"product": True}}, "supplier": True}
        return await self.prisma.purchaseorder.find_first(
            where={"id": po_id, "deletedAt": None},
            include=include,
        )

    async def count_today_pos(self, date_str: str) -> int:
        """Count purchase orders with PO number starting with today's date prefix."""
        return await self.prisma.purchaseorder.count(
            where={"poNumber": {"startsWith": f"PO-{date_str}-"}}
        )

    async def create_with_items(self, po_data: dict, items_data: list[dict]):
        """Create a purchase order with nested items in a single call."""
        include = {"purchaseOrderItems": {"include": {"product": True}}, "supplier": True}
        return await self.prisma.purchaseorder.create(
            data={**po_data, "purchaseOrderItems": {"create": items_data}},
            include=include,
        )

    async def update_draft(self, po_id: str, po_data: dict, items_data: list[dict] | None):
        """Update PO fields and optionally replace items transactionally (draft only).

        When items_data is None, existing line items are preserved unchanged.
        When items_data is a list (including empty), all existing items are replaced.
        """
        include = {"purchaseOrderItems": {"include": {"product": True}}, "supplier": True}
        async with self.prisma.tx() as tx:
            if po_data:
                await tx.purchaseorder.update(where={"id": po_id}, data=po_data)
            if items_data is not None:
                await tx.purchaseorderitem.delete_many(where={"purchaseOrderId": po_id})
                for item in items_data:
                    await tx.purchaseorderitem.create(data={**item, "purchaseOrderId": po_id})
        return await self.prisma.purchaseorder.find_first(
            where={"id": po_id},
            include=include,
        )

    async def update_status(self, po_id: str, status: str):
        """Update only the status of a purchase order."""
        include = {"purchaseOrderItems": {"include": {"product": True}}, "supplier": True}
        return await self.prisma.purchaseorder.update(
            where={"id": po_id},
            data={"status": status},
            include=include,
        )

    async def soft_delete(self, po_id: str) -> None:
        """Set deletedAt to now, effectively removing the PO from active queries."""
        await self.prisma.purchaseorder.update(
            where={"id": po_id},
            data={"deletedAt": datetime.now(timezone.utc)},
        )

    async def find_item_by_id(self, item_id: str):
        """Return a single purchase order item by id."""
        return await self.prisma.purchaseorderitem.find_first(where={"id": item_id})

    async def find_product_by_id(self, product_id: str):
        """Return a non-deleted product by id."""
        return await self.prisma.product.find_first(
            where={"id": product_id, "deletedAt": None}
        )

    async def receive_items(
        self,
        po_id: str,
        item_updates: list[dict],   # [{item_id, new_received_qty}]
        stock_updates: list[dict],  # [{product_id, incoming_qty, stock_before, new_stock, performed_by}]
        new_po_status: str,
    ):
        """Atomically update received quantities, product stock, and PO status; create stock movements."""
        include = {"purchaseOrderItems": {"include": {"product": True}}, "supplier": True}
        async with self.prisma.tx() as tx:
            for upd in item_updates:
                await tx.purchaseorderitem.update(
                    where={"id": upd["item_id"]},
                    data={"receivedQuantity": upd["new_received_qty"]},
                )
            await tx.purchaseorder.update(
                where={"id": po_id},
                data={"status": new_po_status},
            )
            for su in stock_updates:
                await tx.product.update(
                    where={"id": su["product_id"]},
                    data={"stockQuantity": su["new_stock"]},
                )
                await tx.stockmovement.create(data={
                    "productId": su["product_id"],
                    "movementType": "in",
                    "quantity": su["incoming_qty"],
                    "stockBefore": su["stock_before"],
                    "stockAfter": su["new_stock"],
                    "referenceType": "purchase_order",
                    "referenceId": po_id,
                    "performedBy": su["performed_by"],
                })
        return await self.prisma.purchaseorder.find_first(
            where={"id": po_id},
            include=include,
        )
