# ShopERP — Coding Standards

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Python files | snake_case | `product_service.py` |
| Python classes | PascalCase | `ProductService` |
| Python functions | snake_case | `get_product_by_id()` |
| Constants | UPPER_SNAKE | `MAX_PAGE_SIZE` |
| Pydantic models | PascalCase | `ProductCreate` |
| DB tables | snake_case plural | `purchase_orders` |
| DB columns | snake_case | `unit_price` |
| API routes | kebab-case | `/purchase-orders` |
| React components | PascalCase file | `ProductListPage.tsx` |
| React hooks | camelCase use- | `useProducts.ts` |
| TypeScript types | PascalCase | `Product` |

## Python Backend Patterns

### Controller (thin — validate, delegate, respond)
```python
async def create_product(body: ProductCreate, user: User = Depends(get_current_user)):
    result = await product_service.create(body, user)
    return success_response(data=result, message="Product created", status_code=201)
```

### Service (ALL business logic)
```python
async def create(self, input: ProductCreate, user: User) -> ProductResponse:
    existing = await self.repo.find_by_sku(input.sku)
    if existing:
        raise ConflictError(f"Product with SKU '{input.sku}' already exists")
    return await self.repo.create(input.model_dump())
```

### Repository (database only)
```python
async def find_by_sku(self, sku: str) -> Product | None:
    return await self.prisma.product.find_first(where={"sku": sku, "deleted_at": None})
```

## React Frontend Patterns

### Component structure: imports → hooks → early returns → render
### API services: typed functions wrapping axios calls
### Hooks: TanStack Query wrappers per module
### Every page handles: loading, error, empty states

## General Rules

- No `any` in TypeScript.
- No `# TODO` in committed code.
- No commented-out code.
- Functions under 30 lines.
- Files under 300 lines.
- Always handle errors. No empty except/catch.
- Type hints on all Python function signatures.
- Comments explain WHY, not WHAT.

## Git Commits

```
type(scope): description
Types: feat, fix, refactor, test, docs, chore, ci
Example: feat(products): add CSV import endpoint
```
