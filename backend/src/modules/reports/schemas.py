from __future__ import annotations
from dataclasses import dataclass


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
