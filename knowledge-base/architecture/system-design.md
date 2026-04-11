# ShopERP — System Design

## System Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   React SPA  │────▶│  FastAPI     │────▶│ PostgreSQL   │
│  (Vite/TS)   │◀────│  (Python)    │◀────│ + Prisma     │
│  port 5173   │     │  port 8000   │     │  port 5432   │
└──────────────┘     └──────────────┘     └──────────────┘
```

Type: Monolithic. Single backend, single frontend, single database. No microservices.

## Backend Architecture

### Layered Structure

```
HTTP Request
  → FastAPI Router (URL mapping)
    → Controller (parse, validate, delegate, respond)
      → Service (ALL business logic)
        → Repository (database queries via Prisma)
          → PostgreSQL
```

Each layer has exactly one job. No layer may skip a level.

### Module File Layout

```
src/
├── main.py                    → FastAPI app creation, middleware, router registration
├── config.py                  → Environment variable loading, app settings
├── database.py                → Prisma client initialization
├── middleware/
│   ├── auth.py                → JWT verification, current user injection
│   ├── error_handler.py       → Global exception → HTTP response mapping
│   └── role_guard.py          → Role-based access control decorator
├── shared/
│   ├── errors.py              → AppError, NotFoundError, ValidationError, ConflictError, ForbiddenError
│   ├── response.py            → success_response(), error_response(), paginated_response()
│   ├── pagination.py          → PaginationParams, paginate() helper
│   └── constants.py           → MAX_PAGE_SIZE, DEFAULT_PAGE_SIZE, currency, timezone
├── modules/
│   ├── auth/                  → register, login, logout, me, change password
│   ├── categories/            → CRUD, tree
│   ├── products/              → CRUD, search, filter, import, low-stock
│   ├── inventory/             → movements, adjust, valuation
│   ├── suppliers/             → CRUD, purchase history
│   ├── purchases/             → PO lifecycle, receiving
│   ├── promotions/            → CRUD, active, discount calculation
│   ├── sales/                 → record, list, detail, daily summary
│   ├── accounting/            → chart of accounts, journal entries, expenses
│   ├── reports/               → all report endpoints
│   └── dashboard/             → summary, trends
```

### Error Handling Chain

```python
class AppError(Exception):
    def __init__(self, status_code: int, message: str, code: str):
        self.status_code = status_code
        self.message = message
        self.code = code

class NotFoundError(AppError):       # 404
class ValidationError(AppError):     # 400
class ConflictError(AppError):       # 409
class UnauthorizedError(AppError):   # 401
class ForbiddenError(AppError):      # 403
```

Global error handler middleware catches all AppError subclasses and returns the standard error response format. Unhandled exceptions return 500 with a generic message (never expose stack traces).

### Authentication Flow

```
POST /auth/login (email, password)
  → Verify credentials against bcrypt hash
  → Generate JWT with {user_id, role, exp}
  → Set JWT in HTTP-only, Secure, SameSite=Lax cookie
  → Return user profile

Every subsequent request:
  → Auth middleware reads cookie
  → Verifies JWT signature and expiry
  → Loads user from database
  → Injects current_user into request state
  → If invalid/expired → 401 Unauthorized
```

### Data Flow: Recording a Sale

```
POST /sales {items: [{product_id, quantity, unit_price}], payment_method, promotion_id?}
  → Controller: validate input with SaleCreateSchema
  → Service: BEGIN TRANSACTION
    → Calculate subtotals per item
    → If promotion_id: validate promotion is active, calculate discount
    → If no promotion_id: find best active promotion, apply automatically
    → Calculate tax per item based on product tax_rate
    → Calculate sale total: subtotal - discount + tax
    → For each item:
      → Verify product exists and is active
      → Verify sufficient stock (stock_quantity >= sale quantity)
      → Deduct stock: UPDATE products SET stock_quantity = stock_quantity - N
      → Create stock_movement: type=out, reference_type=sale
    → Insert sale record with sale_number (auto-generated)
    → Insert sale_items
    → Create journal_entry: debit Cash, credit Sales Revenue
    → Insert journal_entry_lines
  → Service: COMMIT
  → Return sale with calculated totals
```

## Frontend Architecture

```
client/src/
├── main.tsx                    → App entry, providers
├── App.tsx                     → Route definitions
├── components/
│   ├── common/                 → Button, Input, Modal, Table, Pagination, Badge, Card
│   └── layout/                 → Sidebar, Header, PageWrapper, ProtectedRoute
├── pages/
│   ├── auth/                   → LoginPage
│   ├── dashboard/              → DashboardPage
│   ├── products/               → ListPage, FormPage, DetailPage
│   ├── inventory/              → MovementsPage, AdjustPage
│   ├── suppliers/              → ListPage, FormPage, DetailPage
│   ├── purchases/              → ListPage, FormPage, DetailPage, ReceivePage
│   ├── promotions/             → ListPage, FormPage, DetailPage
│   ├── sales/                  → ListPage, FormPage, DetailPage
│   ├── accounting/             → AccountsPage, JournalPage, ExpensesPage
│   └── reports/                → SalesReport, ProfitLoss, InventoryReport
├── services/                   → API call functions per module
├── hooks/                      → React Query hooks per module
├── types/                      → TypeScript interfaces per module
├── lib/
│   ├── api.ts                  → Axios instance with interceptors
│   ├── auth.ts                 → Auth context, useAuth hook
│   └── utils.ts                → formatCurrency, formatDate, etc.
```

### State Management

- Server state: TanStack Query for all API data (caching, refetch, optimistic updates)
- Form state: React Hook Form + Zod for validation
- Auth state: React Context for current user
- No Redux. The app does not need global client state beyond auth.

## Security

- JWT in HTTP-only cookies (XSS protection)
- Bcrypt password hashing (12 salt rounds)
- Role-based middleware on all mutation endpoints
- Pydantic input validation on all endpoints
- Parameterized queries via Prisma (SQL injection prevention)
- CORS configured for frontend origin only
- Rate limiting on auth endpoints (10 attempts per minute)
