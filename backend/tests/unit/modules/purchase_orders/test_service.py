"""
Unit tests for src/modules/purchase_orders/service.py

All repository calls are mocked. Tests verify business logic only.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.purchase_orders.repository import PurchaseOrderRepository
from src.modules.purchase_orders.schemas import (
    POItemCreate,
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
    ReceiveItemInput,
    ReceiveRequest,
)
from src.modules.purchase_orders.service import PurchaseOrderService


def _make_fake_item(
    *,
    item_id: str = "item-uuid-1",
    po_id: str = "po-uuid-1",
    product_id: str = "prod-uuid-1",
    quantity: int = 10,
    received_quantity: int = 0,
    unit_cost: int = 500,
) -> MagicMock:
    """Create a MagicMock that mimics a Prisma PurchaseOrderItem model."""
    item = MagicMock()
    item.id = item_id
    item.purchaseOrderId = po_id
    item.productId = product_id
    item.quantity = quantity
    item.receivedQuantity = received_quantity
    item.unitCost = unit_cost
    item.totalCost = quantity * unit_cost
    product = MagicMock()
    product.name = "Test Product"
    product.sku = "SKU-001"
    item.product = product
    return item


def _make_fake_po(
    *,
    po_id: str = "po-uuid-1",
    status: str = "draft",
    items: list | None = None,
) -> MagicMock:
    """Create a MagicMock that mimics a Prisma PurchaseOrder model with relations."""
    po = MagicMock()
    po.id = po_id
    po.poNumber = "PO-20260411-001"
    po.supplierId = "supplier-uuid-1"
    po.status = status
    po.subtotal = 5000
    po.taxAmount = 0
    po.totalAmount = 5000
    po.createdBy = "user-uuid-1"
    po.orderDate = date.today()
    po.expectedDate = None
    po.createdAt = datetime(2026, 4, 11, tzinfo=timezone.utc)
    po.deletedAt = None
    po.notes = None
    supplier = MagicMock()
    supplier.name = "Test Supplier"
    po.supplier = supplier
    po.purchaseOrderItems = items if items is not None else [_make_fake_item(po_id=po_id)]
    return po


def _make_service() -> tuple[PurchaseOrderService, AsyncMock]:
    repo = AsyncMock(spec=PurchaseOrderRepository)
    service = PurchaseOrderService(repo)
    return service, repo


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

class TestCreate:
    @pytest.mark.asyncio
    async def test_generates_po_number_with_correct_format(self):
        service, repo = _make_service()
        fake_po = _make_fake_po()
        repo.count_today_pos.return_value = 0
        repo.create_with_items.return_value = fake_po

        today_str = date.today().strftime("%Y%m%d")
        await service.create(
            PurchaseOrderCreate(
                supplier_id="supplier-uuid-1",
                items=[POItemCreate(product_id="prod-uuid-1", quantity=5, unit_cost=1000)],
            ),
            created_by="user-uuid-1",
        )

        call_args = repo.create_with_items.call_args.args
        po_data = call_args[0]
        assert po_data["poNumber"] == f"PO-{today_str}-001"

    @pytest.mark.asyncio
    async def test_calculates_totals_correctly(self):
        service, repo = _make_service()
        fake_po = _make_fake_po()
        repo.count_today_pos.return_value = 0
        repo.create_with_items.return_value = fake_po

        await service.create(
            PurchaseOrderCreate(
                supplier_id="supplier-uuid-1",
                items=[
                    POItemCreate(product_id="prod-1", quantity=5, unit_cost=1000),
                    POItemCreate(product_id="prod-2", quantity=2, unit_cost=2000),
                ],
            ),
            created_by="user-uuid-1",
        )

        call_args = repo.create_with_items.call_args.args
        po_data = call_args[0]
        items_data = call_args[1]
        # subtotal = 5*1000 + 2*2000 = 5000 + 4000 = 9000
        assert po_data["subtotal"] == 9000
        assert po_data["totalAmount"] == 9000
        assert items_data[0]["totalCost"] == 5000
        assert items_data[1]["totalCost"] == 4000

    @pytest.mark.asyncio
    async def test_returns_purchase_order_response(self):
        service, repo = _make_service()
        fake_po = _make_fake_po()
        repo.count_today_pos.return_value = 0
        repo.create_with_items.return_value = fake_po

        result = await service.create(
            PurchaseOrderCreate(
                supplier_id="supplier-uuid-1",
                items=[POItemCreate(product_id="prod-1", quantity=1, unit_cost=500)],
            ),
            created_by="user-uuid-1",
        )

        assert isinstance(result, PurchaseOrderResponse)


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

class TestUpdate:
    @pytest.mark.asyncio
    async def test_updates_draft_po_successfully(self):
        service, repo = _make_service()
        fake_po = _make_fake_po(status="draft")
        updated_po = _make_fake_po(status="draft")
        repo.find_by_id.return_value = fake_po
        repo.update_draft.return_value = updated_po

        result = await service.update("po-uuid-1", PurchaseOrderUpdate(notes="Updated notes"))

        assert isinstance(result, PurchaseOrderResponse)
        repo.update_draft.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_validation_error_for_ordered_status(self):
        service, repo = _make_service()
        fake_po = _make_fake_po(status="ordered")
        repo.find_by_id.return_value = fake_po

        with pytest.raises(ValidationError):
            await service.update("po-uuid-1", PurchaseOrderUpdate(notes="Too late"))

    @pytest.mark.asyncio
    async def test_raises_not_found_when_po_missing(self):
        service, repo = _make_service()
        repo.find_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.update("nonexistent-id", PurchaseOrderUpdate())

    @pytest.mark.asyncio
    async def test_update_without_items_preserves_existing_items(self):
        service, repo = _make_service()
        fake_po = _make_fake_po(status="draft")
        repo.find_by_id.return_value = fake_po
        repo.update_draft.return_value = fake_po

        await service.update(fake_po.id, PurchaseOrderUpdate(notes="updated note"))

        # items_data should be None — not [] — so existing items are NOT wiped
        call_args = repo.update_draft.call_args
        assert call_args.kwargs.get("items_data") is None or call_args.args[2] is None


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

class TestDelete:
    @pytest.mark.asyncio
    async def test_soft_deletes_draft_po(self):
        service, repo = _make_service()
        fake_po = _make_fake_po(status="draft")
        repo.find_by_id.return_value = fake_po

        await service.delete("po-uuid-1")

        repo.soft_delete.assert_awaited_once_with("po-uuid-1")

    @pytest.mark.asyncio
    async def test_raises_validation_error_for_ordered_status(self):
        service, repo = _make_service()
        fake_po = _make_fake_po(status="ordered")
        repo.find_by_id.return_value = fake_po

        with pytest.raises(ValidationError):
            await service.delete("po-uuid-1")

    @pytest.mark.asyncio
    async def test_raises_not_found_when_po_missing(self):
        service, repo = _make_service()
        repo.find_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.delete("nonexistent-id")


# ---------------------------------------------------------------------------
# submit
# ---------------------------------------------------------------------------

class TestSubmit:
    @pytest.mark.asyncio
    async def test_transitions_draft_to_ordered(self):
        service, repo = _make_service()
        fake_po = _make_fake_po(status="draft")
        ordered_po = _make_fake_po(status="ordered")
        repo.find_by_id.return_value = fake_po
        repo.update_status.return_value = ordered_po

        result = await service.submit("po-uuid-1")

        repo.update_status.assert_awaited_once_with("po-uuid-1", "ordered")
        assert isinstance(result, PurchaseOrderResponse)

    @pytest.mark.asyncio
    async def test_raises_validation_error_if_already_ordered(self):
        service, repo = _make_service()
        fake_po = _make_fake_po(status="ordered")
        repo.find_by_id.return_value = fake_po

        with pytest.raises(ValidationError):
            await service.submit("po-uuid-1")

    @pytest.mark.asyncio
    async def test_raises_not_found_when_po_missing(self):
        service, repo = _make_service()
        repo.find_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.submit("nonexistent-id")


# ---------------------------------------------------------------------------
# receive
# ---------------------------------------------------------------------------

class TestReceive:
    @pytest.mark.asyncio
    async def test_partial_receive_sets_partially_received_status(self):
        service, repo = _make_service()
        item = _make_fake_item(quantity=10, received_quantity=0)
        fake_po = _make_fake_po(status="ordered", items=[item])
        received_po = _make_fake_po(status="partially_received", items=[item])
        repo.find_by_id.return_value = fake_po
        product = MagicMock()
        product.stockQuantity = 20
        repo.find_product_by_id.return_value = product
        repo.receive_items.return_value = received_po

        result = await service.receive(
            "po-uuid-1",
            ReceiveRequest(items=[ReceiveItemInput(item_id="item-uuid-1", received_quantity=5)]),
            performed_by="user-uuid-1",
        )

        call_args = repo.receive_items.call_args.args
        assert call_args[3] == "partially_received"
        assert isinstance(result, PurchaseOrderResponse)

    @pytest.mark.asyncio
    async def test_full_receive_sets_received_status(self):
        service, repo = _make_service()
        item = _make_fake_item(quantity=10, received_quantity=0)
        fake_po = _make_fake_po(status="ordered", items=[item])
        received_po = _make_fake_po(status="received", items=[item])
        repo.find_by_id.return_value = fake_po
        product = MagicMock()
        product.stockQuantity = 20
        repo.find_product_by_id.return_value = product
        repo.receive_items.return_value = received_po

        await service.receive(
            "po-uuid-1",
            ReceiveRequest(items=[ReceiveItemInput(item_id="item-uuid-1", received_quantity=10)]),
            performed_by="user-uuid-1",
        )

        call_args = repo.receive_items.call_args.args
        assert call_args[3] == "received"

    @pytest.mark.asyncio
    async def test_raises_validation_error_if_status_is_draft(self):
        service, repo = _make_service()
        fake_po = _make_fake_po(status="draft")
        repo.find_by_id.return_value = fake_po

        with pytest.raises(ValidationError):
            await service.receive(
                "po-uuid-1",
                ReceiveRequest(items=[ReceiveItemInput(item_id="item-uuid-1", received_quantity=1)]),
                performed_by="user-uuid-1",
            )

    @pytest.mark.asyncio
    async def test_raises_validation_error_if_incoming_qty_exceeds_remaining(self):
        service, repo = _make_service()
        item = _make_fake_item(quantity=10, received_quantity=8)
        fake_po = _make_fake_po(status="ordered", items=[item])
        repo.find_by_id.return_value = fake_po

        with pytest.raises(ValidationError):
            await service.receive(
                "po-uuid-1",
                ReceiveRequest(items=[ReceiveItemInput(item_id="item-uuid-1", received_quantity=5)]),
                performed_by="user-uuid-1",
            )


# ---------------------------------------------------------------------------
# cancel
# ---------------------------------------------------------------------------

class TestCancel:
    @pytest.mark.asyncio
    async def test_cancels_draft_po(self):
        service, repo = _make_service()
        fake_po = _make_fake_po(status="draft")
        cancelled_po = _make_fake_po(status="cancelled")
        repo.find_by_id.return_value = fake_po
        repo.update_status.return_value = cancelled_po

        result = await service.cancel("po-uuid-1")

        repo.update_status.assert_awaited_once_with("po-uuid-1", "cancelled")
        assert isinstance(result, PurchaseOrderResponse)

    @pytest.mark.asyncio
    async def test_cancels_ordered_po(self):
        service, repo = _make_service()
        fake_po = _make_fake_po(status="ordered")
        cancelled_po = _make_fake_po(status="cancelled")
        repo.find_by_id.return_value = fake_po
        repo.update_status.return_value = cancelled_po

        await service.cancel("po-uuid-1")

        repo.update_status.assert_awaited_once_with("po-uuid-1", "cancelled")

    @pytest.mark.asyncio
    async def test_raises_validation_error_if_already_received(self):
        service, repo = _make_service()
        fake_po = _make_fake_po(status="received")
        repo.find_by_id.return_value = fake_po

        with pytest.raises(ValidationError):
            await service.cancel("po-uuid-1")

    @pytest.mark.asyncio
    async def test_raises_not_found_when_po_missing(self):
        service, repo = _make_service()
        repo.find_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.cancel("nonexistent-id")
