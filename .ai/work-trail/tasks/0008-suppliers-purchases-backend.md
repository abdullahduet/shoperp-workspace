# Task 0008: Suppliers + Purchases Backend

## Branch: task/0008-suppliers-purchases-backend
## Assigned to: engineer
## Status: not started

## Context Bundle

Everything you need is here. Do NOT read knowledge-base/ files directly.

### Relevant Schema (Prisma, camelCase in Python)

```prisma
model Supplier {
  id            String    @id @default(dbgenerated("gen_random_uuid()")) @db.Uuid
  name          String    @db.VarChar(255)
  contactPerson String?   @map("contact_person")
  phone         String?
  email         String?
  address       String?
  city          String?
  country       String?   @default("Bangladesh")
  paymentTerms  String?   @map("payment_terms")
  isActive      Boolean   @default(true)
  notes         String?
  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt
  deletedAt     DateTime?
  purchaseOrders PurchaseOrder[]
}

model PurchaseOrder {
  id           String    @id @default(dbgenerated("gen_random_uuid()")) @db.Uuid
  poNumber     String    @unique @map("po_number")
  supplierId   String    @map("supplier_id")
  orderDate    DateTime  @default(now()) @db.Date
  expectedDate DateTime? @db.Date
  status       String    @default("draft")  -- draft|ordered|partially_received|received|cancelled
  subtotal     Int       @default(0)
  taxAmount    Int       @default(0)
  totalAmount  Int       @default(0)
  notes        String?
  createdBy    String?
  createdAt    DateTime  @default(now())
  updatedAt    DateTime  @updatedAt
  deletedAt    DateTime?
  supplier           Supplier
  purchaseOrderItems PurchaseOrderItem[]
}

model PurchaseOrderItem {
  id               String   @id @default(dbgenerated("gen_random_uuid()")) @db.Uuid
  purchaseOrderId  String   @map("purchase_order_id")
  productId        String   @map("product_id")
  quantity         Int
  receivedQuantity Int      @default(0)
  unitCost         Int
  totalCost        Int
  createdAt        DateTime @default(now())
  updatedAt        DateTime @updatedAt
  purchaseOrder    PurchaseOrder
  product          Product
}
```

**Prisma model names in Python (lowercase, no underscores):**
- `prisma.supplier`
- `prisma.purchaseorder`
- `prisma.purchaseorderitem`
- `prisma.stockmovement`
- `prisma.product`

**All attribute access is camelCase:** `supplierId`, `poNumber`, `orderDate`, `expectedDate`, `taxAmount`, `totalAmount`, `createdBy`, `deletedAt`, `isActive`, `contactPerson`, `paymentTerms`, `purchaseOrderId`, `productId`, `receivedQuantity`, `unitCost`, `totalCost`, `stockQuantity`, `costPrice` etc.

### API Contract

```
# Suppliers
GET    /api/suppliers              → paginated list [all auth]
GET    /api/suppliers/:id          → detail [all auth]
POST   /api/suppliers              → create [admin, manager]
PUT    /api/suppliers/:id          → update [admin, manager]
DELETE /api/suppliers/:id          → soft delete [admin]
GET    /api/suppliers/:id/purchases → PO history (paginated) [admin, manager]

# Purchase Orders
GET    /api/purchase-orders              → paginated list [admin, manager]
GET    /api/purchase-orders/:id          → detail with items [admin, manager]
POST   /api/purchase-orders              → create draft [admin, manager]
PUT    /api/purchase-orders/:id          → update draft [admin, manager]
DELETE /api/purchase-orders/:id          → delete draft (only status=draft) [admin]
POST   /api/purchase-orders/:id/submit   → draft → ordered [admin, manager]
POST   /api/purchase-orders/:id/receive  → receive items, update stock [admin, manager]
POST   /api/purchase-orders/:id/cancel   → cancel (only draft or ordered) [admin]
```

**GET /suppliers query params:** `page`, `limit` (default 20), `search` (name), `is_active` (bool)

**GET /purchase-orders query params:** `page`, `limit` (default 20), `supplier_id`, `status`

**POST /purchase-orders body:**
```json
{
  "supplier_id": "uuid",
  "expected_date": "2026-05-01",   // optional ISO date
  "notes": "...",                   // optional
  "items": [
    { "product_id": "uuid", "quantity": 10, "unit_cost": 50000 }
  ]
}
```

**PUT /purchase-orders/:id body** — same as POST (only allowed if status=draft)

**POST /purchase-orders/:id/receive body:**
```json
{
  "items": [
    { "item_id": "purchase_order_item_uuid", "received_quantity": 5 }
  ]
}
```

### Response Shapes

**SupplierResponse:**
```python
id, name, contact_person, phone, email, address, city, country,
payment_terms, is_active, notes, created_at
```

**PurchaseOrderItemResponse:**
```python
id, purchase_order_id, product_id, product_name, product_sku,
quantity, received_quantity, unit_cost, total_cost
```

**PurchaseOrderResponse:**
```python
id, po_number, supplier_id, supplier_name, order_date, expected_date,
status, subtotal, tax_amount, total_amount, notes, created_by, created_at,
items: list[PurchaseOrderItemResponse]
```

### Business Logic (ALL in service layer)

**PO Number generation:** `PO-YYYYMMDD-NNN` where NNN is zero-padded sequential per day.
- Query: count today's POs, increment, format. E.g. `PO-20260411-001`
- In repository: `count_today_pos(date_str: str) -> int`

**Totals calculation** (service, NOT repository):
- `total_cost` per item = `quantity × unit_cost`
- `subtotal` = sum of all item `total_cost`
- `tax_amount` = 0 (no tax on POs per spec — keep field, set to 0)
- `total_amount` = `subtotal + tax_amount`

**Status transitions (service enforces all):**
- `submit`: only from `draft` → `ordered`; reject other statuses with ValidationError
- `receive`: only from `ordered` or `partially_received`; reject others
  - For each item in the receive request: `new_received = current_received + incoming`; cannot exceed item.quantity
  - After updating received quantities: if all items fully received → status = `received`; else → `partially_received`
  - For each item received: update `product.stockQuantity` += incoming qty; create `stock_movement` (type=`in`, referenceType=`purchase_order`, referenceId=po_id)
  - All of the above in ONE transaction (Rule #8)
- `cancel`: only from `draft` or `ordered`; reject others with ValidationError
- `delete`: only allowed if status = `draft`; reject if already submitted/received/cancelled

**Receiving transaction (repository method `receive_items`):**
```python
async def receive_items(
    self,
    po_id: str,
    item_updates: list[dict],   # [{item_id, incoming_qty, new_received_qty, new_status}]
    stock_updates: list[dict],  # [{product_id, new_stock, stock_before, performed_by}]
    new_po_status: str,
) -> PurchaseOrder:
    async with self.prisma.tx() as tx:
        # 1. Update each PO item receivedQuantity
        for upd in item_updates:
            await tx.purchaseorderitem.update(
                where={"id": upd["item_id"]},
                data={"receivedQuantity": upd["new_received_qty"]},
            )
        # 2. Update PO status
        await tx.purchaseorder.update(
            where={"id": po_id},
            data={"status": new_po_status},
        )
        # 3. Update each product stockQuantity + create stock movement
        for su in stock_updates:
            await tx.product.update(
                where={"id": su["product_id"]},
                data={"stockQuantity": su["new_stock"]},
            )
            await tx.stockmovement.create(
                data={
                    "productId": su["product_id"],
                    "movementType": "in",
                    "quantity": su["incoming_qty"],
                    "stockBefore": su["stock_before"],
                    "stockAfter": su["new_stock"],
                    "referenceType": "purchase_order",
                    "referenceId": po_id,
                    "performedBy": su["performed_by"],
                }
            )
        # 4. Return updated PO with items and supplier
        return await tx.purchaseorder.find_first(
            where={"id": po_id},
            include={"purchaseOrderItems": {"include": {"product": True}}, "supplier": True},
        )
```

### Architecture Rules That Apply

- Rule #2: Money as integers (unit_cost, total_cost, subtotal, tax_amount, total_amount in paisa)
- Rule #8: Receiving is ONE atomic transaction — PO item updates + PO status + product stock updates + stock movement creation
- Rule #9: Controllers — zero business logic
- Rule #10: Services — ALL business logic (PO number gen, totals, status transitions, stock deduction)
- Rule #11: Repositories — DB queries only (computation like totals goes in service)
- Rule #22: Every stock change creates a stock_movement record (receiving must create one per item)
- Rule #24: PO numbers are auto-generated and immutable after creation

## What to Build

### Module: Suppliers (`src/modules/suppliers/`)

**schemas.py:**
- `SupplierCreate`: name (required), contact_person, phone, email, address, city, country (default "Bangladesh"), payment_terms, notes (all Optional[str])
- `SupplierUpdate`: all Optional
- `SupplierResponse`: with model_validate mapping camelCase → snake_case

**service.py — SupplierService:**
- `list(page, limit, search, is_active) → PaginatedSuppliers`
- `get_by_id(id) → SupplierResponse` — NotFoundError if missing/deleted
- `create(input) → SupplierResponse`
- `update(id, input) → SupplierResponse` — NotFoundError; partial update (skip None fields)
- `delete(id) → None` — soft delete; NotFoundError

**repository.py — SupplierRepository:**
- `find_paginated(skip, take, where, order_by) → tuple[list, int]`
- `find_by_id(id) → Supplier | None` (where deletedAt=None)
- `create(data) → Supplier`
- `update(id, data) → Supplier`
- `soft_delete(id) → Supplier`

**router.py:**
```
GET    /suppliers               → list_suppliers          [all auth]
GET    /suppliers/{id}          → get_supplier            [all auth]
POST   /suppliers               → create_supplier         [admin, manager]
PUT    /suppliers/{id}          → update_supplier         [admin, manager]
DELETE /suppliers/{id}          → delete_supplier         [admin]
GET    /suppliers/{id}/purchases → get_supplier_purchases [admin, manager]
```
**IMPORTANT:** `/{id}/purchases` must come BEFORE `/{id}` — actually in FastAPI with different paths it's fine. Register `/{supplier_id}/purchases` as its own route.

The `get_supplier_purchases` controller function calls the PO service to get POs filtered by `supplier_id`. Wire it through the purchase order service (pass it as a dependency).

---

### Module: Purchase Orders (`src/modules/purchase_orders/`)

**Note:** Python module directory is `purchase_orders` (with underscore); router prefix is `/purchase-orders` (with hyphen).

**schemas.py:**
- `POItemCreate`: product_id (str), quantity (int > 0), unit_cost (int >= 0)
- `POItemUpdate`: product_id, quantity, unit_cost (all Optional)
- `PurchaseOrderCreate`: supplier_id (str), expected_date (Optional[str] ISO date), notes (Optional[str]), items (list[POItemCreate], min 1 item)
- `PurchaseOrderUpdate`: supplier_id, expected_date, notes, items — all Optional
- `ReceiveItemInput`: item_id (str), received_quantity (int > 0)
- `ReceiveRequest`: items (list[ReceiveItemInput], min 1)
- `POItemResponse`: id, purchase_order_id, product_id, product_name, product_sku, quantity, received_quantity, unit_cost, total_cost
- `PurchaseOrderResponse`: id, po_number, supplier_id, supplier_name, order_date, expected_date, status, subtotal, tax_amount, total_amount, notes, created_by, created_at, items: list[POItemResponse]
  - model_validate maps camelCase + includes supplier.name and items with product.name/sku

**service.py — PurchaseOrderService:**
- `list(page, limit, supplier_id, status) → PaginatedPOs`
- `get_by_id(id) → PurchaseOrderResponse` — includes items
- `create(input, created_by) → PurchaseOrderResponse`
  - Generate PO number: `PO-{YYYYMMDD}-{NNN:03d}`
  - Calculate totals (in service)
  - Create PO + items in one call (Prisma nested create)
- `update(id, input) → PurchaseOrderResponse`
  - Only allowed if status = `draft`; else ValidationError
  - Update PO fields + replace items (delete old items, create new ones) in transaction
- `delete(id) → None` — only if draft; else ValidationError
- `submit(id) → PurchaseOrderResponse` — draft → ordered
- `receive(id, items, performed_by) → PurchaseOrderResponse`
  - Validate status is ordered or partially_received
  - For each receive item: load current PO item, validate incoming qty doesn't exceed remaining
  - Determine new PO status
  - Call repo.receive_items with all updates in one transaction
- `cancel(id) → PurchaseOrderResponse` — only draft or ordered

**repository.py — PurchaseOrderRepository:**
- `find_paginated(skip, take, where) → tuple[list, int]` — include supplier + items + product
- `find_by_id(id) → PurchaseOrder | None` — include supplier + items + product
- `count_today_pos(date_str: str) → int` — count POs with poNumber LIKE `PO-{date_str}-%`
  Use: `where={"poNumber": {"startsWith": f"PO-{date_str}-"}}`
- `create_with_items(po_data, items_data) → PurchaseOrder` — Prisma nested create:
  ```python
  await self.prisma.purchaseorder.create(
      data={
          **po_data,
          "purchaseOrderItems": {"create": items_data},
      },
      include={"purchaseOrderItems": {"include": {"product": True}}, "supplier": True},
  )
  ```
- `update_draft(id, po_data, items_data) → PurchaseOrder` — transaction: delete items + update PO + create new items
- `update_status(id, status) → PurchaseOrder`
- `soft_delete(id) → PurchaseOrder`
- `receive_items(po_id, item_updates, stock_updates, new_po_status, performed_by) → PurchaseOrder` — atomic transaction (see pattern above)

**router.py — EXACT ORDER MATTERS:**
```python
router = APIRouter(prefix="/purchase-orders", tags=["purchase-orders"])
# Static paths FIRST
router.add_api_route("", list_pos, methods=["GET"], deps=[admin_manager])
router.add_api_route("", create_po, methods=["POST"], status_code=201, deps=[admin_manager])
# /:id/action paths BEFORE bare /:id GET
router.add_api_route("/{po_id}/submit", submit_po, methods=["POST"], deps=[admin_manager])
router.add_api_route("/{po_id}/receive", receive_po, methods=["POST"], deps=[admin_manager])
router.add_api_route("/{po_id}/cancel", cancel_po, methods=["POST"], deps=[admin])
router.add_api_route("/{po_id}", get_po, methods=["GET"], deps=[admin_manager])
router.add_api_route("/{po_id}", update_po, methods=["PUT"], deps=[admin_manager])
router.add_api_route("/{po_id}", delete_po, methods=["DELETE"], deps=[admin])
```

### Register routers in `main.py`

```python
from src.modules.suppliers.router import router as suppliers_router
from src.modules.purchase_orders.router import router as purchase_orders_router

app.include_router(suppliers_router, prefix="/api")
app.include_router(purchase_orders_router, prefix="/api")
```

### Tests

**Unit tests — mock repository:**

`tests/unit/modules/suppliers/test_service.py`:
- TestList: returns paginated suppliers
- TestGetById: happy path; NotFoundError if None
- TestCreate: creates supplier
- TestUpdate: happy path; NotFoundError
- TestDelete: happy path; NotFoundError

`tests/unit/modules/purchase_orders/test_service.py`:
- TestCreate: PO number generated as `PO-YYYYMMDD-001` when no prior POs today; items totals calculated correctly
- TestCreate: second PO same day gets `PO-YYYYMMDD-002`
- TestUpdate: succeeds for draft; ValidationError if status != draft
- TestDelete: succeeds for draft; ValidationError if status = ordered
- TestSubmit: draft→ordered; ValidationError if already ordered
- TestReceive: happy path — partial receive sets `partially_received`; full receive sets `received`; repo.receive_items called with correct stock_updates
- TestReceive: ValidationError if status = draft (not yet submitted)
- TestReceive: ValidationError if incoming_qty exceeds remaining (quantity - received_quantity)
- TestCancel: draft→cancelled; ordered→cancelled; ValidationError if received

`tests/integration/test_suppliers_api.py`:
- GET /api/suppliers → 200
- POST /api/suppliers with manager → 201; with staff → 403
- PUT /api/suppliers/:id → 200; 404 on missing
- DELETE /api/suppliers/:id with admin → 200; with manager → 403

`tests/integration/test_purchase_orders_api.py`:
- GET /api/purchase-orders → 200
- POST /api/purchase-orders with manager → 201
- POST /api/purchase-orders with staff → 403
- GET /api/purchase-orders/:id → 200; 404 on missing
- POST /api/purchase-orders/:id/submit → 200
- POST /api/purchase-orders/:id/receive → 200
- POST /api/purchase-orders/:id/cancel → 200 with admin; 403 with manager
- DELETE /api/purchase-orders/:id → 200 with admin (draft PO); 422 if not draft

## Acceptance Criteria

- [ ] Full CRUD for suppliers; search by name; filter by is_active
- [ ] GET /suppliers/:id/purchases returns supplier's PO list
- [ ] PO number auto-generated `PO-YYYYMMDD-NNN` and unique
- [ ] PO totals calculated in service: subtotal = sum(qty × unit_cost), total = subtotal
- [ ] POST /purchase-orders/:id/submit: draft → ordered; 422 otherwise
- [ ] POST /purchase-orders/:id/receive: updates received_qty per item, product stock, creates stock_movements, determines status — ALL in one transaction
- [ ] Partial receive → partially_received; full receive → received
- [ ] POST /purchase-orders/:id/cancel: draft/ordered → cancelled; 422 otherwise
- [ ] DELETE /purchase-orders/:id: only draft allowed
- [ ] pytest exits 0; ruff exits 0

## Known Pitfalls

- Prisma model name is `purchaseorder` (no underscore) and `purchaseorderitem` (no underscore)
- For `include` with nested relations: `include={"purchaseOrderItems": {"include": {"product": True}}, "supplier": True}`
- PO number collision: use `count_today_pos` + retry or just increment — sequential within a day is sufficient
- `update_draft`: must be a transaction — delete all existing items first (`deleteMany` where purchaseOrderId=id), then update PO fields, then create new items
- `receive_items` transaction: must loop through items, and for each calculate stock_before from the current product record (fetched before the tx begins in the service)
- The `performed_by` param must be threaded through from the current_user in the controller all the way to receive_items
- `orderDate` and `expectedDate` are `@db.Date` — use `date.today()` not `datetime.now()`
- In Prisma Python, `@db.Date` fields come back as `datetime.date` objects — serialize with `.isoformat()` in model_validate
- `status` values: exactly `draft`, `ordered`, `partially_received`, `received`, `cancelled`

## Exit Signal

```bash
cd /Users/abdullah/projects/shoperp-workspace/backend
python -m pytest tests/unit/modules/suppliers/ tests/unit/modules/purchase_orders/ \
  tests/integration/test_suppliers_api.py tests/integration/test_purchase_orders_api.py -v
ruff check src/modules/suppliers src/modules/purchase_orders
# Both exit 0
```

## Outcome (filled by Lead after merge)

_Not yet completed._
