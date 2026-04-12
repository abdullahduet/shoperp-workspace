# Task 0012: Sales Recording Backend

## Branch: task/0012-sales-backend

## Context Bundle

### Relevant Schema (Sales, SaleItem, Account, JournalEntry, JournalEntryLine)

```prisma
model Sale {
  id             String    @id @default(dbgenerated("gen_random_uuid()")) @db.Uuid
  saleNumber     String    @unique @map("sale_number") @db.VarChar(50)
  saleDate       DateTime  @default(now()) @map("sale_date") @db.Timestamptz()
  customerName   String?   @map("customer_name") @db.VarChar(255)
  subtotal       Int       @default(0)
  discountAmount Int       @default(0) @map("discount_amount")
  taxAmount      Int       @default(0) @map("tax_amount")
  totalAmount    Int       @default(0) @map("total_amount")
  paymentMethod  String    @default("cash") @map("payment_method") @db.VarChar(20)
  promotionId    String?   @map("promotion_id") @db.Uuid
  notes          String?   @db.Text
  recordedBy     String?   @map("recorded_by") @db.Uuid
  createdAt      DateTime  @default(now()) @map("created_at") @db.Timestamptz()
  updatedAt      DateTime  @updatedAt @map("updated_at") @db.Timestamptz()
  deletedAt      DateTime? @map("deleted_at") @db.Timestamptz()

  promotion      Promotion? @relation(fields: [promotionId], references: [id])
  recordedByUser User?      @relation(fields: [recordedBy], references: [id])
  saleItems      SaleItem[]

  @@index([saleDate], name: "idx_sales_date")
  @@index([paymentMethod], name: "idx_sales_payment")
  @@map("sales")
}

model SaleItem {
  id         String   @id @default(dbgenerated("gen_random_uuid()")) @db.Uuid
  saleId     String   @map("sale_id") @db.Uuid
  productId  String   @map("product_id") @db.Uuid
  quantity   Int
  unitPrice  Int      @map("unit_price")
  discount   Int      @default(0)     -- per-item discount (always 0; promotion discount is at sale level)
  totalPrice Int      @map("total_price")
  createdAt  DateTime @default(now()) @map("created_at") @db.Timestamptz()

  sale    Sale    @relation(fields: [saleId], references: [id], onDelete: Cascade)
  product Product @relation(fields: [productId], references: [id])

  @@index([saleId], name: "idx_si_sale")
  @@map("sale_items")
}

model Account {
  code      String    @unique @db.VarChar(20)
  -- Seeded codes used by sales: "1000" (Cash), "4000" (Sales Revenue)
  @@map("accounts")
}

model JournalEntry {
  id            String   @id @default(dbgenerated("gen_random_uuid()")) @db.Uuid
  entryNumber   String   @unique @map("entry_number") @db.VarChar(50)
  date          DateTime @default(now()) @db.Date
  description   String   @db.Text
  referenceType String?  @map("reference_type") @db.VarChar(50)
  referenceId   String?  @map("reference_id") @db.Uuid
  createdBy     String?  @map("created_by") @db.Uuid
  createdAt     DateTime @default(now()) @map("created_at") @db.Timestamptz()

  journalEntryLines JournalEntryLine[]
  @@map("journal_entries")
}

model JournalEntryLine {
  id             String  @id @default(dbgenerated("gen_random_uuid()")) @db.Uuid
  journalEntryId String  @map("journal_entry_id") @db.Uuid
  accountId      String  @map("account_id") @db.Uuid
  debitAmount    Int     @default(0) @map("debit_amount")
  creditAmount   Int     @default(0) @map("credit_amount")
  description    String? @db.Text

  journalEntry JournalEntry @relation(fields: [journalEntryId], references: [id], onDelete: Cascade)
  account      Account      @relation(fields: [accountId], references: [id])

  @@map("journal_entry_lines")
}
```

**Prisma client model names (lowercase, no underscores):**
- `prisma.sale`, `prisma.saleitem`, `prisma.product`, `prisma.stockmovement`
- `prisma.account`, `prisma.journalentry`, `prisma.journalentryline`

**Prisma attribute mapping (Python access uses camelCase):**
- `sale.saleNumber`, `sale.saleDate`, `sale.customerName`, `sale.discountAmount`, `sale.taxAmount`, `sale.totalAmount`, `sale.paymentMethod`, `sale.promotionId`, `sale.recordedBy`
- `sale.saleItems` — relation include
- `saleItem.saleId`, `saleItem.productId`, `saleItem.unitPrice`, `saleItem.totalPrice`
- `product.stockQuantity`, `product.taxRate` (Decimal type — use `float(product.taxRate)`)
- `product.isActive`, `product.deletedAt`

**Seeded account codes:**
- `"1000"` → Cash (asset)
- `"4000"` → Sales Revenue (revenue)

### Relevant API Endpoints

**Prefix: `/api/sales`**

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| GET | `/api/sales` | Yes | all | Paginated list. Params: `page`, `limit`, `start_date` (YYYY-MM-DD), `end_date`, `payment_method` |
| GET | `/api/sales/daily-summary` | Yes | admin, manager | Today's totals — MUST be registered BEFORE `/{sale_id}` |
| GET | `/api/sales/{sale_id}` | Yes | all | Sale detail with items |
| POST | `/api/sales` | Yes | all | Record a sale atomically |

**POST /api/sales request body:**
```json
{
  "items": [
    {"product_id": "uuid", "quantity": 2, "unit_price": 50000}
  ],
  "payment_method": "cash",        // optional, default "cash" — cash/card/mobile/credit
  "customer_name": "John Doe",     // optional
  "notes": "walk-in customer"      // optional
}
```
Note: `promotion_id` is NOT sent by the client. The server auto-selects the best active promotion.

**POST /api/sales response (201):**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "sale_number": "SALE-20260411-001",
    "sale_date": "2026-04-11T10:00:00+00:00",
    "customer_name": null,
    "subtotal": 100000,
    "discount_amount": 20000,
    "tax_amount": 5000,
    "total_amount": 85000,
    "payment_method": "cash",
    "promotion_id": "promo-uuid-or-null",
    "notes": null,
    "recorded_by": "user-uuid",
    "items": [
      {"id": "uuid", "product_id": "uuid", "quantity": 2, "unit_price": 50000, "discount": 0, "total_price": 100000, "created_at": "..."}
    ],
    "created_at": "..."
  },
  "message": "Sale recorded successfully"
}
```

**GET /api/sales/daily-summary response (200):**
```json
{
  "success": true,
  "data": {
    "date": "2026-04-11",
    "total_sales": 350000,
    "transaction_count": 5,
    "payment_breakdown": {"cash": 200000, "card": 100000, "mobile": 50000, "credit": 0}
  }
}
```

**GET /api/sales response (200):**
```json
{
  "success": true,
  "data": [...],
  "pagination": {"page": 1, "limit": 20, "total": 42, "pages": 3}
}
```

### Relevant Patterns

**Module structure (follow exactly):**
```
backend/src/modules/sales/
├── __init__.py
├── schemas.py
├── repository.py
├── service.py
├── controller.py
├── router.py
└── CONTEXT.md
```

**Standard response helpers:**
```python
from src.core.responses import success_response, paginated_response, error_response
# success_response(data, message, status_code=200)
# paginated_response(data, page, limit, total)
```

**Auth dependency:**
```python
from src.core.auth import get_current_user, require_roles
from fastapi import Depends
# current_user: User = Depends(get_current_user)
# require_roles("admin", "manager"): Depends(require_roles("admin", "manager"))
```

**Router registration (add_api_route style — match existing modules):**
```python
from fastapi import APIRouter
router = APIRouter(prefix="/sales", tags=["sales"])

# CRITICAL: /daily-summary BEFORE /{sale_id}
router.add_api_route("/daily-summary", controller.get_daily_summary, methods=["GET"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/{sale_id}", controller.get_sale, methods=["GET"],
                     dependencies=[Depends(get_current_user)])
```

**Transaction pattern (from purchase_orders/repository.py — identical pattern):**
```python
async with self.prisma.tx() as tx:
    sale = await tx.sale.create(data={...})
    await tx.saleitem.create(data={...})
    await tx.product.update(where={"id": product_id}, data={"stockQuantity": new_stock})
    await tx.stockmovement.create(data={...})
    entry = await tx.journalentry.create(data={...})
    await tx.journalentryline.create(data={"journalEntryId": entry.id, ...})
    await tx.journalentryline.create(data={"journalEntryId": entry.id, ...})
# After tx: fresh find_first with includes
return await self.prisma.sale.find_first(
    where={"id": sale.id},
    include={"saleItems": True},
)
```

**Cross-module import (service-to-service, Rule #25):**
```python
# In sales/service.py — import promotion service, NOT promotion repository
from src.modules.promotions.service import PromotionService
from src.modules.promotions.repository import PromotionRepository

class SalesService:
    def __init__(self, repo: SalesRepository, promotion_service: PromotionService) -> None:
        self.repo = repo
        self.promotion_service = promotion_service
```

**Controller wires up both services:**
```python
# In sales/controller.py
from src.modules.sales.repository import SalesRepository
from src.modules.sales.service import SalesService
from src.modules.promotions.repository import PromotionRepository
from src.modules.promotions.service import PromotionService
from src import database

async def record_sale(input: SaleCreate, current_user=Depends(get_current_user)):
    db = database.get_db()
    promotion_repo = PromotionRepository(db)
    promotion_service = PromotionService(promotion_repo)
    repo = SalesRepository(db)
    service = SalesService(repo, promotion_service)
    result = await service.record_sale(input, recorded_by=current_user.id)
    return success_response(result, "Sale recorded successfully", 201)
```

**Existing file to modify — promotions/service.py:**
Add this method to `PromotionService` (after `delete`):
```python
async def get_best_discount(
    self,
    subtotal: int,
    items: list[dict],
) -> tuple[str | None, int]:
    """Find the best active promotion. Returns (promotion_id, discount_amount).
    Returns (None, 0) if no promotion applies or gives discount > 0.
    Items must be: [{"product_id": str, "quantity": int, "unit_price": int}]
    """
    now = datetime.now(timezone.utc)
    promotions = await self.repo.find_active(now)
    best_id: str | None = None
    best_discount = 0
    for promo in promotions:
        discount = self.calculate_discount(promo, subtotal, items)
        if discount > best_discount:
            best_discount = discount
            best_id = promo.id
    return best_id, best_discount
```

**Number generation (sale number, match PO number pattern):**
```python
async def _generate_sale_number(self) -> str:
    from datetime import date
    today_str = date.today().strftime("%Y%m%d")
    count = await self.repo.count_today_sales(today_str)
    return f"SALE-{today_str}-{count + 1:03d}"
```

Repository method:
```python
async def count_today_sales(self, today_str: str) -> int:
    return await self.prisma.sale.count(
        where={"saleNumber": {"startswith": f"SALE-{today_str}"}}
    )
```

**Journal entry number generation:**
```python
async def _generate_entry_number(self) -> str:
    from datetime import date
    today_str = date.today().strftime("%Y%m%d")
    count = await self.repo.count_today_journal_entries(today_str)
    return f"JE-{today_str}-{count + 1:03d}"
```

Repository method:
```python
async def count_today_journal_entries(self, today_str: str) -> int:
    return await self.prisma.journalentry.count(
        where={"entryNumber": {"startswith": f"JE-{today_str}"}}
    )
```

**Daily summary query:**
```python
# In repository — just raw DB queries, no calculations
async def find_today_sales(self, today_start: datetime, today_end: datetime) -> list:
    return await self.prisma.sale.find_many(
        where={
            "deletedAt": None,
            "saleDate": {"gte": today_start, "lt": today_end},
        }
    )

# In service — all calculations
async def get_daily_summary(self) -> DailySummaryResponse:
    today = date.today()
    today_start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
    today_end = today_start + timedelta(days=1)
    sales = await self.repo.find_today_sales(today_start, today_end)
    total_sales = sum(s.totalAmount for s in sales)
    transaction_count = len(sales)
    payment_breakdown = {"cash": 0, "card": 0, "mobile": 0, "credit": 0}
    for s in sales:
        method = s.paymentMethod if s.paymentMethod in payment_breakdown else "cash"
        payment_breakdown[method] += s.totalAmount
    return DailySummaryResponse(
        date=today.isoformat(),
        total_sales=total_sales,
        transaction_count=transaction_count,
        payment_breakdown=payment_breakdown,
    )
```

**Stock movement for sales (movementType="out"):**
```python
await tx.stockmovement.create(data={
    "productId": product_id,
    "movementType": "out",
    "quantity": quantity,
    "stockBefore": stock_before,
    "stockAfter": stock_before - quantity,
    "referenceType": "sale",
    "referenceId": sale.id,
    "performedBy": recorded_by,
})
```

### Architecture Rules That Apply

- Rule #8: Cross-table mutations use `async with self.prisma.tx() as tx`. The sale transaction covers: sale + sale_items + stock updates + stock_movements + journal entry + journal entry lines.
- Rule #11: Repositories contain ONLY DB queries. Tax computation, discount selection, total calculations go in service.
- Rule #13: Typed exceptions — `NotFoundError`, `ValidationError`.
- Rule #22: Every stock change creates a stock_movement record. Sales deduct stock → must create stock_movement per item with movementType="out".
- Rule #23: Sale recording is atomic — entire transaction rolls back if any step fails.
- Rule #25: No cross-module repository imports. SalesService imports PromotionService, not PromotionRepository directly.

## What to Build

### 1. `backend/src/modules/promotions/service.py` — ADD METHOD

Add `get_best_discount(subtotal, items)` method to the existing `PromotionService` class. Do NOT remove or change any existing methods. This is the only change to the promotions module.

### 2. `backend/src/modules/sales/schemas.py`

```python
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal

PaymentMethod = Literal["cash", "card", "mobile", "credit"]

class SaleItemCreate(BaseModel):
    product_id: str
    quantity: int = Field(gt=0)
    unit_price: int = Field(ge=0)  # paisa

class SaleCreate(BaseModel):
    items: list[SaleItemCreate] = Field(min_length=1)
    payment_method: PaymentMethod = "cash"
    customer_name: str | None = None
    notes: str | None = None

class SaleItemResponse(BaseModel):
    id: str
    product_id: str
    quantity: int
    unit_price: int
    discount: int
    total_price: int
    created_at: str

    @classmethod
    def model_validate(cls, obj):
        return cls(
            id=obj.id,
            product_id=obj.productId,
            quantity=obj.quantity,
            unit_price=obj.unitPrice,
            discount=obj.discount,
            total_price=obj.totalPrice,
            created_at=obj.createdAt.isoformat(),
        )

class SaleResponse(BaseModel):
    id: str
    sale_number: str
    sale_date: str
    customer_name: str | None
    subtotal: int
    discount_amount: int
    tax_amount: int
    total_amount: int
    payment_method: str
    promotion_id: str | None
    notes: str | None
    recorded_by: str | None
    items: list[SaleItemResponse]
    created_at: str

    @classmethod
    def model_validate(cls, obj):
        return cls(
            id=obj.id,
            sale_number=obj.saleNumber,
            sale_date=obj.saleDate.isoformat(),
            customer_name=obj.customerName,
            subtotal=obj.subtotal,
            discount_amount=obj.discountAmount,
            tax_amount=obj.taxAmount,
            total_amount=obj.totalAmount,
            payment_method=obj.paymentMethod,
            promotion_id=obj.promotionId,
            notes=obj.notes,
            recorded_by=obj.recordedBy,
            items=[SaleItemResponse.model_validate(i) for i in (obj.saleItems or [])],
            created_at=obj.createdAt.isoformat(),
        )

class DailySummaryResponse(BaseModel):
    date: str
    total_sales: int
    transaction_count: int
    payment_breakdown: dict[str, int]
```

### 3. `backend/src/modules/sales/repository.py`

Methods (DB queries only — no calculations):
- `find_by_id(sale_id: str)` → Sale with `saleItems` included, `deletedAt=None` guard
- `find_paginated(skip, take, where)` → `(list[Sale], int)` — include saleItems
- `count_today_sales(today_str: str)` → int (for number generation)
- `count_today_journal_entries(today_str: str)` → int (for JE number generation)
- `find_product_by_id(product_id: str)` → Product (for validation + tax rate)
- `find_account_by_code(code: str)` → Account
- `find_today_sales(today_start, today_end)` → list[Sale] (no saleItems needed)
- `create_sale_atomic(sale_data, items_data, stock_updates, journal_data) → Sale` — THE TRANSACTION

`create_sale_atomic` signature and implementation:
```python
async def create_sale_atomic(
    self,
    sale_data: dict,           # all sale fields
    items_data: list[dict],    # [{productId, quantity, unitPrice, discount, totalPrice}]
    stock_updates: list[dict], # [{product_id, qty, stock_before, stock_after, performed_by, sale_id}]
    journal_data: dict,        # {entry_number, description, reference_id, created_by, debit_account_id, credit_account_id, amount}
):
    async with self.prisma.tx() as tx:
        sale = await tx.sale.create(data=sale_data)
        for item in items_data:
            await tx.saleitem.create(data={"saleId": sale.id, **item})
        for su in stock_updates:
            await tx.product.update(
                where={"id": su["product_id"]},
                data={"stockQuantity": su["stock_after"]},
            )
            await tx.stockmovement.create(data={
                "productId": su["product_id"],
                "movementType": "out",
                "quantity": su["qty"],
                "stockBefore": su["stock_before"],
                "stockAfter": su["stock_after"],
                "referenceType": "sale",
                "referenceId": su["sale_id_placeholder"],  # we use sale.id below
                "performedBy": su["performed_by"],
            })
        entry = await tx.journalentry.create(data={
            "entryNumber": journal_data["entry_number"],
            "description": journal_data["description"],
            "referenceType": "sale",
            "referenceId": journal_data["reference_id"],
            "createdBy": journal_data["created_by"],
        })
        await tx.journalentryline.create(data={
            "journalEntryId": entry.id,
            "accountId": journal_data["debit_account_id"],
            "debitAmount": journal_data["amount"],
            "creditAmount": 0,
            "description": "Cash received",
        })
        await tx.journalentryline.create(data={
            "journalEntryId": entry.id,
            "accountId": journal_data["credit_account_id"],
            "debitAmount": 0,
            "creditAmount": journal_data["amount"],
            "description": "Sales revenue",
        })
    return await self.prisma.sale.find_first(
        where={"id": sale.id},
        include={"saleItems": True},
    )
```

**Important note on stock movements referenceId:** The `referenceId` for stock movements must be the sale's `id`. But when inside the transaction, `sale.id` is available immediately after `tx.sale.create(data=...)` — use `sale.id` directly in the stock movement creates. Remove `su["sale_id_placeholder"]` from the stock_updates dict and instead pass `sale.id` directly:

```python
for su in stock_updates:
    await tx.product.update(
        where={"id": su["product_id"]},
        data={"stockQuantity": su["stock_after"]},
    )
    await tx.stockmovement.create(data={
        "productId": su["product_id"],
        "movementType": "out",
        "quantity": su["qty"],
        "stockBefore": su["stock_before"],
        "stockAfter": su["stock_after"],
        "referenceType": "sale",
        "referenceId": sale.id,   # sale.id is available here
        "performedBy": su["performed_by"],
    })
```

### 4. `backend/src/modules/sales/service.py`

```python
@dataclass
class PaginatedSales:
    items: list[SaleResponse]
    total: int

class SalesService:
    def __init__(self, repo: SalesRepository, promotion_service: PromotionService) -> None:
        self.repo = repo
        self.promotion_service = promotion_service
```

Service methods:
- `list(page, limit, start_date, end_date, payment_method)` → `PaginatedSales`
- `get_by_id(sale_id)` → `SaleResponse` (raises NotFoundError if not found)
- `get_daily_summary()` → `DailySummaryResponse`
- `record_sale(input: SaleCreate, recorded_by: str)` → `SaleResponse`

`record_sale` logic:
1. Validate each item's product exists, is active, has sufficient stock
2. Compute `subtotal = sum(item.quantity * item.unit_price for item in input.items)`
3. Build `items_for_discount = [{"product_id": i.product_id, "quantity": i.quantity, "unit_price": i.unit_price} for i in input.items]`
4. Call `promotion_id, discount_amount = await self.promotion_service.get_best_discount(subtotal, items_for_discount)`
5. Load products again (or cache from step 1) to compute tax:
   `tax_amount = sum(int(item.quantity * item.unit_price * float(product.taxRate) / 100) for each item + product pair)`
6. `total_amount = subtotal - discount_amount + tax_amount`
7. Generate sale number: `sale_number = await self._generate_sale_number()`
8. Generate journal entry number: `entry_number = await self._generate_entry_number()`
9. Look up accounts: `cash_account = await self.repo.find_account_by_code("1000")`, `revenue_account = await self.repo.find_account_by_code("4000")`
10. Build all data structures for the atomic transaction
11. Call `sale = await self.repo.create_sale_atomic(sale_data, items_data, stock_updates, journal_data)`
12. Return `SaleResponse.model_validate(sale)`

**Validation rules:**
- Each product must exist (not None, deletedAt is None)
- Each product must be active (`isActive == True`)
- Each product must have sufficient stock (`stockQuantity >= item.quantity`)
- If any product fails → raise `ValidationError` with descriptive message
- If account "1000" or "4000" not found → raise `ValidationError("Chart of accounts not seeded")`

**Build stock_updates in service (no arithmetic in repo):**
```python
stock_updates = []
for item, product in zip(input.items, products):
    stock_before = product.stockQuantity
    stock_after = stock_before - item.quantity
    stock_updates.append({
        "product_id": item.product_id,
        "qty": item.quantity,
        "stock_before": stock_before,
        "stock_after": stock_after,
        "performed_by": recorded_by,
    })
```

**Build sale_data dict:**
```python
sale_data = {
    "saleNumber": sale_number,
    "subtotal": subtotal,
    "discountAmount": discount_amount,
    "taxAmount": tax_amount,
    "totalAmount": total_amount,
    "paymentMethod": input.payment_method,
    "recordedBy": recorded_by,
}
if input.customer_name:
    sale_data["customerName"] = input.customer_name
if promotion_id:
    sale_data["promotionId"] = promotion_id
if input.notes:
    sale_data["notes"] = input.notes
```

**Build items_data:**
```python
items_data = [
    {
        "productId": item.product_id,
        "quantity": item.quantity,
        "unitPrice": item.unit_price,
        "discount": 0,
        "totalPrice": item.quantity * item.unit_price,
    }
    for item in input.items
]
```

### 5. `backend/src/modules/sales/controller.py`

Four endpoint functions:
- `list_sales(page, limit, start_date, end_date, payment_method, current_user)` → `paginated_response`
- `get_sale(sale_id, current_user)` → `success_response`
- `get_daily_summary(current_user)` → `success_response`
- `record_sale(input: SaleCreate, current_user)` → `success_response(..., status_code=201)`

Controller wires up SalesService + PromotionService from database instance.

### 6. `backend/src/modules/sales/router.py`

**CRITICAL route ordering — `/daily-summary` MUST be registered BEFORE `/{sale_id}`:**
```python
router = APIRouter(prefix="/sales", tags=["sales"])

router.add_api_route("", controller.list_sales, methods=["GET"],
                     dependencies=[Depends(get_current_user)])
router.add_api_route("", controller.record_sale, methods=["POST"],
                     dependencies=[Depends(get_current_user)])
router.add_api_route("/daily-summary", controller.get_daily_summary, methods=["GET"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/{sale_id}", controller.get_sale, methods=["GET"],
                     dependencies=[Depends(get_current_user)])
```

### 7. `backend/src/main.py` — ADD IMPORT AND REGISTRATION

Add after promotions router:
```python
from src.modules.sales.router import router as sales_router
# ...
app.include_router(sales_router, prefix="/api")
```

### 8. Tests

**`backend/tests/unit/modules/sales/__init__.py`** — empty

**`backend/tests/unit/modules/sales/test_service.py`**

Unit tests for SalesService (all repo + promotion_service calls mocked). Required test classes and coverage:

```
TestRecordSale:
  test_raises_not_found_if_product_missing
  test_raises_validation_error_if_product_inactive
  test_raises_validation_error_if_insufficient_stock
  test_computes_subtotal_correctly
  test_applies_best_promotion_discount
  test_tax_computed_from_product_tax_rate
  test_total_amount_is_subtotal_minus_discount_plus_tax
  test_records_sale_with_no_promotion_when_none_active

TestGetById:
  test_returns_sale_response
  test_raises_not_found_if_missing

TestList:
  test_returns_paginated_sales
  test_applies_date_filters
  test_applies_payment_method_filter

TestGetDailySummary:
  test_returns_correct_totals
  test_payment_breakdown_correct
  test_returns_zeros_when_no_sales_today

TestGetBestDiscount (in promotions/test_service.py — add 2 tests):
  test_returns_none_zero_when_no_active_promotions
  test_returns_promotion_with_highest_discount
```

Add `TestGetBestDiscount` class to the EXISTING `backend/tests/unit/modules/promotions/test_service.py` file (do NOT create a new file for it — just append).

**`backend/tests/integration/test_sales_api.py`**

Integration tests with mocked DB. Required tests:

```
TestListSales:
  test_all_roles_get_200_paginated_response
  test_date_filter_passed_to_service

TestGetSale:
  test_returns_200_with_sale_detail
  test_returns_404_for_missing_sale
  test_unauthenticated_gets_401

TestGetDailySummary:
  test_admin_gets_200_with_summary
  test_manager_gets_200_with_summary
  test_staff_gets_403

TestRecordSale:
  test_any_role_can_record_sale_returns_201
  test_returns_422_for_empty_items_list
  test_returns_422_for_invalid_payment_method
  test_returns_422_for_zero_quantity
```

## Acceptance Criteria

- [ ] `ruff check backend/` exits 0 (no lint errors)
- [ ] `pytest backend/tests/unit/modules/sales/ -v` — all pass
- [ ] `pytest backend/tests/unit/modules/promotions/test_service.py -v` — all pass (including new `TestGetBestDiscount`)
- [ ] `pytest backend/tests/integration/test_sales_api.py -v` — all pass
- [ ] `pytest backend/` exits 0 — full suite passes
- [ ] `GET /api/sales` returns paginated list with filters
- [ ] `GET /api/sales/daily-summary` returns today's totals (admin/manager only, 403 for staff)
- [ ] `GET /api/sales/{id}` returns sale with items array
- [ ] `POST /api/sales` creates sale, deducts stock, creates stock movements, creates journal entry
- [ ] Journal entry: debit Cash (code=1000) = totalAmount, credit Revenue (code=4000) = totalAmount — balanced
- [ ] Sale number format: `SALE-YYYYMMDD-NNN`
- [ ] Tax computed server-side from product.taxRate (Decimal → float)
- [ ] Best promotion auto-selected server-side (not specified by client)
- [ ] Insufficient stock raises 422
- [ ] Inactive or deleted product raises 422
- [ ] Empty items list raises 422
- [ ] CONTEXT.md updated in all touched directories

## Files to Create

**New:**
- `backend/src/modules/sales/__init__.py`
- `backend/src/modules/sales/schemas.py`
- `backend/src/modules/sales/repository.py`
- `backend/src/modules/sales/service.py`
- `backend/src/modules/sales/controller.py`
- `backend/src/modules/sales/router.py`
- `backend/src/modules/sales/CONTEXT.md`
- `backend/tests/unit/modules/sales/__init__.py`
- `backend/tests/unit/modules/sales/test_service.py`
- `backend/tests/integration/test_sales_api.py`

**Modified:**
- `backend/src/modules/promotions/service.py` — add `get_best_discount()` method
- `backend/src/main.py` — import and register sales_router
- `backend/src/modules/CONTEXT.md`
- `backend/src/modules/sales/CONTEXT.md` (new file)
- `backend/tests/unit/modules/promotions/test_service.py` — append `TestGetBestDiscount` class

## Known Pitfalls

1. **Route ordering** — `/daily-summary` MUST be registered before `/{sale_id}`. If reversed, FastAPI will try to parse "daily-summary" as a UUID sale_id and return 404.

2. **`taxRate` is Decimal** — `product.taxRate` is a Prisma Decimal (Python `Decimal` type). Must convert: `float(product.taxRate)` before multiplication. Do NOT do `product.taxRate * item.unit_price` directly — this mixes Decimal and int.

3. **`sale.id` in stock movements** — `sale` is available inside the transaction after `tx.sale.create(data=sale_data)`. Use `sale.id` directly as `referenceId` for stock movements and journal entry. No placeholder needed.

4. **Journal entry balance** — debit_amount must equal credit_amount for Rule #21. Both lines use `journal_data["amount"]` = `totalAmount`. Never use subtotal or discount separately.

5. **`get_best_discount` in PromotionService** — this method needs `from datetime import datetime, timezone` (already imported in the file). Just add the method — no new imports needed.

6. **Integration test mock DB** — Sales integration tests need to mock these Prisma models: `sale`, `saleitem`, `product`, `stockmovement`, `account`, `journalentry`, `journalentryline`. Also mock `prisma.tx()` as async context manager. Study `test_promotions_api.py` for the exact mock pattern.

7. **Product loading in service** — Load each product once (for both validation and tax computation). Store in a list parallel to `input.items` so you can pair them later.

8. **`from __future__ import annotations`** — All Python files must start with this import.

9. **`find_paginated` include** — When returning paginated sale list, include `saleItems: True` in the `find_many` query so `SaleResponse.model_validate()` can build the items list.

## Exit Signal

```bash
cd /path/to/shoperp-workspace
ruff check backend/
pytest backend/ -q
# Must exit 0. Report total passing test count.
```
