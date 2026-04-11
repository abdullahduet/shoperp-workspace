# ShopERP — API Contracts

## Base URL: `http://localhost:8000/api`

## Standard Response Shapes

```python
# Success single: {"success": True, "data": {...}, "message": "..."}
# Success list:   {"success": True, "data": [...], "pagination": {"page": 1, "limit": 20, "total": N, "total_pages": N}}
# Error:          {"success": False, "error": "...", "code": "ERROR_CODE", "details": [...]}
```

## Auth

| Method | Path | Description | Auth | Roles |
|--------|------|-------------|------|-------|
| POST | /auth/register | Create user account | Yes | admin |
| POST | /auth/login | Login, set JWT cookie | No | — |
| POST | /auth/logout | Clear JWT cookie | Yes | all |
| GET | /auth/me | Current user profile | Yes | all |
| PUT | /auth/me/password | Change password | Yes | all |

## Categories

| Method | Path | Description | Auth | Roles |
|--------|------|-------------|------|-------|
| GET | /categories | List all categories | Yes | all |
| GET | /categories/tree | Nested category tree | Yes | all |
| POST | /categories | Create category | Yes | admin, manager |
| PUT | /categories/:id | Update category | Yes | admin, manager |
| DELETE | /categories/:id | Soft delete | Yes | admin |

## Products

| Method | Path | Description | Auth | Roles |
|--------|------|-------------|------|-------|
| GET | /products | Paginated list | Yes | all |
| GET | /products/:id | Detail | Yes | all |
| POST | /products | Create | Yes | admin, manager |
| PUT | /products/:id | Update | Yes | admin, manager |
| DELETE | /products/:id | Soft delete | Yes | admin |
| POST | /products/import | CSV import | Yes | admin |
| GET | /products/low-stock | Below min level | Yes | all |

Query params for GET /products: `page`, `limit`, `search` (name, SKU), `category_id`, `is_active`, `sort` (name, sku, stock_quantity, unit_price), `order` (asc, desc)

## Inventory

| Method | Path | Description | Auth | Roles |
|--------|------|-------------|------|-------|
| GET | /inventory/movements | Stock movement history | Yes | all |
| POST | /inventory/adjust | Manual adjustment | Yes | admin, manager |
| GET | /inventory/valuation | Total inventory value | Yes | admin, manager |

Query params for movements: `product_id`, `movement_type`, `start_date`, `end_date`, `page`, `limit`

## Suppliers

| Method | Path | Description | Auth | Roles |
|--------|------|-------------|------|-------|
| GET | /suppliers | Paginated list | Yes | all |
| GET | /suppliers/:id | Detail | Yes | all |
| POST | /suppliers | Create | Yes | admin, manager |
| PUT | /suppliers/:id | Update | Yes | admin, manager |
| DELETE | /suppliers/:id | Soft delete | Yes | admin |
| GET | /suppliers/:id/purchases | PO history | Yes | admin, manager |

## Purchase Orders

| Method | Path | Description | Auth | Roles |
|--------|------|-------------|------|-------|
| GET | /purchase-orders | Paginated list | Yes | admin, manager |
| GET | /purchase-orders/:id | Detail with items | Yes | admin, manager |
| POST | /purchase-orders | Create (draft) | Yes | admin, manager |
| PUT | /purchase-orders/:id | Update draft PO | Yes | admin, manager |
| DELETE | /purchase-orders/:id | Delete draft PO | Yes | admin |
| POST | /purchase-orders/:id/submit | Draft → Ordered | Yes | admin, manager |
| POST | /purchase-orders/:id/receive | Receive items | Yes | admin, manager |
| POST | /purchase-orders/:id/cancel | Cancel PO | Yes | admin |

## Promotions

| Method | Path | Description | Auth | Roles |
|--------|------|-------------|------|-------|
| GET | /promotions | All promotions | Yes | all |
| GET | /promotions/active | Currently active | Yes | all |
| GET | /promotions/:id | Detail | Yes | all |
| POST | /promotions | Create | Yes | admin, manager |
| PUT | /promotions/:id | Update | Yes | admin, manager |
| DELETE | /promotions/:id | Soft delete | Yes | admin |

## Sales

| Method | Path | Description | Auth | Roles |
|--------|------|-------------|------|-------|
| GET | /sales | Paginated list | Yes | all |
| GET | /sales/:id | Detail with items | Yes | all |
| POST | /sales | Record a sale | Yes | all |
| GET | /sales/daily-summary | Today summary | Yes | admin, manager |

## Accounting

| Method | Path | Description | Auth | Roles |
|--------|------|-------------|------|-------|
| GET | /accounting/accounts | Chart of accounts | Yes | admin, manager |
| GET | /accounting/journal-entries | Journal entries | Yes | admin, manager |
| POST | /accounting/journal-entries | Manual entry | Yes | admin |
| GET | /expenses | List expenses | Yes | admin, manager |
| POST | /expenses | Record expense | Yes | admin, manager |
| PUT | /expenses/:id | Update expense | Yes | admin, manager |
| DELETE | /expenses/:id | Soft delete | Yes | admin |

## Reports

| Method | Path | Description | Auth | Roles |
|--------|------|-------------|------|-------|
| GET | /reports/sales | Sales report | Yes | admin, manager |
| GET | /reports/profit-loss | P&L statement | Yes | admin, manager |
| GET | /reports/top-products | Top selling | Yes | admin, manager |
| GET | /reports/low-stock | Low stock | Yes | all |
| GET | /reports/purchases | Purchase summary | Yes | admin, manager |
| GET | /reports/expenses | Expense breakdown | Yes | admin, manager |
| GET | /reports/inventory-valuation | Inventory value | Yes | admin, manager |

Common report params: `start_date`, `end_date`, `format` (json, csv)

## Dashboard

| Method | Path | Description | Auth | Roles |
|--------|------|-------------|------|-------|
| GET | /dashboard/summary | Today + month stats | Yes | admin, manager |
| GET | /dashboard/trends | Monthly sales (12mo) | Yes | admin, manager |

## Health

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | /health | App health check | No |
