from collections import defaultdict
from datetime import datetime, date, timezone, timedelta

from src.modules.dashboard.repository import DashboardRepository
from src.modules.dashboard.schemas import DashboardSummary, TrendItem


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
