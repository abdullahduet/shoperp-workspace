# Task 0006: Inventory Backend

## Branch: task/0006-inventory-backend
## Assigned to: engineer
## Status: not started

## Context Bundle

Everything you need is here. Do NOT read knowledge-base/ files directly.

### Relevant Schema (Prisma)

```prisma
model StockMovement {
  id            String   @id @default(dbgenerated("gen_random_uuid()")) @db.Uuid
  productId     String   @map("product_id") @db.Uuid
  movementType  String   @map("movement_type") @db.VarChar(20)
  quantity      Int
  stockBefore   Int      @map("stock_before")
  stockAfter    Int      @map("stock_after")
  referenceType String?  @map("reference_type") @db.VarChar(50)
  referenceId   String?  @map("reference_id") @db.Uuid
  notes         String?  @db.Text
  performedBy   String?  @map("performed_by") @db.Uuid
  createdAt     DateTime @default(now()) @map("created_at") @db.Timestamptz()

  product         Product @relation(fields: [productId], references: [id])
  performedByUser User?   @relation(fields: [performedBy], references: [id])

  @@index([productId], name: "idx_sm_product")
  @@index([createdAt], name: "idx_sm_date")
  @@map("stock_movements")
}

model Product {
  -- relevant fields --
  id            String   @id ...
  name          String
  sku           String   @unique
  stockQuantity Int      @map("stock_quantity")
  minStockLevel Int      @map("min_stock_level")
  costPrice     Int      @map("cost_price")
  isActive      Boolean  @map("is_active")
  deletedAt     DateTime? @map("deleted_at")
}
```

**Prisma uses camelCase in Python:** `productId`, `movementType`, `stockBefore`, `stockAfter`, `referenceType`, `referenceId`, `performedBy`, `createdAt`, `stockQuantity`, `costPrice`, etc.

### API Contract

```
GET  /api/inventory/movements   → paginated list of stock movements (all auth)
POST /api/inventory/adjust      → manual stock adjustment             [admin, manager]
GET  /api/inventory/valuation   → total inventory value              [admin, manager]
```

**GET /inventory/movements query params:**
- `page` (int, default 1), `limit` (int, default 20, max 100)
- `product_id` (str UUID) — filter by product
- `movement_type` (str: `in`|`out`|`adjustment`) — filter by type
- `start_date` (str ISO date `YYYY-MM-DD`) — createdAt >= start_date (start of day UTC)
- `end_date` (str ISO date `YYYY-MM-DD`) — createdAt <= end_date (end of day UTC)

**POST /inventory/adjust body:**
```json
{
  "product_id": "uuid",
  "quantity": -5,          // signed integer: positive = stock in, negative = stock out
  "notes": "Damaged goods removed"
}
```
Rules:
- `quantity` must be non-zero
- Resulting stock (`current + quantity`) must be >= 0 — reject if it would go negative
- Creates a `stock_movement` record with `movement_type = "adjustment"`
- Updates `product.stock_quantity` atomically with the movement creation (transaction)

**GET /inventory/valuation response:**
```json
{
  "success": true,
  "data": {
    "total_value": 1250000,       // integer paisa: SUM(stock_quantity * cost_price)
    "product_count": 42,          // count of active non-deleted products with stock > 0
    "currency": "BDT"
  },
  "message": "OK"
}
```

### Response Shapes

**StockMovementResponse:**
```python
{
  "id": str,
  "product_id": str,
  "product_name": str,       # joined — include product.name
  "product_sku": str,        # joined — include product.sku
  "movement_type": str,      # "in" | "out" | "adjustment"
  "quantity": int,
  "stock_before": int,
  "stock_after": int,
  "reference_type": str | None,
  "reference_id": str | None,
  "notes": str | None,
  "performed_by": str | None,
  "created_at": datetime
}
```

**AdjustmentRequest:**
```python
{
  "product_id": str,
  "quantity": int (non-zero, enforced by Pydantic Field(ne=0))
  "notes": Optional[str]
}
```

### Patterns to Follow

**Service with transaction (adjust):**
```python
async def adjust(self, product_id: str, quantity: int, notes: str | None, performed_by: str) -> StockMovementResponse:
    product = await self.repo.find_product_by_id(product_id)
    if product is None:
        raise NotFoundError("Product", product_id)
    if not product.isActive or product.deletedAt is not None:
        raise ValidationError("Cannot adjust stock for an inactive or deleted product")
    
    stock_before = product.stockQuantity
    stock_after = stock_before + quantity
    if stock_after < 0:
        raise ValidationError(f"Adjustment would result in negative stock ({stock_after})")
    
    movement = await self.repo.create_adjustment(
        product_id=product_id,
        quantity=quantity,
        stock_before=stock_before,
        stock_after=stock_after,
        notes=notes,
        performed_by=performed_by,
    )
    return StockMovementResponse.model_validate(movement)
```

**Repository with transaction:**
```python
async def create_adjustment(self, product_id, quantity, stock_before, stock_after, notes, performed_by):
    async with self.prisma.tx() as tx:
        movement = await tx.stockmovement.create(data={
            "productId": product_id,
            "movementType": "adjustment",
            "quantity": quantity,
            "stockBefore": stock_before,
            "stockAfter": stock_after,
            "notes": notes,
            "performedBy": performed_by,
            "referenceType": "manual_adjustment",
        })
        await tx.product.update(
            where={"id": product_id},
            data={"stockQuantity": stock_after},
        )
        return movement
```

**Note on `find_many` with `include`:** To get product name/sku in movement responses, use Prisma's `include`:
```python
items = await self.prisma.stockmovement.find_many(
    skip=skip, take=take, where=where, order=[{"createdAt": "desc"}],
    include={"product": True}
)
```
Then in `model_validate`, access `obj.product.name` and `obj.product.sku`.

**Valuation in Python** (Prisma can't do column multiplication):
```python
async def compute_valuation(self) -> tuple[int, int]:
    products = await self.prisma.product.find_many(
        where={"deletedAt": None, "isActive": True, "stockQuantity": {"gt": 0}}
    )
    total_value = sum(p.stockQuantity * p.costPrice for p in products)
    product_count = len(products)
    return total_value, product_count
```

**Date filtering** for movements:
```python
from datetime import datetime, timezone, timedelta

if start_date:
    dt_start = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    where["createdAt"] = {**where.get("createdAt", {}), "gte": dt_start}
if end_date:
    dt_end = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc) + timedelta(days=1)
    where["createdAt"] = {**where.get("createdAt", {}), "lt": dt_end}
```

**Existing patterns to match:**
- Controller: thin, imports from `src.core.auth`, `src.core.responses`, `src.database`
- Service: class with `__init__(self, repo)`, all logic here
- Repository: class with `__init__(self, prisma)`, Prisma queries only
- Error types: `NotFoundError`, `ValidationError` from `src.core.exceptions`
- Response: `success_response`, `paginated_response` from `src.core.responses`
- Auth: `Depends(get_current_user)`, `Depends(require_roles(...))` from `src.core.auth`

### Architecture Rules That Apply

- Rule #8: Cross-table mutations use database transactions. The `adjust` endpoint MUST update both `product.stock_quantity` and create `stock_movement` in one transaction.
- Rule #9: Controllers — zero business logic
- Rule #10: Services — ALL business logic (negative stock guard, product existence/active check)
- Rule #11: Repositories — DB queries only
- Rule #12: Pydantic validation before service
- Rule #13: Typed exceptions
- Rule #14: Standard response format
- Rule #16: Role guards on mutation endpoints
- Rule #22: Every stock change creates a `stock_movement` record (enforced here)

## What to Build

### Module: Inventory (`src/modules/inventory/`)

```
backend/src/modules/inventory/
├── router.py
├── controller.py
├── service.py
├── repository.py
├── schemas.py
└── CONTEXT.md
```

**schemas.py:**
```python
class AdjustmentRequest(BaseModel):
    product_id: str
    quantity: int = Field(..., ne=0)   # non-zero
    notes: Optional[str] = None

class StockMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    product_id: str
    product_name: str
    product_sku: str
    movement_type: str
    quantity: int
    stock_before: int
    stock_after: int
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    notes: Optional[str] = None
    performed_by: Optional[str] = None
    created_at: datetime

    @classmethod
    def model_validate(cls, obj, ...):
        # map camelCase Prisma attributes + include product
        if hasattr(obj, "__dict__") and not isinstance(obj, dict):
            data = {
                "id": obj.id,
                "product_id": obj.productId,
                "product_name": obj.product.name if obj.product else "",
                "product_sku": obj.product.sku if obj.product else "",
                "movement_type": obj.movementType,
                "quantity": obj.quantity,
                "stock_before": obj.stockBefore,
                "stock_after": obj.stockAfter,
                "reference_type": obj.referenceType,
                "reference_id": obj.referenceId,
                "notes": obj.notes,
                "performed_by": obj.performedBy,
                "created_at": obj.createdAt,
            }
            return cls(**data)
        return super().model_validate(obj, ...)

class ValuationResponse(BaseModel):
    total_value: int
    product_count: int
    currency: str = "BDT"
```

**service.py — InventoryService:**
- `list_movements(page, limit, product_id, movement_type, start_date, end_date) → PaginatedMovements`
- `adjust(product_id, quantity, notes, performed_by) → StockMovementResponse`
- `get_valuation() → ValuationResponse`

**repository.py — InventoryRepository:**
- `find_movements(skip, take, where) → tuple[list[StockMovement], int]` (with `include={"product": True}`)
- `find_product_by_id(product_id) → Product | None` (where deletedAt=None)
- `create_adjustment(product_id, quantity, stock_before, stock_after, notes, performed_by) → StockMovement` (transaction: create movement + update product)
- `compute_valuation() → tuple[int, int]` (total_value, product_count) — fetch products, sum in Python

**controller.py:**
```python
async def list_movements(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    product_id: Optional[str] = Query(None),
    movement_type: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    service=Depends(_get_service),
) → JSONResponse

async def adjust(
    body: AdjustmentRequest,
    current_user: User = Depends(get_current_user),
    service=Depends(_get_service),
) → JSONResponse  # 201

async def get_valuation(service=Depends(_get_service)) → JSONResponse
```

**router.py:**
```python
router = APIRouter(prefix="/inventory", tags=["inventory"])
router.add_api_route("/movements", controller.list_movements, methods=["GET"],
    dependencies=[Depends(get_current_user)])
router.add_api_route("/adjust", controller.adjust, methods=["POST"],
    status_code=201, dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/valuation", controller.get_valuation, methods=["GET"],
    dependencies=[Depends(require_roles("admin", "manager"))])
```

### Register router in `backend/src/main.py`

```python
from src.modules.inventory.router import router as inventory_router
app.include_router(inventory_router, prefix="/api")
```

### Tests

**`tests/unit/modules/inventory/test_service.py`:**
- `_make_fake_product(stock_quantity, cost_price, is_active=True)` — MagicMock with camelCase attrs
- `_make_fake_movement(product_mock)` — MagicMock with all StockMovement camelCase attrs + `.product` relation
- `TestListMovements`: happy path returns paginated movements
- `TestAdjust`:
  - `test_positive_adjustment_succeeds` — quantity=+10, new stock = old+10
  - `test_negative_adjustment_succeeds` — quantity=-5, stock=10, new stock=5
  - `test_adjustment_rejected_when_would_go_negative` — quantity=-20, stock=10 → ValidationError
  - `test_adjustment_raises_not_found_for_missing_product` — find_product returns None → NotFoundError
  - `test_adjustment_raises_validation_for_inactive_product` — isActive=False → ValidationError
- `TestGetValuation`:
  - `test_valuation_sums_stock_times_cost` — two products, verify total_value = sum

**`tests/integration/test_inventory_api.py`:**
Mock pattern: `db.stockmovement.*`, `db.product.*`, `db.user.find_first`

- GET /api/inventory/movements → 200, paginated
- GET /api/inventory/movements?product_id=X → 200 (filter works)
- POST /api/inventory/adjust with manager JWT → 201
- POST /api/inventory/adjust with staff JWT → 403
- POST /api/inventory/adjust with quantity=0 → 422 (Pydantic)
- POST /api/inventory/adjust resulting in negative stock → 422
- GET /api/inventory/valuation with admin JWT → 200
- GET /api/inventory/valuation with staff JWT → 403

For the adjust integration test, `db.product.find_first` returns a product with enough stock, and `db.tx` must be mocked. Mock `db.tx` as an async context manager:

```python
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import asynccontextmanager

# Mock the transaction context manager
mock_tx = MagicMock()
mock_tx.stockmovement = MagicMock()
mock_tx.stockmovement.create = AsyncMock(return_value=fake_movement)
mock_tx.product = MagicMock()
mock_tx.product.update = AsyncMock(return_value=None)

@asynccontextmanager
async def fake_tx():
    yield mock_tx

db.tx = fake_tx
```

## Acceptance Criteria

- [ ] `GET /api/inventory/movements` returns paginated list with product_name and product_sku
- [ ] Filter by `product_id`, `movement_type`, `start_date`, `end_date` all work
- [ ] `POST /api/inventory/adjust` creates movement + updates product stock atomically (transaction)
- [ ] Adjustment rejected (422) if resulting stock would go negative
- [ ] Adjustment rejected (404) if product not found
- [ ] Adjustment rejected (422) if product is inactive or deleted
- [ ] `GET /api/inventory/valuation` returns total_value (paisa), product_count, currency
- [ ] Staff role gets 403 on adjust and valuation
- [ ] `pytest` exits 0 (all tests pass)
- [ ] `ruff check src/modules/inventory` exits 0

## Files to Create/Modify

**Create:**
- `backend/src/modules/inventory/router.py`
- `backend/src/modules/inventory/controller.py`
- `backend/src/modules/inventory/service.py`
- `backend/src/modules/inventory/repository.py`
- `backend/src/modules/inventory/schemas.py`
- `backend/src/modules/inventory/CONTEXT.md`
- `backend/src/modules/inventory/__init__.py`
- `backend/tests/unit/modules/inventory/__init__.py`
- `backend/tests/unit/modules/inventory/test_service.py`
- `backend/tests/integration/test_inventory_api.py`

**Modify:**
- `backend/src/main.py` — add inventory router

## Known Pitfalls

- `StockMovement` Prisma model name is `stockmovement` in Python (lowercase, no underscore): `prisma.stockmovement.find_many(...)` — NOT `prisma.stock_movement`
- `include={"product": True}` gives you `obj.product.name` and `obj.product.sku` on each result
- Prisma transaction: `async with self.prisma.tx() as tx:` — use `tx` for all DB calls inside
- `movement_type` filter in Prisma where: `{"movementType": movement_type}` (camelCase key)
- `Field(ne=0)` in Pydantic v2 to enforce non-zero: use `Field(..., ne=0)` — note: in Pydantic v2, `ne` is NOT a valid Field kwarg; instead use `Annotated[int, Field()] ` with a validator, OR use `Field(...)` plus `@field_validator`. Simpler: `quantity: int = Field(..., description="non-zero")` + `@field_validator('quantity') def quantity_nonzero(cls, v): if v == 0: raise ValueError('quantity must be non-zero'); return v`
- Date filtering: `end_date` should be end of that day — add 1 day and use `lt` (strictly less than), so all movements on that date are included
- The `count` call for paginated movements also needs the same `where` dict as `find_many`
- The transaction mock for integration tests needs `asynccontextmanager` — see pattern in task file

## Exit Signal

```bash
cd /Users/abdullah/projects/shoperp-workspace/backend
python -m pytest tests/unit/modules/inventory/ tests/integration/test_inventory_api.py -v
# All pass (exit 0)

ruff check src/modules/inventory
# No errors
```

## Outcome (filled by Lead after merge)

_Not yet completed._
