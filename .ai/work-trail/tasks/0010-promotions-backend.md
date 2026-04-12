# Task 0010: Promotions Backend

## Branch: task/0010-promotions-backend

## Context Bundle

### Relevant Schema

```sql
CREATE TABLE promotions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('percentage', 'fixed', 'bogo')),
    value INTEGER NOT NULL,            -- percentage points or paisa; 0 for bogo
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    min_purchase_amount INTEGER DEFAULT 0,  -- paisa
    applies_to VARCHAR(20) DEFAULT 'all' CHECK (applies_to IN ('all', 'specific')),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX idx_promo_dates ON promotions(start_date, end_date);

CREATE TABLE promotion_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    promotion_id UUID NOT NULL REFERENCES promotions(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE(promotion_id, product_id)
);
```

**Prisma camelCase attributes (Python access):**
- `obj.id`, `obj.name`, `obj.type`, `obj.value`
- `obj.startDate`, `obj.endDate`
- `obj.minPurchaseAmount`
- `obj.appliesTo`
- `obj.isActive`
- `obj.createdAt`, `obj.updatedAt`, `obj.deletedAt`
- `obj.promotionProducts` — list of PromotionProduct objects
  - Each PromotionProduct: `pp.promotionId`, `pp.productId`

**Prisma model names (Python access):**
- `prisma.promotion` — the promotions table
- `prisma.promotionproduct` — the promotion_products table

**Include pattern:**
```python
include = {"promotionProducts": True}
```
(No nested product include needed — we only expose product_ids, not product details)

### Relevant API Contract

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| GET | /promotions | Yes | all | Paginated list with filters |
| GET | /promotions/active | Yes | all | Currently active promotions |
| GET | /promotions/:id | Yes | all | Single promotion detail |
| POST | /promotions | Yes | admin, manager | Create promotion |
| PUT | /promotions/:id | Yes | admin, manager | Update promotion |
| DELETE | /promotions/:id | Yes | admin | Soft delete |

**Query params for GET /promotions:** `page` (default 1), `limit` (default 20), `is_active` (bool), `type` (str)

**"Active" definition:** `is_active=True AND deleted_at IS NULL AND start_date <= NOW() <= end_date`

**Response shape:**
```json
{
  "id": "uuid",
  "name": "Summer Sale",
  "type": "percentage",
  "value": 20,
  "start_date": "2026-06-01T00:00:00+00:00",
  "end_date": "2026-06-30T23:59:59+00:00",
  "min_purchase_amount": 0,
  "applies_to": "all",
  "is_active": true,
  "product_ids": [],
  "created_at": "2026-04-11T00:00:00+00:00"
}
```

**Create body:**
```json
{
  "name": "Summer Sale",
  "type": "percentage",
  "value": 20,
  "start_date": "2026-06-01T00:00:00+00:00",
  "end_date": "2026-06-30T23:59:59+00:00",
  "min_purchase_amount": 0,
  "applies_to": "specific",
  "is_active": true,
  "product_ids": ["uuid1", "uuid2"]
}
```

### Relevant Patterns

**Module file layout:**
```
backend/src/modules/promotions/
├── __init__.py
├── router.py
├── controller.py
├── service.py
├── repository.py
├── schemas.py
└── CONTEXT.md
```

**Layered architecture:**
```
Router → Controller → Service → Repository → Prisma
```

**Controller pattern (from purchase_orders/controller.py):**
```python
def _get_service(db=Depends(get_db)) -> PromotionService:
    return PromotionService(PromotionRepository(db))

async def list_promotions(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = Query(None),
    type: Optional[str] = Query(None),
    service: PromotionService = Depends(_get_service),
) -> JSONResponse:
    result = await service.list(page=page, limit=limit, is_active=is_active, type=type)
    return paginated_response(
        data=[p.model_dump(mode="json") for p in result.items],
        page=page, limit=limit, total=result.total,
    )
```

**Route ordering — CRITICAL:** `/promotions/active` MUST be registered BEFORE `/{promotion_id}`:
```python
router.add_api_route("", controller.list_promotions, methods=["GET"], ...)
router.add_api_route("/active", controller.get_active_promotions, methods=["GET"], ...)  # BEFORE /{id}
router.add_api_route("/{promotion_id}", controller.get_promotion, methods=["GET"], ...)
```

**model_validate pattern (from purchase_orders/schemas.py):**
```python
class PromotionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    # ... fields ...

    @classmethod
    def model_validate(cls, obj, *, strict=None, from_attributes=None, context=None, experimental_allow_partial=None):
        if hasattr(obj, "__dict__") and not isinstance(obj, dict):
            data = {
                "id": obj.id,
                "name": obj.name,
                "type": obj.type,
                "value": obj.value,
                "start_date": obj.startDate.isoformat() if obj.startDate else "",
                "end_date": obj.endDate.isoformat() if obj.endDate else "",
                "min_purchase_amount": obj.minPurchaseAmount,
                "applies_to": obj.appliesTo,
                "is_active": obj.isActive,
                "product_ids": [pp.productId for pp in obj.promotionProducts] if obj.promotionProducts else [],
                "created_at": obj.createdAt.isoformat() if obj.createdAt else "",
            }
            return cls(**data)
        return super().model_validate(obj, strict=strict, from_attributes=from_attributes, context=context)
```

**Transaction pattern (for create with products):**
```python
async with self.prisma.tx() as tx:
    promotion = await tx.promotion.create(data=promo_data)
    for product_id in product_ids:
        await tx.promotionproduct.create(data={
            "promotionId": promotion.id,
            "productId": product_id,
        })
return await self.prisma.promotion.find_first(where={"id": promotion.id}, include={"promotionProducts": True})
```

**Active promotions query:**
```python
from datetime import datetime, timezone

now = datetime.now(timezone.utc)
where = {
    "isActive": True,
    "deletedAt": None,
    "startDate": {"lte": now},
    "endDate": {"gte": now},
}
return await self.prisma.promotion.find_many(where=where, include={"promotionProducts": True})
```

**Standard response helpers:**
```python
from src.core.responses import success_response, paginated_response, error_response
```

**Typed exceptions:**
```python
from src.core.exceptions import NotFoundError, ValidationError
raise NotFoundError("Promotion", promotion_id)
raise ValidationError("end_date must be after start_date")
```

### Architecture Rules That Apply

- Rule #8: Cross-table mutations use transactions (create promotion + promotion_products in one tx).
- Rule #9: Controllers contain zero business logic.
- Rule #10: Services contain ALL business logic. Repositories have only DB queries.
- Rule #11: Repositories contain database queries only — no conditionals, no calculations.
- Rule #12: All inputs validated with Pydantic schemas.
- Rule #14: Standard response format.
- Rule #15: Auth enforced by middleware.
- Rule #16: Role guards on mutation endpoints.

## What to Build

### schemas.py

```python
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

class PromotionCreate(BaseModel):
    name: str = Field(..., min_length=1)
    type: Literal['percentage', 'fixed', 'bogo']
    value: int = Field(..., ge=0)       # % points, paisa, or 0 for bogo
    start_date: str                      # ISO datetime string
    end_date: str                        # ISO datetime string
    min_purchase_amount: int = Field(0, ge=0)
    applies_to: Literal['all', 'specific'] = 'all'
    is_active: bool = True
    product_ids: list[str] = []

class PromotionUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[Literal['percentage', 'fixed', 'bogo']] = None
    value: Optional[int] = Field(None, ge=0)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    min_purchase_amount: Optional[int] = Field(None, ge=0)
    applies_to: Optional[Literal['all', 'specific']] = None
    is_active: Optional[bool] = None
    product_ids: Optional[list[str]] = None  # None = don't touch products; [] = clear all

class PromotionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    type: str
    value: int
    start_date: str
    end_date: str
    min_purchase_amount: int
    applies_to: str
    is_active: bool
    product_ids: list[str]
    created_at: str
    # custom model_validate as shown above
```

### repository.py

Methods to implement:

```python
async def find_paginated(self, skip, take, where) -> tuple[list, int]
async def find_active(self, now: datetime) -> list
async def find_by_id(self, promotion_id: str)  # include promotionProducts
async def create_with_products(self, promo_data: dict, product_ids: list[str])
async def update_with_products(self, promotion_id: str, promo_data: dict, product_ids: list[str] | None)
    # product_ids=None → leave existing products unchanged
    # product_ids=[] → clear all products
    # product_ids=[...] → replace products
async def soft_delete(self, promotion_id: str) -> None
```

### service.py

Methods to implement:

```python
async def list(self, page, limit, is_active, type) -> PaginatedPromotions
async def get_active(self) -> list[PromotionResponse]
async def get_by_id(self, promotion_id: str) -> PromotionResponse
async def create(self, input: PromotionCreate) -> PromotionResponse
    # Validate: end_date > start_date
    # Validate: if applies_to='specific', product_ids must not be empty
async def update(self, promotion_id: str, input: PromotionUpdate) -> PromotionResponse
    # Only update fields that are not None
    # Pass product_ids to repo (None if not provided in update)
async def delete(self, promotion_id: str) -> None
    # Soft delete only

def calculate_discount(
    self,
    promotion,           # Prisma Promotion object with promotionProducts loaded
    subtotal: int,       # total in paisa
    items: list[dict],   # [{product_id, quantity, unit_price}] unit_price in paisa
) -> int:               # discount amount in paisa
    """
    Rules:
    - If subtotal < promotion.minPurchaseAmount → return 0
    - percentage: int(subtotal * promotion.value / 100)
    - fixed: min(promotion.value, subtotal)
    - bogo:
        - qualifying products = all items if appliesTo='all',
          else only items whose product_id is in promotionProducts
        - for each qualifying item: free_count = qty // 2
        - discount = sum(free_count * unit_price) for each qualifying item
    """
```

### router.py

```python
router = APIRouter(prefix="/promotions", tags=["promotions"])

# Static/action routes BEFORE /{promotion_id}
router.add_api_route("", controller.list_promotions, methods=["GET"],
    dependencies=[Depends(require_roles("admin", "manager", "staff"))])
router.add_api_route("", controller.create_promotion, methods=["POST"], status_code=201,
    dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/active", controller.get_active_promotions, methods=["GET"],
    dependencies=[Depends(require_roles("admin", "manager", "staff"))])

# Parameterized routes LAST
router.add_api_route("/{promotion_id}", controller.get_promotion, methods=["GET"],
    dependencies=[Depends(require_roles("admin", "manager", "staff"))])
router.add_api_route("/{promotion_id}", controller.update_promotion, methods=["PUT"],
    dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/{promotion_id}", controller.delete_promotion, methods=["DELETE"],
    dependencies=[Depends(require_roles("admin"))])
```

Note: `require_roles("admin", "manager", "staff")` = all authenticated users. Check if there's a simpler dependency in `core/auth.py` — if so, use `get_current_user` directly for read endpoints.

### main.py

Add after existing routers:
```python
from src.modules.promotions.router import router as promotions_router
app.include_router(promotions_router, prefix="/api")
```

### Tests

**`tests/unit/modules/promotions/test_service.py`** — Test all service methods:

`TestCreate`:
- `test_raises_validation_error_if_end_date_before_start_date`
- `test_raises_validation_error_if_specific_applies_to_has_no_product_ids`
- `test_creates_promotion_with_products`
- `test_creates_promotion_without_products`

`TestUpdate`:
- `test_raises_not_found_if_missing`
- `test_updates_fields_and_passes_product_ids_to_repo`
- `test_passes_none_product_ids_when_not_provided`

`TestList` / `TestGetById` / `TestGetActive` / `TestDelete`:
- Standard not-found and happy-path tests

`TestCalculateDiscount`:
- `test_percentage_discount_correct`
- `test_fixed_discount_correct`
- `test_fixed_discount_capped_at_subtotal`
- `test_bogo_all_products`
- `test_bogo_specific_products_only`
- `test_returns_zero_if_min_purchase_not_met`
- `test_bogo_odd_quantity_floors_correctly` (qty=3 → 1 free)

**`tests/integration/test_promotions_api.py`** — Test all endpoints:
- GET /promotions → 200 paginated (admin)
- GET /promotions/active → 200 list (staff)
- GET /promotions/:id → 200 / 404
- POST /promotions → 201 (manager) / 403 (staff) / 422 (missing fields)
- PUT /promotions/:id → 200
- DELETE /promotions/:id → 200 (admin) / 403 (manager)

## Acceptance Criteria

- [ ] GET /promotions returns paginated list with `is_active` and `type` filters working
- [ ] GET /promotions/active returns only promotions where `is_active=true AND start_date ≤ NOW ≤ end_date`
- [ ] GET /promotions/:id returns full promotion with `product_ids` list
- [ ] POST /promotions validates `end_date > start_date`
- [ ] POST /promotions validates `applies_to='specific'` requires non-empty `product_ids`
- [ ] POST /promotions with `applies_to='specific'` creates promotion_product records in transaction
- [ ] PUT /promotions/:id with `product_ids` replaces existing product associations
- [ ] PUT /promotions/:id without `product_ids` (None) leaves product associations unchanged
- [ ] PUT /promotions/:id with `product_ids=[]` clears all product associations
- [ ] DELETE /promotions/:id soft-deletes (sets deleted_at, not removed from DB)
- [ ] `calculate_discount` returns correct amounts for all three types
- [ ] `calculate_discount` returns 0 when `subtotal < min_purchase_amount`
- [ ] BOGO only counts qualifying products when `applies_to='specific'`
- [ ] Router registers `/active` before `/{promotion_id}` (no shadowing)
- [ ] All tests pass: `pytest` exits 0
- [ ] Lint passes: `ruff check` exits 0

## Files to Create/Modify

**New files:**
- `backend/src/modules/promotions/__init__.py`
- `backend/src/modules/promotions/schemas.py`
- `backend/src/modules/promotions/repository.py`
- `backend/src/modules/promotions/service.py`
- `backend/src/modules/promotions/controller.py`
- `backend/src/modules/promotions/router.py`
- `backend/src/modules/promotions/CONTEXT.md`
- `backend/tests/unit/modules/promotions/__init__.py`
- `backend/tests/unit/modules/promotions/test_service.py`
- `backend/tests/integration/test_promotions_api.py`

**Modified files:**
- `backend/src/main.py` — add promotions router import + include

## Known Pitfalls

1. **Route ordering** — `/active` must be added BEFORE `/{promotion_id}` in the router. Use `router.add_api_route` (not decorator shorthand) in the exact order specified above.

2. **Prisma model names** — `prisma.promotion` and `prisma.promotionproduct` (both lowercase, no underscores).

3. **DateTime parsing** — `start_date` and `end_date` come in as ISO strings from the request. Parse them before storing:
   ```python
   from datetime import datetime
   dt = datetime.fromisoformat(input.start_date)
   ```
   The Prisma client expects a `datetime` object, not a string.

4. **Active query with datetime** — Use `datetime.now(timezone.utc)` to get current UTC time. Prisma Timestamptz comparison:
   ```python
   "startDate": {"lte": now},
   "endDate": {"gte": now},
   ```

5. **BOGO integer floor** — `qty // 2` not `qty / 2`. Free count for qty=3 is 1, not 1.5.

6. **Transaction return value** — After `async with self.prisma.tx() as tx:` block, the promotion object may not have includes loaded. Always do a fresh `find_first` after the transaction to return the full object.

7. **test_health.py on main** — The main branch does not have an integration test_health.py (it was added in phase/1). Do NOT add one. Only the files listed above.

8. **Unused import in tests** — Ruff will flag unused imports as F401. Do not import classes that aren't used. Use `AsyncMock` for async methods, `MagicMock` for sync. Do not import `pytest` unless you use `@pytest.mark.asyncio` or `pytest.raises`.

## Exit Signal

```bash
cd backend
python3 -m pytest tests/ -x -q 2>&1 | tail -5
# Must show: N passed, 0 failed (where N ≥ 339 + new tests)
python3 -m ruff check src/ tests/ 2>&1 | grep -v "^tests/integration/test_categories\|^tests/integration/test_inventory\|^tests/integration/test_products\|^tests/unit/modules/inventory"
# Must show: All checks passed! (pre-existing errors in older test files are acceptable)
```
