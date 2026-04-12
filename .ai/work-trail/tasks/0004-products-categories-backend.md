# Task 0004: Products + Categories Backend

## Branch: task/0004-products-categories-backend
## Assigned to: engineer
## Status: merged ✓

## Context Bundle

Everything you need is here. Do NOT read knowledge-base/ files directly.

### Relevant Schema (Prisma)

```prisma
model Category {
  id          String     @id @default(dbgenerated("gen_random_uuid()")) @db.Uuid
  name        String     @db.VarChar(255)
  description String?    @db.Text
  parentId    String?    @map("parent_id") @db.Uuid
  sortOrder   Int        @default(0) @map("sort_order")
  createdAt   DateTime   @default(now()) @map("created_at") @db.Timestamptz()
  updatedAt   DateTime   @updatedAt @map("updated_at") @db.Timestamptz()
  deletedAt   DateTime?  @map("deleted_at") @db.Timestamptz()

  parent    Category?  @relation("CategoryParent", fields: [parentId], references: [id], onDelete: SetNull)
  children  Category[] @relation("CategoryParent")
  products  Product[]
}

model Product {
  id             String    @id @default(dbgenerated("gen_random_uuid()")) @db.Uuid
  name           String    @db.VarChar(255)
  sku            String    @unique @db.VarChar(100)
  barcode        String?   @unique @db.VarChar(100)
  categoryId     String?   @map("category_id") @db.Uuid
  description    String?   @db.Text
  unitPrice      Int       @default(0) @map("unit_price")
  costPrice      Int       @default(0) @map("cost_price")
  taxRate        Decimal   @default(0.00) @map("tax_rate") @db.Decimal(5, 2)
  stockQuantity  Int       @default(0) @map("stock_quantity")
  minStockLevel  Int       @default(0) @map("min_stock_level")
  unitOfMeasure  String    @default("pcs") @map("unit_of_measure") @db.VarChar(20)
  imageUrl       String?   @map("image_url") @db.VarChar(500)
  isActive       Boolean   @default(true) @map("is_active")
  createdAt      DateTime  @default(now()) @map("created_at") @db.Timestamptz()
  updatedAt      DateTime  @updatedAt @map("updated_at") @db.Timestamptz()
  deletedAt      DateTime? @map("deleted_at") @db.Timestamptz()

  category           Category?           @relation(fields: [categoryId], references: [id], onDelete: SetNull)
  purchaseOrderItems PurchaseOrderItem[]
  stockMovements     StockMovement[]
  saleItems          SaleItem[]
  promotionProducts  PromotionProduct[]
}
```

**Important: Prisma uses camelCase attribute names in Python.** All queries use camelCase:
- `deletedAt` not `deleted_at`
- `parentId` not `parent_id`
- `categoryId` not `category_id`
- `unitPrice` not `unit_price`
- etc.

### Relevant API Contract

```
# Categories
GET    /api/categories         → list all (flat, non-deleted)
GET    /api/categories/tree    → nested tree (parent → children)
POST   /api/categories         → create   [admin, manager]
PUT    /api/categories/:id     → update   [admin, manager]
DELETE /api/categories/:id     → soft delete [admin]

# Products
GET    /api/products                  → paginated list (with filters)
GET    /api/products/low-stock        → products where stock_quantity < min_stock_level
GET    /api/products/:id              → single product detail
POST   /api/products                  → create   [admin, manager]
PUT    /api/products/:id              → update   [admin, manager]
DELETE /api/products/:id              → soft delete [admin]
POST   /api/products/import           → CSV bulk import [admin]
```

**Query params for GET /products:**
- `page` (int, default 1)
- `limit` (int, default 20, max 100)
- `search` (str) — matches name or SKU (case-insensitive)
- `category_id` (UUID str)
- `is_active` (bool)
- `sort` (str: `name`|`sku`|`stock_quantity`|`unit_price`, default `name`)
- `order` (str: `asc`|`desc`, default `asc`)

### Response Shapes

**CategoryResponse:**
```python
{
  "id": str,
  "name": str,
  "description": str | None,
  "parent_id": str | None,
  "sort_order": int,
  "created_at": datetime
}
```

**CategoryTreeNode** (for /tree endpoint):
```python
{
  "id": str,
  "name": str,
  "description": str | None,
  "sort_order": int,
  "children": [CategoryTreeNode, ...]   # only children, no parent_id needed
}
```

**ProductResponse:**
```python
{
  "id": str,
  "name": str,
  "sku": str,
  "barcode": str | None,
  "category_id": str | None,
  "description": str | None,
  "unit_price": int,
  "cost_price": int,
  "tax_rate": float,
  "stock_quantity": int,
  "min_stock_level": int,
  "unit_of_measure": str,
  "image_url": str | None,
  "is_active": bool,
  "created_at": datetime
}
```

**CSV Import response** (`POST /products/import`):
```python
{
  "success": True,
  "data": {
    "created": 10,
    "skipped": 2,
    "errors": [{"row": 3, "sku": "SKU-003", "reason": "Duplicate SKU"}]
  },
  "message": "Import complete"
}
```

### Relevant Patterns

**Camelcase mapping in response schemas** — same pattern as UserResponse:
```python
class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    sku: str
    # ... all fields ...

    @classmethod
    def model_validate(cls, obj, *, strict=None, from_attributes=None, context=None, experimental_allow_partial=None):
        if hasattr(obj, "__dict__") and not isinstance(obj, dict):
            data = {
                "id": obj.id,
                "name": obj.name,
                "sku": obj.sku,
                "barcode": obj.barcode,
                "category_id": obj.categoryId,
                "description": obj.description,
                "unit_price": obj.unitPrice,
                "cost_price": obj.costPrice,
                "tax_rate": float(obj.taxRate),  # Decimal → float
                "stock_quantity": obj.stockQuantity,
                "min_stock_level": obj.minStockLevel,
                "unit_of_measure": obj.unitOfMeasure,
                "image_url": obj.imageUrl,
                "is_active": obj.isActive,
                "created_at": obj.createdAt,
            }
            return cls(**data)
        return super().model_validate(obj, strict=strict, from_attributes=from_attributes, context=context)
```

**Controller pattern** (thin — validate, delegate, respond):
```python
from fastapi import APIRouter, Depends, Query
from src.core.auth import get_current_user, require_roles
from src.core.responses import success_response, paginated_response
from src.database import get_db

async def list_products(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    category_id: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    sort: str = Query("name"),
    order: str = Query("asc"),
    service = Depends(_get_service),
) -> JSONResponse:
    result = await service.list_products(page, limit, search, category_id, is_active, sort, order)
    return paginated_response(
        data=[p.model_dump(mode="json") for p in result.items],
        page=page, limit=limit, total=result.total
    )
```

**Service pattern** (ALL business logic):
```python
@dataclass
class PaginatedProducts:
    items: list[ProductResponse]
    total: int

class ProductService:
    def __init__(self, repo: ProductRepository) -> None:
        self.repo = repo

    async def create(self, input: ProductCreate) -> ProductResponse:
        if await self.repo.find_by_sku(input.sku):
            raise ConflictError(f"SKU '{input.sku}' already exists")
        if input.barcode and await self.repo.find_by_barcode(input.barcode):
            raise ConflictError(f"Barcode '{input.barcode}' already exists")
        product = await self.repo.create(input)
        return ProductResponse.model_validate(product)
```

**Repository pattern** (DB queries only):
```python
class ProductRepository:
    def __init__(self, prisma: Prisma) -> None:
        self.prisma = prisma

    async def find_by_sku(self, sku: str):
        return await self.prisma.product.find_first(
            where={"sku": sku, "deletedAt": None}
        )

    async def list_paginated(self, skip: int, take: int, where: dict, order_by: dict):
        items = await self.prisma.product.find_many(
            skip=skip, take=take, where=where, order=[order_by]
        )
        total = await self.prisma.product.count(where=where)
        return items, total
```

**Router pattern:**
```python
router = APIRouter(prefix="/products", tags=["products"])

router.add_api_route("", controller.list_products, methods=["GET"])
router.add_api_route("/low-stock", controller.low_stock, methods=["GET"])
router.add_api_route("/{product_id}", controller.get_product, methods=["GET"])
router.add_api_route("", controller.create_product, methods=["POST"],
    status_code=201, dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/{product_id}", controller.update_product, methods=["PUT"],
    dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/{product_id}", controller.delete_product, methods=["DELETE"],
    dependencies=[Depends(require_roles("admin"))])
router.add_api_route("/import", controller.import_products, methods=["POST"],
    dependencies=[Depends(require_roles("admin"))])
```

**IMPORTANT — route ordering**: `/low-stock` and `/import` MUST be registered BEFORE `/{product_id}` or FastAPI will interpret them as product IDs.

**IMPORTANT — Prisma `where` with `None` values**: When building the filter dict, omit keys whose values are None. Do NOT pass `{"categoryId": None}` as a filter — use `if category_id: where["categoryId"] = category_id`.

**IMPORTANT — Prisma search (contains)**: For case-insensitive search use:
```python
if search:
    where["OR"] = [
        {"name": {"contains": search, "mode": "insensitive"}},
        {"sku": {"contains": search, "mode": "insensitive"}},
    ]
```

**CSV import pattern**: Use Python's `csv.DictReader` on the uploaded file bytes. Required columns: `name`, `sku`, `unit_price`, `cost_price`. Optional: `barcode`, `description`, `min_stock_level`, `unit_of_measure`, `tax_rate`. Skip rows with missing required fields or duplicate SKUs. Return summary.

```python
async def import_products(
    file: UploadFile = File(...),
    service = Depends(_get_service),
) -> JSONResponse:
    contents = await file.read()
    result = await service.import_from_csv(contents)
    return success_response(data=result, message="Import complete")
```

### Architecture Rules That Apply

- Rule #1: UUIDs for all PKs
- Rule #2: Money as integers (unit_price, cost_price in paisa)
- Rule #4: `deleted_at` on all business entities
- Rule #5: All queries filter `deleted_at IS NULL` (Prisma: `"deletedAt": None`)
- Rule #9: Controllers — zero business logic
- Rule #10: Services — ALL business logic (SKU uniqueness, barcode uniqueness, soft delete logic)
- Rule #11: Repositories — DB queries only
- Rule #12: Pydantic validation before service
- Rule #13: Typed exceptions (NotFoundError, ConflictError, ValidationError)
- Rule #14: Standard API response format
- Rule #16: Role guards on mutation endpoints

## What to Build

### Module: Categories (`src/modules/categories/`)

Files to create:
```
backend/src/modules/categories/
├── router.py
├── controller.py
├── service.py
├── repository.py
├── schemas.py
└── CONTEXT.md
```

**schemas.py:**
- `CategoryCreate`: `name` (required, min 1), `description` (optional), `parent_id` (optional UUID str), `sort_order` (int, default 0)
- `CategoryUpdate`: all fields optional (same fields as Create)
- `CategoryResponse`: id, name, description, parent_id, sort_order, created_at (with model_validate mapping camelCase)
- `CategoryTreeNode`: id, name, description, sort_order, children (list of CategoryTreeNode, default [])

**service.py — CategoryService methods:**
- `list_all() → list[CategoryResponse]` — all non-deleted, ordered by sort_order, name
- `get_tree() → list[CategoryTreeNode]` — fetch all non-deleted, build tree in-memory (parent_id=None are roots; attach children)
- `get_by_id(id) → CategoryResponse` — raises NotFoundError if not found or deleted
- `create(input) → CategoryResponse` — if parent_id given, verify parent exists; create
- `update(id, input) → CategoryResponse` — raises NotFoundError; apply partial update (only non-None fields)
- `delete(id) → None` — soft delete (set deletedAt = now); raises NotFoundError; raises ValidationError if category has active products

**repository.py — CategoryRepository methods:**
- `find_all() → list[Category]` — where deletedAt=None, order by sortOrder ASC, name ASC
- `find_by_id(id) → Category | None` — where deletedAt=None
- `find_children(parent_id) → list[Category]` — where parentId=parent_id and deletedAt=None
- `create(data: dict) → Category`
- `update(id, data: dict) → Category`
- `soft_delete(id) → Category`
- `has_active_products(category_id) → bool` — count products where categoryId=category_id and deletedAt=None > 0

**router.py:**
```
GET    /categories         → list_categories   (all authenticated)
GET    /categories/tree    → get_tree          (all authenticated)
POST   /categories         → create_category   [admin, manager]
PUT    /categories/:id     → update_category   [admin, manager]
DELETE /categories/:id     → delete_category   [admin]
```
Route `/tree` MUST be registered before `/:id`.

---

### Module: Products (`src/modules/products/`)

Files to create:
```
backend/src/modules/products/
├── router.py
├── controller.py
├── service.py
├── repository.py
├── schemas.py
└── CONTEXT.md
```

**schemas.py:**
- `ProductCreate`: name (required), sku (required), barcode (optional), category_id (optional), description (optional), unit_price (int ≥ 0, default 0), cost_price (int ≥ 0, default 0), tax_rate (Decimal/float 0-100, default 0), stock_quantity (int ≥ 0, default 0), min_stock_level (int ≥ 0, default 0), unit_of_measure (str, default "pcs"), image_url (optional), is_active (bool, default True)
- `ProductUpdate`: all fields optional
- `ProductResponse`: id, name, sku, barcode, category_id, description, unit_price, cost_price, tax_rate (float), stock_quantity, min_stock_level, unit_of_measure, image_url, is_active, created_at
- `ImportResult`: created (int), skipped (int), errors (list of dict {row, sku, reason})

**service.py — ProductService methods:**
- `list_products(page, limit, search, category_id, is_active, sort, order) → PaginatedProducts`
- `get_low_stock() → list[ProductResponse]` — where stock_quantity < min_stock_level and is_active=True and deletedAt=None
- `get_by_id(id) → ProductResponse` — raises NotFoundError
- `create(input: ProductCreate) → ProductResponse` — check SKU uniqueness, check barcode uniqueness if provided
- `update(id, input: ProductUpdate) → ProductResponse` — raises NotFoundError; if sku changed, check uniqueness; if barcode changed, check uniqueness
- `delete(id) → None` — soft delete; raises NotFoundError
- `import_from_csv(contents: bytes) → dict` — parse CSV, create products, return ImportResult

**repository.py — ProductRepository methods:**
- `find_paginated(skip, take, where, order_by) → tuple[list[Product], int]`
- `find_low_stock() → list[Product]`
- `find_by_id(id) → Product | None`
- `find_by_sku(sku) → Product | None`
- `find_by_barcode(barcode) → Product | None`
- `create(data: dict) → Product`
- `update(id, data: dict) → Product`
- `soft_delete(id) → Product`

**router.py** — register in this exact order to avoid route conflicts:
```
GET    /products            → list_products    (all authenticated)
GET    /products/low-stock  → low_stock        (all authenticated)
POST   /products/import     → import_products  [admin]  ← BEFORE /{id}
GET    /products/{id}       → get_product      (all authenticated)
POST   /products            → create_product   [admin, manager]
PUT    /products/{id}       → update_product   [admin, manager]
DELETE /products/{id}       → delete_product   [admin]
```

---

### Register routers in `backend/src/main.py`

Add to imports and `app.include_router(...)`:
```python
from src.modules.categories.router import router as categories_router
from src.modules.products.router import router as products_router

app.include_router(categories_router, prefix="/api")
app.include_router(products_router, prefix="/api")
```

---

### Tests

**Unit tests** — mock the repository:

`tests/unit/modules/categories/test_service.py`:
- TestListAll: list returns all categories
- TestGetTree: builds correct parent-child tree structure
- TestCreate: happy path; parent_id not found raises NotFoundError
- TestUpdate: happy path; not found raises NotFoundError
- TestDelete: happy path; has active products raises ValidationError; not found raises NotFoundError

`tests/unit/modules/products/test_service.py`:
- TestListProducts: happy path with pagination
- TestGetLowStock: returns only products where stock < min
- TestGetById: happy path; not found raises NotFoundError
- TestCreate: happy path; duplicate SKU raises ConflictError; duplicate barcode raises ConflictError
- TestUpdate: happy path; not found raises NotFoundError; SKU conflict raises ConflictError
- TestDelete: happy path; not found raises NotFoundError
- TestImportFromCSV: success case (2 created); duplicate SKU row is skipped (counted in skipped); missing required field row counted in errors

`tests/unit/modules/products/test_schemas.py`:
- ProductCreate requires name and sku
- unit_price must be >= 0
- cost_price must be >= 0

**Integration tests** — TestClient with mocked DB:

`tests/integration/test_categories_api.py`:
- GET /api/categories — returns 200 list
- GET /api/categories/tree — returns 200 nested tree
- POST /api/categories — 201 with admin token; 403 with staff token; 422 on missing name
- PUT /api/categories/:id — 200 with manager token; 404 on missing id
- DELETE /api/categories/:id — 200 with admin token; 403 with manager token

`tests/integration/test_products_api.py`:
- GET /api/products — returns 200 paginated list
- GET /api/products/low-stock — returns 200 list
- GET /api/products/:id — returns 200; 404 on missing
- POST /api/products — 201 with manager token; 403 with staff token; 422 on missing sku
- PUT /api/products/:id — 200 with admin token; 404 on missing
- DELETE /api/products/:id — 200 with admin; 403 with manager
- POST /api/products/import — 200 with CSV file

Follow the EXACT test pattern from `tests/integration/test_auth.py`:
- Use `_make_db()` helper to build mock Prisma client
- Use `_make_client(mock_db)` to build TestClient
- Mock `db.category.find_many`, `db.category.find_first`, `db.category.create`, `db.category.update`, `db.category.count`
- Mock `db.product.find_many`, `db.product.find_first`, `db.product.create`, `db.product.update`, `db.product.count`

## Acceptance Criteria

- [ ] `GET /api/categories` returns flat list of all non-deleted categories
- [ ] `GET /api/categories/tree` returns parent→children nested structure
- [ ] `POST /api/categories` creates category; 403 for staff
- [ ] `PUT /api/categories/:id` updates; 404 if not found
- [ ] `DELETE /api/categories/:id` soft deletes; fails if category has active products
- [ ] `GET /api/products` returns paginated list; search, category_id, is_active, sort, order all work
- [ ] `GET /api/products/low-stock` returns products where stock_quantity < min_stock_level
- [ ] `GET /api/products/:id` returns product detail; 404 if not found
- [ ] `POST /api/products` creates product; 409 on duplicate SKU or barcode
- [ ] `PUT /api/products/:id` updates; 404 if not found
- [ ] `DELETE /api/products/:id` soft deletes; 403 for non-admin
- [ ] `POST /api/products/import` processes CSV; returns created/skipped/errors counts
- [ ] `pytest` exits 0 (all tests pass)
- [ ] `ruff check backend/src/modules/categories backend/src/modules/products` exits 0
- [ ] Routers registered in main.py

## Files to Create/Modify

**Create:**
- `backend/src/modules/categories/router.py`
- `backend/src/modules/categories/controller.py`
- `backend/src/modules/categories/service.py`
- `backend/src/modules/categories/repository.py`
- `backend/src/modules/categories/schemas.py`
- `backend/src/modules/categories/CONTEXT.md`
- `backend/src/modules/products/router.py`
- `backend/src/modules/products/controller.py`
- `backend/src/modules/products/service.py`
- `backend/src/modules/products/repository.py`
- `backend/src/modules/products/schemas.py`
- `backend/src/modules/products/CONTEXT.md`
- `backend/tests/unit/modules/categories/test_service.py`
- `backend/tests/unit/modules/products/test_service.py`
- `backend/tests/unit/modules/products/test_schemas.py`
- `backend/tests/integration/test_categories_api.py`
- `backend/tests/integration/test_products_api.py`

**Modify:**
- `backend/src/main.py` — add two `include_router` calls

## Known Pitfalls

- Route order matters: `/low-stock` and `/import` must be registered BEFORE `/{product_id}` in the router.
- Similarly `/tree` must be before `/:id` in categories router.
- Prisma uses camelCase in Python: `deletedAt`, `categoryId`, `unitPrice`, etc.
- `taxRate` is a `Decimal` in Prisma — convert to `float(obj.taxRate)` in model_validate.
- When building Prisma `where` dicts for filters, never pass `None` as a filter value — only include keys that have actual values.
- For soft delete: set `deletedAt` to `datetime.now(timezone.utc)`, do NOT use `deleted_at`.
- CSV import uses `python-multipart` for file upload — already in requirements. Use `UploadFile` from fastapi.
- Prisma `update` requires a `where` dict: `await self.prisma.category.update(where={"id": id}, data={...})`
- `find_many` with `order` parameter expects a list: `order=[{"name": "asc"}]`
- For `get_tree`: do NOT make N+1 queries. Fetch all at once, then build tree in-memory in the service.

## Exit Signal

```bash
cd /Users/abdullah/projects/shoperp-workspace/backend
python -m pytest tests/unit/modules/categories/ tests/unit/modules/products/ tests/integration/test_categories_api.py tests/integration/test_products_api.py -v
# Expected: all tests pass (exit 0)

ruff check src/modules/categories src/modules/products
# Expected: no errors
```

## Outcome (filled by Lead after merge)

- **Date:** 2026-04-11
- **QA verdict:** APPROVED (after 1 fix cycle — 1 blocker, 2 warnings)
- **Tests:** 73 new, 259 total passing
- **Ruff:** clean
- **Blocker fixed:** `has_active_products` was missing `isActive=True` filter — deactivated products were incorrectly blocking category deletion
- **Files created:** 22 (12 source + 10 test)
- **Merge commit:** phase/2-products-categories
