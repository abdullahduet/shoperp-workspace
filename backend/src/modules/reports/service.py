import csv
import io
from datetime import datetime, date, timezone

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

    def _parse_date_range(self, start_date, end_date) -> tuple[datetime, datetime]:
        """Return a [start, end] datetime range for @db.Date columns.

        Prisma Client Python requires datetime objects (not bare date objects)
        for @db.Date column filters. Both datetimes are UTC midnight-bounded.
        """
        if start_date:
            s = datetime.combine(
                date.fromisoformat(start_date), datetime.min.time()
            ).replace(tzinfo=timezone.utc)
        else:
            s = datetime(2000, 1, 1, tzinfo=timezone.utc)
        if end_date:
            e = datetime.combine(
                date.fromisoformat(end_date), datetime.max.time()
            ).replace(tzinfo=timezone.utc)
        else:
            e = datetime.now(timezone.utc)
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
