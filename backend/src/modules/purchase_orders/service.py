"""Purchase orders service — ALL business logic for purchase order management."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.purchase_orders.repository import PurchaseOrderRepository
from src.modules.purchase_orders.schemas import (
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
    ReceiveRequest,
)


@dataclass
class PaginatedPOs:
    items: list[PurchaseOrderResponse]
    total: int


class PurchaseOrderService:
    def __init__(self, repo: PurchaseOrderRepository) -> None:
        self.repo = repo

    async def _generate_po_number(self) -> str:
        """Generate a unique PO number in the format PO-YYYYMMDD-NNN."""
        today_str = date.today().strftime("%Y%m%d")
        count = await self.repo.count_today_pos(today_str)
        return f"PO-{today_str}-{count + 1:03d}"

    async def list(
        self,
        page: int,
        limit: int,
        supplier_id: str | None,
        status: str | None,
    ) -> PaginatedPOs:
        """Return a paginated list of purchase orders with optional filters."""
        where: dict = {"deletedAt": None}
        if supplier_id:
            where["supplierId"] = supplier_id
        if status:
            where["status"] = status
        skip = (page - 1) * limit
        items, total = await self.repo.find_paginated(skip, limit, where)
        return PaginatedPOs(
            items=[PurchaseOrderResponse.model_validate(p) for p in items],
            total=total,
        )

    async def get_by_id(self, po_id: str) -> PurchaseOrderResponse:
        """Return a single purchase order or raise NotFoundError."""
        po = await self.repo.find_by_id(po_id)
        if po is None:
            raise NotFoundError("PurchaseOrder", po_id)
        return PurchaseOrderResponse.model_validate(po)

    async def create(self, input: PurchaseOrderCreate, created_by: str) -> PurchaseOrderResponse:
        """Create a new draft purchase order with items. Calculates totals."""
        po_number = await self._generate_po_number()

        items_data = []
        subtotal = 0
        for item in input.items:
            total_cost = item.quantity * item.unit_cost
            subtotal += total_cost
            items_data.append({
                "productId": item.product_id,
                "quantity": item.quantity,
                "unitCost": item.unit_cost,
                "totalCost": total_cost,
            })
        total_amount = subtotal  # tax = 0

        po_data: dict = {
            "poNumber": po_number,
            "supplierId": input.supplier_id,
            "status": "draft",
            "subtotal": subtotal,
            "taxAmount": 0,
            "totalAmount": total_amount,
            "createdBy": created_by,
        }
        if input.notes:
            po_data["notes"] = input.notes
        if input.expected_date:
            d = date.fromisoformat(input.expected_date)
            po_data["expectedDate"] = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)

        po = await self.repo.create_with_items(po_data, items_data)
        return PurchaseOrderResponse.model_validate(po)

    async def update(self, po_id: str, input: PurchaseOrderUpdate) -> PurchaseOrderResponse:
        """Update a draft purchase order. Raises ValidationError if not draft."""
        existing = await self.repo.find_by_id(po_id)
        if existing is None:
            raise NotFoundError("PurchaseOrder", po_id)
        if existing.status != "draft":
            raise ValidationError("Only draft purchase orders can be updated")

        po_data: dict = {}
        if input.supplier_id:
            po_data["supplierId"] = input.supplier_id
        if input.notes is not None:
            po_data["notes"] = input.notes
        if input.expected_date is not None:
            if input.expected_date:
                d = date.fromisoformat(input.expected_date)
                po_data["expectedDate"] = datetime(d.year, d.month, d.day, tzinfo=timezone.utc)
            else:
                po_data["expectedDate"] = None

        items_data = None
        if input.items is not None:
            items_data = []
            subtotal = 0
            for item in input.items:
                total_cost = item.quantity * item.unit_cost
                subtotal += total_cost
                items_data.append({
                    "productId": item.product_id,
                    "quantity": item.quantity,
                    "unitCost": item.unit_cost,
                    "totalCost": total_cost,
                })
            po_data["subtotal"] = subtotal
            po_data["totalAmount"] = subtotal

        po = await self.repo.update_draft(po_id, po_data, items_data)
        return PurchaseOrderResponse.model_validate(po)

    async def delete(self, po_id: str) -> None:
        """Soft-delete a draft purchase order. Raises ValidationError if not draft."""
        po = await self.repo.find_by_id(po_id)
        if po is None:
            raise NotFoundError("PurchaseOrder", po_id)
        if po.status != "draft":
            raise ValidationError("Only draft purchase orders can be deleted")
        await self.repo.soft_delete(po_id)

    async def submit(self, po_id: str) -> PurchaseOrderResponse:
        """Transition a draft purchase order to 'ordered' status."""
        po = await self.repo.find_by_id(po_id)
        if po is None:
            raise NotFoundError("PurchaseOrder", po_id)
        if po.status != "draft":
            raise ValidationError(f"Cannot submit purchase order with status '{po.status}'")
        po = await self.repo.update_status(po_id, "ordered")
        return PurchaseOrderResponse.model_validate(po)

    async def receive(
        self,
        po_id: str,
        receive_request: ReceiveRequest,
        performed_by: str,
    ) -> PurchaseOrderResponse:
        """Receive items on a purchase order. Updates stock and creates stock movements."""
        po = await self.repo.find_by_id(po_id)
        if po is None:
            raise NotFoundError("PurchaseOrder", po_id)
        if po.status not in ("ordered", "partially_received"):
            raise ValidationError(
                f"Cannot receive items for purchase order with status '{po.status}'"
            )

        # Index existing items by id
        existing_items = {item.id: item for item in po.purchaseOrderItems}

        item_updates = []
        stock_updates = []
        for receive_item in receive_request.items:
            existing = existing_items.get(receive_item.item_id)
            if existing is None:
                raise ValidationError(
                    f"Item {receive_item.item_id} not found in this purchase order"
                )
            remaining = existing.quantity - existing.receivedQuantity
            if receive_item.received_quantity > remaining:
                raise ValidationError(
                    f"Cannot receive {receive_item.received_quantity} units for item "
                    f"{receive_item.item_id}: only {remaining} remaining"
                )
            new_received = existing.receivedQuantity + receive_item.received_quantity
            item_updates.append({
                "item_id": receive_item.item_id,
                "new_received_qty": new_received,
            })

            # Get current product stock
            product = await self.repo.find_product_by_id(existing.productId)
            stock_before = product.stockQuantity if product else 0
            new_stock = stock_before + receive_item.received_quantity
            stock_updates.append({
                "product_id": existing.productId,
                "incoming_qty": receive_item.received_quantity,
                "stock_before": stock_before,
                "new_stock": new_stock,
                "performed_by": performed_by,
            })

        # Determine new PO status: check if fully received after this update
        updated_received = {u["item_id"]: u["new_received_qty"] for u in item_updates}
        all_received = all(
            updated_received.get(item.id, item.receivedQuantity) >= item.quantity
            for item in po.purchaseOrderItems
        )
        new_status = "received" if all_received else "partially_received"

        po = await self.repo.receive_items(po_id, item_updates, stock_updates, new_status)
        return PurchaseOrderResponse.model_validate(po)

    async def cancel(self, po_id: str) -> PurchaseOrderResponse:
        """Cancel a draft or ordered purchase order."""
        po = await self.repo.find_by_id(po_id)
        if po is None:
            raise NotFoundError("PurchaseOrder", po_id)
        if po.status not in ("draft", "ordered"):
            raise ValidationError(
                f"Cannot cancel purchase order with status '{po.status}'"
            )
        po = await self.repo.update_status(po_id, "cancelled")
        return PurchaseOrderResponse.model_validate(po)
