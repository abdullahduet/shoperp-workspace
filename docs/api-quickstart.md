# ShopERP — API Quick-Start Guide

> **Audience:** Developers who have `docker compose up --build` running and want to create accounts and start making API calls.
>
> Base URL: `http://localhost:8000/api`
> Interactive docs: `http://localhost:8000/docs`

---

## 1. Bootstrapping: Creating the First Admin User

There is **no automatic seed for users**. The `/api/auth/register` endpoint is protected — it requires an existing admin session. This creates a chicken-and-egg problem for the very first user, which is solved by inserting the admin directly into the database.

### Option A — Python one-liner via Docker (recommended)

Run this in your terminal with the containers already up:

```bash
docker compose exec backend python - <<'EOF'
import asyncio, os
from prisma import Prisma
from passlib.context import CryptContext

pwd = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
password_hash = pwd.hash("Admin1234!")

async def main():
    db = Prisma()
    await db.connect()
    user = await db.user.create(data={
        "email": "admin@shoperp.com",
        "passwordHash": password_hash,
        "name": "Super Admin",
        "role": "admin",
        "isActive": True,
    })
    print(f"Created: {user.email}  role={user.role}  id={user.id}")
    await db.disconnect()

asyncio.run(main())
EOF
```

This creates:

| Field    | Value             |
|----------|-------------------|
| Email    | admin@shoperp.com |
| Password | Admin1234!        |
| Role     | admin             |

Change the password immediately after your first login (see §4).

### Option B — Direct SQL via psql

If you prefer SQL:

```bash
docker compose exec db psql -U shoperp -d shoperp
```

Then paste this (the hash below is bcrypt, 12 rounds, for the password `Admin1234!`):

```sql
INSERT INTO users (email, password_hash, name, role, is_active)
VALUES (
    'admin@shoperp.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj/o9lkMRIi2',
    'Super Admin',
    'admin',
    true
);
```

> **Note:** If you want a different password, use Option A and change `"Admin1234!"` to your chosen password — it will be hashed correctly automatically.

---

## 2. Logging In (and the Cookie)

The API uses **HttpOnly cookies** for auth — not Bearer tokens. This is intentional: the cookie is set on login and sent automatically on every subsequent request, preventing XSS token theft.

### Login request

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "admin@shoperp.com",
  "password": "Admin1234!"
}
```

**Response:**

```json
{
  "success": true,
  "data": {
    "id": "...",
    "email": "admin@shoperp.com",
    "name": "Super Admin",
    "role": "admin",
    "is_active": true,
    "last_login_at": null,
    "created_at": "2026-04-12T..."
  },
  "message": "Login successful"
}
```

The response also sets an `HttpOnly` cookie named `access_token` (7-day expiry). Every subsequent request must carry this cookie.

---

## 3. Configuring Postman for Cookie Auth

Postman does **not** send cookies automatically unless you configure it. Follow these steps once:

### Step 1 — Enable cookie capture for localhost

1. Click the **Cookies** button (top-right of any request, near **Send**)
2. In the Cookies dialog → **Domains** tab → add `localhost`
3. Click **Close**

### Step 2 — Send the login request

1. `POST http://localhost:8000/api/auth/login`
2. Body → Raw → JSON:
   ```json
   { "email": "admin@shoperp.com", "password": "Admin1234!" }
   ```
3. Click **Send**
4. In the **Cookies** tab of the response panel you will see `access_token` set for `localhost`

### Step 3 — All subsequent requests just work

Postman automatically attaches the `access_token` cookie to every request to `localhost:8000`. No manual header needed. The session lasts 7 days.

### Step 4 — Log out

```http
POST /api/auth/logout
```

This clears the cookie server-side. Your next request will return `401`.

---

## 4. Step-by-Step API Flow (New Installation)

Follow this sequence to go from zero to a working shop:

### Step 1 — Bootstrap and log in

```http
POST /api/auth/login    { "email": "admin@shoperp.com", "password": "Admin1234!" }
```

### Step 2 — Change the default password

```http
PUT /api/auth/me/password
{ "current_password": "Admin1234!", "new_password": "YourSecurePassword!" }
```

### Step 3 — Create staff accounts

```http
POST /api/auth/register
{ "email": "manager@example.com", "name": "Store Manager", "password": "...", "role": "manager" }
```

Repeat for each user. Valid roles: `admin`, `manager`, `staff`.

### Step 4 — Set up product categories

```http
POST /api/categories
{ "name": "Beverages", "description": "Drinks and juices" }
```

### Step 5 — Add products

```http
POST /api/products
{
  "name": "Mango Juice 1L",
  "sku": "MJ-001",
  "category_id": "<category-uuid>",
  "unit_price": 15000,
  "cost_price": 10000,
  "tax_rate": "0.00",
  "stock_quantity": 50,
  "min_stock_level": 10
}
```

> All money values are in **paisa** (1 BDT = 100 paisa). `15000` = ৳150.00

### Step 6 — Add a supplier and create a purchase order

```http
POST /api/suppliers
{ "name": "ABC Distributors", "country": "Bangladesh" }

POST /api/purchase-orders
{
  "supplier_id": "<supplier-uuid>",
  "items": [{ "product_id": "<product-uuid>", "quantity": 100, "unit_cost": 9500 }]
}

POST /api/purchase-orders/<id>/submit
POST /api/purchase-orders/<id>/receive
{ "items": [{ "purchase_order_item_id": "<item-uuid>", "received_quantity": 100 }] }
```

Receiving stock automatically creates a `StockMovement` record and updates `product.stock_quantity`.

### Step 7 — Record a sale

```http
POST /api/sales
{
  "customer_name": "Walk-in",
  "payment_method": "cash",
  "items": [{ "product_id": "<uuid>", "quantity": 2, "unit_price": 15000 }]
}
```

The server automatically: deducts stock, applies the best active promotion, computes tax, creates a journal entry, and generates a `SALE-YYYYMMDD-NNN` sale number.

### Step 8 — View dashboard & reports

```http
GET /api/dashboard/summary
GET /api/dashboard/trends
GET /api/reports/profit-loss?start_date=2026-04-01&end_date=2026-04-30
GET /api/reports/sales?format=csv
```

---

## 5. Role Permissions Reference

| Endpoint | staff | manager | admin |
|----------|:-----:|:-------:|:-----:|
| **Auth** | | | |
| POST /auth/login | ✓ | ✓ | ✓ |
| GET /auth/me | ✓ | ✓ | ✓ |
| POST /auth/logout | ✓ | ✓ | ✓ |
| PUT /auth/me/password | ✓ | ✓ | ✓ |
| POST /auth/register | — | — | ✓ |
| **Categories** | | | |
| GET /categories, /categories/tree, /categories/:id | ✓ | ✓ | ✓ |
| POST /categories, PUT /categories/:id | — | ✓ | ✓ |
| DELETE /categories/:id | — | — | ✓ |
| **Products** | | | |
| GET /products, /products/low-stock, /products/:id | ✓ | ✓ | ✓ |
| POST /products, PUT /products/:id | — | ✓ | ✓ |
| POST /products/import | — | — | ✓ |
| DELETE /products/:id | — | — | ✓ |
| **Inventory** | | | |
| GET /inventory/movements | ✓ | ✓ | ✓ |
| POST /inventory/adjust | — | ✓ | ✓ |
| GET /inventory/valuation | — | ✓ | ✓ |
| **Suppliers** | | | |
| GET /suppliers, /suppliers/:id | ✓ | ✓ | ✓ |
| POST /suppliers, PUT /suppliers/:id | — | ✓ | ✓ |
| DELETE /suppliers/:id | — | — | ✓ |
| **Purchase Orders** | | | |
| GET /purchase-orders, /purchase-orders/:id | ✓ | ✓ | ✓ |
| POST, PUT, submit, receive, cancel | — | ✓ | ✓ |
| DELETE /purchase-orders/:id | — | — | ✓ |
| **Promotions** | | | |
| GET /promotions, /promotions/active, /promotions/:id | ✓ | ✓ | ✓ |
| POST /promotions, PUT /promotions/:id | — | ✓ | ✓ |
| DELETE /promotions/:id | — | ✓ | ✓ |
| **Sales** | | | |
| GET /sales, /sales/:id | ✓ | ✓ | ✓ |
| POST /sales (record sale) | ✓ | ✓ | ✓ |
| GET /sales/daily-summary | — | ✓ | ✓ |
| **Accounting** | | | |
| GET /accounting/accounts | — | ✓ | ✓ |
| GET /accounting/journal-entries | — | ✓ | ✓ |
| POST /accounting/journal-entries | — | — | ✓ |
| **Expenses** | | | |
| GET /expenses, POST /expenses, PUT /expenses/:id | — | ✓ | ✓ |
| DELETE /expenses/:id | — | — | ✓ |
| **Reports** | | | |
| GET /reports/low-stock | ✓ | ✓ | ✓ |
| GET /reports/sales, profit-loss, top-products, purchases, expenses, inventory-valuation | — | ✓ | ✓ |
| All reports support `?format=csv` for file download | — | ✓ | ✓ |
| **Dashboard** | | | |
| GET /dashboard/summary | — | ✓ | ✓ |
| GET /dashboard/trends | — | ✓ | ✓ |

---

## 6. Common Response Shapes

**Success (single object):**
```json
{ "success": true, "data": { ... }, "message": "..." }
```

**Success (list with pagination):**
```json
{
  "success": true,
  "data": [ ... ],
  "pagination": { "page": 1, "limit": 20, "total": 45, "total_pages": 3 }
}
```

**Error:**
```json
{ "success": false, "error": "...", "code": "NOT_FOUND", "details": [] }
```

**Common HTTP status codes:**

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Validation error / bad request |
| 401 | Not authenticated (no cookie / expired) |
| 403 | Authenticated but wrong role |
| 404 | Record not found |
| 409 | Conflict (duplicate SKU, email, etc.) |
| 422 | Unprocessable (e.g. insufficient stock, unbalanced journal entry) |

---

## 7. Quick Reference: Key Query Parameters

| Endpoint | Parameters |
|----------|-----------|
| GET /products | `page`, `limit`, `search`, `category_id`, `is_active`, `sort_by`, `order` |
| GET /sales | `page`, `limit`, `start_date`, `end_date`, `payment_method` |
| GET /purchase-orders | `page`, `limit`, `supplier_id`, `status` |
| GET /inventory/movements | `page`, `limit`, `product_id`, `movement_type`, `start_date`, `end_date` |
| GET /accounting/journal-entries | `page`, `limit`, `start_date`, `end_date`, `reference_type` |
| GET /expenses | `page`, `limit`, `start_date`, `end_date`, `category` |
| GET /reports/* | `start_date`, `end_date`, `format=csv` |
| GET /reports/top-products | `start_date`, `end_date`, `limit` (default 10) |
