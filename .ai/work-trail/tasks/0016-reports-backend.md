# Task 0016: Reports + Dashboard Backend

## Branch: task/0016-reports-backend

## Context Bundle

### Relevant Schema (key fields used in reports)

```
Sale: id, saleDate (Timestamptz), totalAmount, paymentMethod, deletedAt
      → saleItems: [{ quantity, unitPrice, totalPrice, productId → product.costPrice }]

SaleItem: saleId, productId, quantity, unitPrice, totalPrice
          → product: { name, sku, costPrice }

PurchaseOrder: id, orderDate (Date), totalAmount, status, deletedAt

Expense: id, date (Date), category, amount, deletedAt

Product: id, name, sku, stockQuantity, minStockLevel, costPrice, isActive, deletedAt

Account / JournalEntry — not needed for reports (reports derive from source tables)
```

**Prisma client model names:** `prisma.sale`, `prisma.saleitem`, `prisma.purchaseorder`, `prisma.expense`, `prisma.product`

**Prisma `@db.Date` columns** (PurchaseOrder.orderDate, Expense.date) → Python `datetime`, use `.date()` method to get `date` object. Filter with Python `date` objects.

**Prisma `@db.Timestamptz` columns** (Sale.saleDate) → Python `datetime` with timezone. Filter with `datetime` objects.

### Relevant API Endpoints

**Prefix: `/api/reports`** — all require admin or manager. `format` param applies to all.

| Method | Path | Params | Description |
|--------|------|--------|-------------|
| GET | `/api/reports/sales` | start_date, end_date, format | Daily sales breakdown |
| GET | `/api/reports/profit-loss` | start_date, end_date, format | P&L report |
| GET | `/api/reports/top-products` | start_date, end_date, limit (default 10), format | Top selling products |
| GET | `/api/reports/low-stock` | format | Products below min level (all roles) |
| GET | `/api/reports/purchases` | start_date, end_date, format | Daily purchase breakdown |
| GET | `/api/reports/expenses` | start_date, end_date, format | Expenses grouped by category |
| GET | `/api/reports/inventory-valuation` | format | Current inventory value with items |

**Prefix: `/api/dashboard`** — admin and manager only.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/dashboard/summary` | Today + this month stats |
| GET | `/api/dashboard/trends` | Monthly sales for last 12 months |

**Dashboard and reports do NOT have parameterized paths** — no route ordering concern.

### Response Shapes

**GET /reports/sales:**
```json
{
  "success": true,
  "data": {
    "period": {"start": "2026-04-01", "end": "2026-04-30"},
    "items": [
      {
        "date": "2026-04-11",
        "total_amount": 350000,
        "transaction_count": 5,
        "payment_breakdown": {"cash": 200000, "card": 100000, "mobile": 50000, "credit": 0}
      }
    ],
    "totals": {
      "total_amount": 350000,
      "transaction_count": 5
    }
  }
}
```

**GET /reports/profit-loss:**
```json
{
  "success": true,
  "data": {
    "period": {"start": "2026-04-01", "end": "2026-04-30"},
    "revenue": 1500000,
    "cogs": 900000,
    "gross_profit": 600000,
    "expenses": 200000,
    "net_profit": 400000
  }
}
```
- Revenue = `sum(sale.totalAmount)` for period
- COGS = `sum(item.quantity * item.product.costPrice)` for all sale items in period (load sales with items + product)
- Expenses = `sum(expense.amount)` for period
- Gross profit = revenue - cogs
- Net profit = gross_profit - expenses

**GET /reports/top-products:**
```json
{
  "success": true,
  "data": {
    "period": {"start": "2026-04-01", "end": "2026-04-30"},
    "items": [
      {"product_id": "...", "name": "Rice 5kg", "sku": "RICE-5KG", "total_quantity": 120, "total_revenue": 600000}
    ]
  }
}
```
- Aggregate sale_items by product_id for period, sorted by total_quantity descending, limited to `limit`
- Load sale_items with product (for name/sku) from sales in the date range

**GET /reports/low-stock:**
```json
{
  "success": true,
  "data": [
    {"id": "...", "name": "Rice 5kg", "sku": "RICE-5KG", "stock_quantity": 2, "min_stock_level": 10}
  ]
}
```
- Active products where stockQuantity < minStockLevel (no date range)

**GET /reports/purchases:**
```json
{
  "success": true,
  "data": {
    "period": {"start": "2026-04-01", "end": "2026-04-30"},
    "items": [
      {"date": "2026-04-05", "total_amount": 500000, "order_count": 2}
    ],
    "totals": {"total_amount": 500000, "order_count": 2}
  }
}
```
- Group PurchaseOrders (not deleted, not cancelled) by orderDate, sum totalAmount
- POs with status="cancelled" are excluded from totals

**GET /reports/expenses:**
```json
{
  "success": true,
  "data": {
    "period": {"start": "2026-04-01", "end": "2026-04-30"},
    "items": [
      {"category": "Rent", "total_amount": 500000, "count": 1},
      {"category": "Utilities", "total_amount": 50000, "count": 2}
    ],
    "totals": {"total_amount": 550000}
  }
}
```

**GET /reports/inventory-valuation:**
```json
{
  "success": true,
  "data": {
    "total_value": 5000000,
    "product_count": 42,
    "currency": "BDT",
    "items": [
      {"product_id": "...", "name": "Rice 5kg", "sku": "RICE-5KG", "stock_quantity": 50, "cost_price": 30000, "value": 1500000}
    ]
  }
}
```
- All active, non-deleted products with stockQuantity > 0

**GET /dashboard/summary:**
```json
{
  "success": true,
  "data": {
    "today_sales": 350000,
    "today_transactions": 5,
    "month_revenue": 3500000,
    "month_profit": 1200000,
    "low_stock_count": 3
  }
}
```
- today = UTC today's date
- month = current calendar month (UTC)
- month_profit = month_revenue - month_expenses (simple: no COGS for now — just revenue minus expenses)

**GET /dashboard/trends:**
```json
{
  "success": true,
  "data": [
    {"month": "2026-04", "revenue": 3500000, "transaction_count": 50},
    {"month": "2026-03", "revenue": 2800000, "transaction_count": 42}
  ]
}
```
- Last 12 months including current month, sorted descending by month
- revenue = sum of sale.totalAmount for that calendar month

### CSV Format

When `format=csv` query param is provided, controller returns CSV instead of JSON:
```python
from fastapi.responses import Response
import csv, io

def to_csv(headers: list[str], rows: list[list]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return output.getvalue()

# Controller:
if format == "csv":
    csv_content = service.generate_csv(data)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=report.csv"},
    )
```

Each service method (or a helper) converts the report data to CSV rows. The CSV helper lives in the service, not the controller (Rule #10/11).

### Relevant Patterns

**Date range parsing (Timestamptz for Sale.saleDate):**
```python
from datetime import datetime, date, timezone, timedelta

def parse_date_range(start_date: str | None, end_date: str | None) -> tuple[datetime, datetime]:
    """Convert YYYY-MM-DD strings to UTC datetime range [start, end+1day)."""
    if start_date:
        start_dt = datetime.combine(date.fromisoformat(start_date), datetime.min.time()).replace(tzinfo=timezone.utc)
    else:
        start_dt = datetime(2000, 1, 1, tzinfo=timezone.utc)
    if end_date:
        end_dt = datetime.combine(date.fromisoformat(end_date), datetime.max.time()).replace(tzinfo=timezone.utc)
    else:
        end_dt = datetime.now(timezone.utc)
    return start_dt, end_dt
```

**Date range parsing (Date for PurchaseOrder.orderDate, Expense.date):**
```python
def parse_date_range_date(start_date: str | None, end_date: str | None) -> tuple[date, date]:
    start = date.fromisoformat(start_date) if start_date else date(2000, 1, 1)
    end = date.fromisoformat(end_date) if end_date else date.today()
    return start, end
```

**Grouping by day (Python, not DB):**
```python
from collections import defaultdict

# Group sales by date
by_date: dict[str, list] = defaultdict(list)
for sale in sales:
    day = sale.saleDate.astimezone(timezone.utc).date().isoformat()
    by_date[day].append(sale)
```

**Top products aggregation:**
```python
from collections import defaultdict

product_totals: dict[str, dict] = {}
for sale in sales:
    for item in sale.saleItems:
        pid = item.productId
        if pid not in product_totals:
            product_totals[pid] = {
                "product_id": pid,
                "name": item.product.name,
                "sku": item.product.sku,
                "total_quantity": 0,
                "total_revenue": 0,
            }
        product_totals[pid]["total_quantity"] += item.quantity
        product_totals[pid]["total_revenue"] += item.totalPrice

sorted_products = sorted(product_totals.values(), key=lambda x: x["total_quantity"], reverse=True)
return sorted_products[:limit]
```

Note: `item.product` requires `include={"saleItems": {"include": {"product": True}}}` in the Prisma query.

**Monthly trends:**
```python
from collections import defaultdict

monthly: dict[str, dict] = defaultdict(lambda: {"revenue": 0, "transaction_count": 0})
for sale in sales:
    month_key = sale.saleDate.astimezone(timezone.utc).strftime("%Y-%m")
    monthly[month_key]["revenue"] += sale.totalAmount
    monthly[month_key]["transaction_count"] += 1

# Return sorted descending by month key (YYYY-MM sorts lexicographically)
return sorted(
    [{"month": k, **v} for k, v in monthly.items()],
    key=lambda x: x["month"],
    reverse=True,
)
```

### Architecture Rules That Apply

- Rule #9: Controllers contain zero business logic — parse params, call service, format response (including CSV conversion).
- Rule #11: ALL aggregation, grouping, and computation in service layer. Repository only fetches raw records.
- Rule #13: No typed exceptions needed for reports (they're read-only, no NotFoundError scenarios).
- Rule #15/16: All report endpoints require auth. Most require admin+manager; `/reports/low-stock` allows all roles.

## What to Build

### Module 1: `backend/src/modules/reports/`

#### `schemas.py`

```python
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

@dataclass
class Period:
    start: str
    end: str

@dataclass
class SalesReportItem:
    date: str
    total_amount: int
    transaction_count: int
    payment_breakdown: dict[str, int]

@dataclass
class SalesReport:
    period: Period
    items: list[SalesReportItem]
    totals: dict[str, int]

@dataclass
class ProfitLossReport:
    period: Period
    revenue: int
    cogs: int
    gross_profit: int
    expenses: int
    net_profit: int

@dataclass
class TopProductItem:
    product_id: str
    name: str
    sku: str
    total_quantity: int
    total_revenue: int

@dataclass
class TopProductsReport:
    period: Period
    items: list[TopProductItem]

@dataclass
class LowStockItem:
    id: str
    name: str
    sku: str
    stock_quantity: int
    min_stock_level: int

@dataclass
class PurchasesReportItem:
    date: str
    total_amount: int
    order_count: int

@dataclass
class PurchasesReport:
    period: Period
    items: list[PurchasesReportItem]
    totals: dict[str, int]

@dataclass
class ExpenseCategoryItem:
    category: str
    total_amount: int
    count: int

@dataclass
class ExpensesReport:
    period: Period
    items: list[ExpenseCategoryItem]
    totals: dict[str, int]

@dataclass
class InventoryValuationItem:
    product_id: str
    name: str
    sku: str
    stock_quantity: int
    cost_price: int
    value: int

@dataclass
class InventoryValuationReport:
    total_value: int
    product_count: int
    currency: str
    items: list[InventoryValuationItem]
```

Use `dataclasses.asdict()` in the controller to serialize before passing to `success_response`.

#### `repository.py`

Methods (DB queries only — no aggregation):

```python
class ReportsRepository:
    def __init__(self, prisma) -> None:
        self.prisma = prisma

    async def find_sales_in_range(self, start: datetime, end: datetime) -> list:
        """Return non-deleted sales in [start, end] (saleDate range)."""
        return await self.prisma.sale.find_many(
            where={"deletedAt": None, "saleDate": {"gte": start, "lte": end}},
            order=[{"saleDate": "asc"}],
        )

    async def find_sales_with_items_in_range(self, start: datetime, end: datetime) -> list:
        """Return sales with saleItems + product included (for COGS and top products)."""
        return await self.prisma.sale.find_many(
            where={"deletedAt": None, "saleDate": {"gte": start, "lte": end}},
            include={"saleItems": {"include": {"product": True}}},
        )

    async def find_expenses_in_range(self, start: date, end: date) -> list:
        """Return non-deleted expenses in [start, end] (date range)."""
        return await self.prisma.expense.find_many(
            where={"deletedAt": None, "date": {"gte": start, "lte": end}},
            order=[{"date": "asc"}],
        )

    async def find_pos_in_range(self, start: date, end: date) -> list:
        """Return non-deleted, non-cancelled POs in [start, end] (orderDate range)."""
        return await self.prisma.purchaseorder.find_many(
            where={
                "deletedAt": None,
                "status": {"not": "cancelled"},
                "orderDate": {"gte": start, "lte": end},
            },
            order=[{"orderDate": "asc"}],
        )

    async def find_low_stock_products(self) -> list:
        """Return active products where stockQuantity < minStockLevel."""
        products = await self.prisma.product.find_many(
            where={"deletedAt": None, "isActive": True},
        )
        return [p for p in products if p.stockQuantity < p.minStockLevel]

    async def find_active_products_with_stock(self) -> list:
        """Return all active non-deleted products (for valuation)."""
        return await self.prisma.product.find_many(
            where={"deletedAt": None, "isActive": True},
        )
```

#### `service.py`

```python
import csv
import io
from collections import defaultdict
from dataclasses import asdict
from datetime import datetime, date, timezone, timedelta
from typing import Optional

from src.modules.reports.repository import ReportsRepository
from src.modules.reports.schemas import (
    Period, SalesReport, SalesReportItem,
    ProfitLossReport, TopProductsReport, TopProductItem,
    LowStockItem, PurchasesReport, PurchasesReportItem,
    ExpensesReport, ExpenseCategoryItem,
    InventoryValuationReport, InventoryValuationItem,
)

class ReportsService:
    def __init__(self, repo: ReportsRepository) -> None:
        self.repo = repo

    def _parse_datetime_range(self, start_date, end_date) -> tuple[datetime, datetime]:
        if start_date:
            s = datetime.combine(date.fromisoformat(start_date), datetime.min.time()).replace(tzinfo=timezone.utc)
        else:
            s = datetime(2000, 1, 1, tzinfo=timezone.utc)
        if end_date:
            e = datetime.combine(date.fromisoformat(end_date), datetime.max.time()).replace(tzinfo=timezone.utc)
        else:
            e = datetime.now(timezone.utc)
        return s, e

    def _parse_date_range(self, start_date, end_date) -> tuple[date, date]:
        s = date.fromisoformat(start_date) if start_date else date(2000, 1, 1)
        e = date.fromisoformat(end_date) if end_date else date.today()
        return s, e

    async def get_sales_report(self, start_date, end_date) -> SalesReport:
        start, end = self._parse_datetime_range(start_date, end_date)
        sales = await self.repo.find_sales_in_range(start, end)

        by_date: dict[str, SalesReportItem] = {}
        for sale in sales:
            day = sale.saleDate.astimezone(timezone.utc).date().isoformat()
            if day not in by_date:
                by_date[day] = SalesReportItem(
                    date=day, total_amount=0, transaction_count=0,
                    payment_breakdown={"cash": 0, "card": 0, "mobile": 0, "credit": 0},
                )
            item = by_date[day]
            item.total_amount += sale.totalAmount
            item.transaction_count += 1
            method = sale.paymentMethod if sale.paymentMethod in item.payment_breakdown else "cash"
            item.payment_breakdown[method] += sale.totalAmount

        items = sorted(by_date.values(), key=lambda x: x.date)
        total_amount = sum(i.total_amount for i in items)
        total_count = sum(i.transaction_count for i in items)
        return SalesReport(
            period=Period(
                start=start_date or "all-time",
                end=end_date or date.today().isoformat(),
            ),
            items=items,
            totals={"total_amount": total_amount, "transaction_count": total_count},
        )

    async def get_profit_loss(self, start_date, end_date) -> ProfitLossReport:
        start, end = self._parse_datetime_range(start_date, end_date)
        date_start, date_end = self._parse_date_range(start_date, end_date)

        sales = await self.repo.find_sales_with_items_in_range(start, end)
        expenses = await self.repo.find_expenses_in_range(date_start, date_end)

        revenue = sum(s.totalAmount for s in sales)
        cogs = sum(
            item.quantity * item.product.costPrice
            for s in sales
            for item in s.saleItems
        )
        total_expenses = sum(e.amount for e in expenses)
        gross_profit = revenue - cogs
        net_profit = gross_profit - total_expenses

        return ProfitLossReport(
            period=Period(
                start=start_date or "all-time",
                end=end_date or date.today().isoformat(),
            ),
            revenue=revenue,
            cogs=cogs,
            gross_profit=gross_profit,
            expenses=total_expenses,
            net_profit=net_profit,
        )

    async def get_top_products(self, start_date, end_date, limit: int = 10) -> TopProductsReport:
        start, end = self._parse_datetime_range(start_date, end_date)
        sales = await self.repo.find_sales_with_items_in_range(start, end)

        product_totals: dict[str, dict] = {}
        for sale in sales:
            for item in sale.saleItems:
                pid = item.productId
                if pid not in product_totals:
                    product_totals[pid] = {
                        "product_id": pid,
                        "name": item.product.name if item.product else "Unknown",
                        "sku": item.product.sku if item.product else "",
                        "total_quantity": 0,
                        "total_revenue": 0,
                    }
                product_totals[pid]["total_quantity"] += item.quantity
                product_totals[pid]["total_revenue"] += item.totalPrice

        sorted_products = sorted(product_totals.values(), key=lambda x: x["total_quantity"], reverse=True)
        items = [TopProductItem(**p) for p in sorted_products[:limit]]

        return TopProductsReport(
            period=Period(
                start=start_date or "all-time",
                end=end_date or date.today().isoformat(),
            ),
            items=items,
        )

    async def get_low_stock(self) -> list[LowStockItem]:
        products = await self.repo.find_low_stock_products()
        return [
            LowStockItem(
                id=p.id, name=p.name, sku=p.sku,
                stock_quantity=p.stockQuantity, min_stock_level=p.minStockLevel,
            )
            for p in products
        ]

    async def get_purchases_report(self, start_date, end_date) -> PurchasesReport:
        date_start, date_end = self._parse_date_range(start_date, end_date)
        pos = await self.repo.find_pos_in_range(date_start, date_end)

        by_date: dict[str, PurchasesReportItem] = {}
        for po in pos:
            day = po.orderDate.date().isoformat() if hasattr(po.orderDate, 'date') else po.orderDate.isoformat()
            if day not in by_date:
                by_date[day] = PurchasesReportItem(date=day, total_amount=0, order_count=0)
            by_date[day].total_amount += po.totalAmount
            by_date[day].order_count += 1

        items = sorted(by_date.values(), key=lambda x: x.date)
        return PurchasesReport(
            period=Period(
                start=start_date or "all-time",
                end=end_date or date.today().isoformat(),
            ),
            items=items,
            totals={
                "total_amount": sum(i.total_amount for i in items),
                "order_count": sum(i.order_count for i in items),
            },
        )

    async def get_expenses_report(self, start_date, end_date) -> ExpensesReport:
        date_start, date_end = self._parse_date_range(start_date, end_date)
        expenses = await self.repo.find_expenses_in_range(date_start, date_end)

        by_category: dict[str, ExpenseCategoryItem] = {}
        for expense in expenses:
            cat = expense.category
            if cat not in by_category:
                by_category[cat] = ExpenseCategoryItem(category=cat, total_amount=0, count=0)
            by_category[cat].total_amount += expense.amount
            by_category[cat].count += 1

        items = sorted(by_category.values(), key=lambda x: x.total_amount, reverse=True)
        return ExpensesReport(
            period=Period(
                start=start_date or "all-time",
                end=end_date or date.today().isoformat(),
            ),
            items=items,
            totals={"total_amount": sum(i.total_amount for i in items)},
        )

    async def get_inventory_valuation(self) -> InventoryValuationReport:
        products = await self.repo.find_active_products_with_stock()
        items = [
            InventoryValuationItem(
                product_id=p.id, name=p.name, sku=p.sku,
                stock_quantity=p.stockQuantity, cost_price=p.costPrice,
                value=p.stockQuantity * p.costPrice,
            )
            for p in products
        ]
        total_value = sum(i.value for i in items)
        return InventoryValuationReport(
            total_value=total_value,
            product_count=len(items),
            currency="BDT",
            items=items,
        )

    # CSV helpers
    def sales_report_to_csv(self, report: SalesReport) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date", "Total Amount (paisa)", "Transactions", "Cash", "Card", "Mobile", "Credit"])
        for item in report.items:
            pb = item.payment_breakdown
            writer.writerow([item.date, item.total_amount, item.transaction_count,
                             pb.get("cash", 0), pb.get("card", 0), pb.get("mobile", 0), pb.get("credit", 0)])
        return output.getvalue()

    def profit_loss_to_csv(self, report: ProfitLossReport) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Metric", "Amount (paisa)"])
        writer.writerows([
            ["Revenue", report.revenue], ["COGS", report.cogs],
            ["Gross Profit", report.gross_profit], ["Expenses", report.expenses],
            ["Net Profit", report.net_profit],
        ])
        return output.getvalue()

    def top_products_to_csv(self, report: TopProductsReport) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Product ID", "Name", "SKU", "Quantity Sold", "Revenue (paisa)"])
        for item in report.items:
            writer.writerow([item.product_id, item.name, item.sku, item.total_quantity, item.total_revenue])
        return output.getvalue()

    def low_stock_to_csv(self, items: list[LowStockItem]) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Name", "SKU", "Stock", "Min Level"])
        for item in items:
            writer.writerow([item.id, item.name, item.sku, item.stock_quantity, item.min_stock_level])
        return output.getvalue()

    def purchases_to_csv(self, report: PurchasesReport) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Date", "Total Amount (paisa)", "Order Count"])
        for item in report.items:
            writer.writerow([item.date, item.total_amount, item.order_count])
        return output.getvalue()

    def expenses_to_csv(self, report: ExpensesReport) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Category", "Total Amount (paisa)", "Count"])
        for item in report.items:
            writer.writerow([item.category, item.total_amount, item.count])
        return output.getvalue()

    def inventory_valuation_to_csv(self, report: InventoryValuationReport) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Product ID", "Name", "SKU", "Stock Qty", "Cost Price (paisa)", "Value (paisa)"])
        for item in report.items:
            writer.writerow([item.product_id, item.name, item.sku, item.stock_quantity, item.cost_price, item.value])
        return output.getvalue()
```

#### `controller.py`

Seven functions. Each follows this pattern:
```python
from dataclasses import asdict
from fastapi import Query
from fastapi.responses import Response

async def get_sales_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    format: Optional[str] = Query(None),
):
    db = database.get_db()
    repo = ReportsRepository(db)
    service = ReportsService(repo)
    report = await service.get_sales_report(start_date, end_date)
    if format == "csv":
        csv_content = service.sales_report_to_csv(report)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=sales-report.csv"},
        )
    return success_response(asdict(report))
```

`get_low_stock` uses the same pattern but no date params. `get_top_products` adds `limit: int = Query(10)`.

#### `router.py`

```python
router = APIRouter(prefix="/reports", tags=["reports"])

router.add_api_route("/sales", controller.get_sales_report, methods=["GET"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/profit-loss", controller.get_profit_loss, methods=["GET"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/top-products", controller.get_top_products, methods=["GET"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/low-stock", controller.get_low_stock, methods=["GET"],
                     dependencies=[Depends(get_current_user)])
router.add_api_route("/purchases", controller.get_purchases_report, methods=["GET"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/expenses", controller.get_expenses_report, methods=["GET"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/inventory-valuation", controller.get_inventory_valuation, methods=["GET"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
```

---

### Module 2: `backend/src/modules/dashboard/`

#### `schemas.py`

```python
@dataclass
class DashboardSummary:
    today_sales: int
    today_transactions: int
    month_revenue: int
    month_profit: int    # month_revenue - month_expenses
    low_stock_count: int

@dataclass
class TrendItem:
    month: str    # "YYYY-MM"
    revenue: int
    transaction_count: int
```

#### `repository.py`

```python
class DashboardRepository:
    async def find_sales_in_range(self, start: datetime, end: datetime) -> list:
        return await self.prisma.sale.find_many(
            where={"deletedAt": None, "saleDate": {"gte": start, "lte": end}},
        )

    async def find_expenses_in_range(self, start: date, end: date) -> list:
        return await self.prisma.expense.find_many(
            where={"deletedAt": None, "date": {"gte": start, "lte": end}},
        )

    async def count_low_stock_products(self) -> int:
        products = await self.prisma.product.find_many(
            where={"deletedAt": None, "isActive": True},
        )
        return sum(1 for p in products if p.stockQuantity < p.minStockLevel)

    async def find_sales_last_12_months(self, start: datetime) -> list:
        """All sales from 12 months ago to now."""
        return await self.prisma.sale.find_many(
            where={"deletedAt": None, "saleDate": {"gte": start}},
        )
```

#### `service.py`

```python
class DashboardService:
    def __init__(self, repo: DashboardRepository) -> None:
        self.repo = repo

    async def get_summary(self) -> DashboardSummary:
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        today_end = today_start + timedelta(days=1)

        month_start_date = date(now.year, now.month, 1)
        month_end_date = date.today()
        month_start_dt = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

        today_sales = await self.repo.find_sales_in_range(today_start, today_end)
        month_sales = await self.repo.find_sales_in_range(month_start_dt, now)
        month_expenses = await self.repo.find_expenses_in_range(month_start_date, month_end_date)
        low_stock_count = await self.repo.count_low_stock_products()

        today_total = sum(s.totalAmount for s in today_sales)
        month_revenue = sum(s.totalAmount for s in month_sales)
        month_exp_total = sum(e.amount for e in month_expenses)
        month_profit = month_revenue - month_exp_total

        return DashboardSummary(
            today_sales=today_total,
            today_transactions=len(today_sales),
            month_revenue=month_revenue,
            month_profit=month_profit,
            low_stock_count=low_stock_count,
        )

    async def get_trends(self) -> list[TrendItem]:
        now = datetime.now(timezone.utc)
        # Go back 12 months from the start of the current month
        twelve_months_ago = datetime(now.year, now.month, 1, tzinfo=timezone.utc) - timedelta(days=365)

        sales = await self.repo.find_sales_last_12_months(twelve_months_ago)

        monthly: dict[str, dict] = defaultdict(lambda: {"revenue": 0, "transaction_count": 0})
        for sale in sales:
            month_key = sale.saleDate.astimezone(timezone.utc).strftime("%Y-%m")
            monthly[month_key]["revenue"] += sale.totalAmount
            monthly[month_key]["transaction_count"] += 1

        return sorted(
            [TrendItem(month=k, revenue=v["revenue"], transaction_count=v["transaction_count"])
             for k, v in monthly.items()],
            key=lambda x: x.month,
            reverse=True,
        )
```

#### `controller.py` and `router.py`

```python
# controller.py
async def get_summary():
    db = database.get_db()
    repo = DashboardRepository(db)
    service = DashboardService(repo)
    summary = await service.get_summary()
    return success_response(asdict(summary))

async def get_trends():
    db = database.get_db()
    repo = DashboardRepository(db)
    service = DashboardService(repo)
    trends = await service.get_trends()
    return success_response([asdict(t) for t in trends])

# router.py
router = APIRouter(prefix="/dashboard", tags=["dashboard"])
router.add_api_route("/summary", controller.get_summary, methods=["GET"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/trends", controller.get_trends, methods=["GET"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
```

---

### Register in `backend/src/main.py`

```python
from src.modules.reports.router import router as reports_router
from src.modules.dashboard.router import router as dashboard_router
# ...
app.include_router(reports_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
```

---

### Tests

**`backend/tests/unit/modules/reports/test_service.py`**

```
TestGetSalesReport:
  test_returns_sales_grouped_by_date
  test_payment_breakdown_correct
  test_totals_correct

TestGetProfitLoss:
  test_revenue_is_sum_of_sale_totals
  test_cogs_uses_product_cost_price
  test_net_profit_equals_gross_minus_expenses

TestGetTopProducts:
  test_returns_sorted_by_quantity_descending
  test_limited_to_limit_param
  test_aggregates_multiple_sales_correctly

TestGetLowStock:
  test_returns_only_products_below_min_level
  test_returns_empty_when_all_stocked

TestGetPurchasesReport:
  test_groups_by_order_date
  test_excludes_cancelled_pos (repo already excludes them — just verify totals)

TestGetExpensesReport:
  test_groups_by_category
  test_sorted_by_total_amount_descending

TestGetInventoryValuation:
  test_value_is_stock_times_cost_price
  test_total_value_is_sum_of_item_values
```

**`backend/tests/unit/modules/dashboard/test_service.py`**

```
TestGetSummary:
  test_today_sales_and_count_correct
  test_month_profit_is_revenue_minus_expenses
  test_low_stock_count_from_repo

TestGetTrends:
  test_returns_items_sorted_descending_by_month
  test_groups_correctly_by_month
```

**`backend/tests/integration/test_reports_api.py`**

```
TestGetSalesReport: test_admin_200, test_staff_403, test_csv_format_response
TestGetProfitLoss: test_admin_200, test_staff_403
TestGetTopProducts: test_admin_200, test_staff_403
TestGetLowStock: test_all_roles_get_200, test_unauthenticated_401
TestGetPurchasesReport: test_admin_200, test_staff_403
TestGetExpensesReport: test_admin_200, test_staff_403
TestGetInventoryValuation: test_admin_200, test_staff_403
```

**`backend/tests/integration/test_dashboard_api.py`**

```
TestGetSummary: test_admin_200, test_staff_403, test_unauthenticated_401
TestGetTrends: test_admin_200, test_staff_403
```

## Acceptance Criteria

- [ ] `ruff check backend/` exits 0
- [ ] `pytest backend/` exits 0
- [ ] `GET /api/reports/sales` returns daily breakdown, admin+manager only
- [ ] `GET /api/reports/profit-loss` computes revenue - COGS - expenses correctly
- [ ] `GET /api/reports/top-products` returns sorted by quantity, `limit` param respected
- [ ] `GET /api/reports/low-stock` accessible by all authenticated roles
- [ ] `GET /api/reports/purchases` excludes cancelled POs
- [ ] `GET /api/reports/expenses` groups by category, sorted by total descending
- [ ] `GET /api/reports/inventory-valuation` value = stock_quantity × cost_price per item
- [ ] All report endpoints support `format=csv` → returns text/csv Content-Type
- [ ] `GET /api/dashboard/summary` returns today + month stats
- [ ] `GET /api/dashboard/trends` returns 12-month list sorted descending
- [ ] CONTEXT.md updated in all touched directories

## Files to Create

**Reports module (new):**
- `backend/src/modules/reports/__init__.py`
- `backend/src/modules/reports/schemas.py`
- `backend/src/modules/reports/repository.py`
- `backend/src/modules/reports/service.py`
- `backend/src/modules/reports/controller.py`
- `backend/src/modules/reports/router.py`
- `backend/src/modules/reports/CONTEXT.md`

**Dashboard module (new):**
- `backend/src/modules/dashboard/__init__.py`
- `backend/src/modules/dashboard/schemas.py`
- `backend/src/modules/dashboard/repository.py`
- `backend/src/modules/dashboard/service.py`
- `backend/src/modules/dashboard/controller.py`
- `backend/src/modules/dashboard/router.py`
- `backend/src/modules/dashboard/CONTEXT.md`

**Tests (new):**
- `backend/tests/unit/modules/reports/__init__.py`
- `backend/tests/unit/modules/reports/test_service.py`
- `backend/tests/unit/modules/dashboard/__init__.py`
- `backend/tests/unit/modules/dashboard/test_service.py`
- `backend/tests/integration/test_reports_api.py`
- `backend/tests/integration/test_dashboard_api.py`

**Modified:**
- `backend/src/main.py`
- `backend/src/modules/CONTEXT.md`

## Known Pitfalls

1. **`po.orderDate` and `expense.date` from `@db.Date`** — Prisma returns these as `datetime` objects in Python, not `date`. When comparing or extracting date string: `po.orderDate.date().isoformat()` or `po.orderDate.strftime("%Y-%m-%d")`. The filter `where={"orderDate": {"gte": start, "lte": end}}` with `date` objects works in Prisma.

2. **`format` parameter name** — Python has a built-in `format`. Use `format: Optional[str] = Query(None)` in the function signature. Avoid shadowing the built-in by not calling it at module level.

3. **`asdict()` on dataclasses** — `from dataclasses import asdict`. Works recursively on nested dataclasses. The `Period`, `SalesReportItem`, etc. can be nested inside `SalesReport` and `asdict()` handles it.

4. **`item.product` in top products / P&L** — requires `include={"saleItems": {"include": {"product": True}}}` in the Prisma query. Use `find_sales_with_items_in_range()` (not `find_sales_in_range()`) for these reports.

5. **Empty period in report** — When no sales exist in the range, return an empty `items: []` and `totals: {total_amount: 0, transaction_count: 0}`. Don't raise errors.

6. **Dashboard `month_profit`** — Defined simply as `month_revenue - month_expenses` (no COGS calculation). COGS requires loading all sale items for the month, which is expensive. Simple profit estimate is sufficient for dashboard.

7. **Trends: last 12 months** — Use `timedelta(days=365)` approximation OR compute exact month start 12 months ago: `datetime(year-1, month, 1)` handling year rollover. Either is acceptable.

8. **CSV `format` query clash** — Avoid using `format` as a Python variable name inside the controller function since it shadows a built-in. Consider `report_format: Optional[str] = Query(None, alias="format")` OR just use it as `format` at function parameter level (safe there since it's just a local variable).

9. **Cancelled POs in purchases report** — The repo already excludes them with `"status": {"not": "cancelled"}`. Just make sure the test verifies this exclusion.

## Exit Signal

```bash
ruff check backend/
pytest backend/ -q
# Must exit 0. Report total passing test count.
```
