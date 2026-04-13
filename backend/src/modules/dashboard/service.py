"""Dashboard service — business logic for summary and trend endpoints."""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, date, timezone, timedelta

from src.core.exceptions import AppError
from src.modules.dashboard.repository import DashboardRepository
from src.modules.dashboard.schemas import DashboardSummary, TrendItem

logger = logging.getLogger(__name__)


def _twelve_months_ago(now: datetime) -> datetime:
    """Return the first day of the month exactly 12 months before *now*, UTC.

    Uses calendar arithmetic instead of timedelta(days=365) to avoid
    landing in the wrong month on leap years.
    """
    year = now.year - 1 if now.month > 1 else now.year - 1
    month = now.month - 1 if now.month > 1 else 12
    # Recalculate: subtract 12 months properly
    target_month = now.month - 12
    target_year = now.year
    if target_month <= 0:
        target_month += 12
        target_year -= 1
    return datetime(target_year, target_month, 1, tzinfo=timezone.utc)


class DashboardService:
    def __init__(self, repo: DashboardRepository) -> None:
        self.repo = repo

    async def get_summary(self) -> DashboardSummary:
        """Return today's sales, month revenue/profit, and low-stock count.

        Returns zeroed DashboardSummary on any repository error so the
        dashboard page always renders rather than showing a 500.
        """
        now = datetime.now(timezone.utc)
        today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        today_end = today_start + timedelta(days=1)
        month_start_dt = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

        # Expense.date is @db.Date — Prisma requires datetime objects, not date.
        month_start_for_expenses = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        month_end_for_expenses = datetime(
            now.year, now.month, now.day, 23, 59, 59, tzinfo=timezone.utc
        )

        try:
            today_sales = await self.repo.find_sales_in_range(today_start, today_end)
            month_sales = await self.repo.find_sales_in_range(month_start_dt, now)
            month_expenses = await self.repo.find_expenses_in_range(
                month_start_for_expenses, month_end_for_expenses
            )
            low_stock_count = await self.repo.count_low_stock_products()
        except AppError:
            raise
        except Exception as exc:
            logger.exception("Dashboard summary query failed: %s", exc)
            return DashboardSummary(
                today_sales=0,
                today_transactions=0,
                month_revenue=0,
                month_profit=0,
                low_stock_count=0,
            )

        today_total = sum(s.totalAmount for s in today_sales)
        month_revenue = sum(s.totalAmount for s in month_sales)
        month_exp_total = sum(e.amount for e in month_expenses)

        return DashboardSummary(
            today_sales=today_total,
            today_transactions=len(today_sales),
            month_revenue=month_revenue,
            month_profit=month_revenue - month_exp_total,
            low_stock_count=low_stock_count,
        )

    async def get_trends(self) -> list[TrendItem]:
        """Return monthly revenue totals for the last 12 calendar months."""
        now = datetime.now(timezone.utc)
        twelve_months_ago = _twelve_months_ago(now)

        try:
            sales = await self.repo.find_sales_last_12_months(twelve_months_ago)
        except AppError:
            raise
        except Exception as exc:
            logger.exception("Dashboard trends query failed: %s", exc)
            return []

        monthly: dict[str, dict] = defaultdict(lambda: {"revenue": 0, "transaction_count": 0})
        for sale in sales:
            month_key = sale.saleDate.astimezone(timezone.utc).strftime("%Y-%m")
            monthly[month_key]["revenue"] += sale.totalAmount
            monthly[month_key]["transaction_count"] += 1

        return sorted(
            [
                TrendItem(month=k, revenue=v["revenue"], transaction_count=v["transaction_count"])
                for k, v in monthly.items()
            ],
            key=lambda x: x.month,
            reverse=True,
        )
