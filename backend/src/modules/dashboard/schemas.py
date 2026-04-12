from __future__ import annotations
from dataclasses import dataclass


@dataclass
class DashboardSummary:
    today_sales: int
    today_transactions: int
    month_revenue: int
    month_profit: int
    low_stock_count: int


@dataclass
class TrendItem:
    month: str
    revenue: int
    transaction_count: int
