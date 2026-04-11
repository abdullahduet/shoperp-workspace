# purchase_orders — Context

## Purpose
Manages the full purchase order lifecycle: draft → ordered → partially_received → received (or cancelled). Items track quantity and received quantity. On receive, stock movements are created and product stock is updated transactionally.

## Key Files
- schemas.py → POItemCreate, PurchaseOrderCreate, PurchaseOrderUpdate, ReceiveRequest, POItemResponse, PurchaseOrderResponse
- repository.py → DB queries; uses prisma.tx() for atomic operations (update_draft, receive_items)
- service.py → Business logic: list, get_by_id, create, update, delete, submit, receive, cancel
- controller.py → FastAPI handler functions; injects current_user for create and receive
- router.py → APIRouter with prefix=/purchase-orders; action routes (submit/receive/cancel) before bare /{po_id}

## Patterns
- model_validate overrides camelCase → snake_case mapping for Prisma objects
- orderDate and expectedDate are @db.Date → serialize with .isoformat()
- Nested include: {"purchaseOrderItems": {"include": {"product": True}}, "supplier": True}
- PO number format: PO-YYYYMMDD-NNN (sequential per day)
- Soft delete via `deletedAt` timestamp; only draft POs can be deleted

## Last Updated
2026-04-11 — initial implementation (task/0008)
