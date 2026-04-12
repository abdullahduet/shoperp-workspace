"""Reports controller — parse params, call service, format response."""
from __future__ import annotations

from dataclasses import asdict
from typing import Optional

from fastapi import Depends, Query
from fastapi.responses import Response

from src.core.responses import success_response
from src.database import get_db
from src.modules.reports.repository import ReportsRepository
from src.modules.reports.service import ReportsService


def _get_service(db=Depends(get_db)) -> ReportsService:
    repo = ReportsRepository(db)
    return ReportsService(repo)


async def get_sales_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    fmt: Optional[str] = Query(None, alias="format"),
    service: ReportsService = Depends(_get_service),
):
    report = await service.get_sales_report(start_date, end_date)
    if fmt == "csv":
        csv_content = service.sales_report_to_csv(report)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=sales-report.csv"},
        )
    return success_response(asdict(report))


async def get_profit_loss(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    fmt: Optional[str] = Query(None, alias="format"),
    service: ReportsService = Depends(_get_service),
):
    report = await service.get_profit_loss(start_date, end_date)
    if fmt == "csv":
        csv_content = service.profit_loss_to_csv(report)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=profit-loss.csv"},
        )
    return success_response(asdict(report))


async def get_top_products(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(10),
    fmt: Optional[str] = Query(None, alias="format"),
    service: ReportsService = Depends(_get_service),
):
    report = await service.get_top_products(start_date, end_date, limit)
    if fmt == "csv":
        csv_content = service.top_products_to_csv(report)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=top-products.csv"},
        )
    return success_response(asdict(report))


async def get_low_stock(
    fmt: Optional[str] = Query(None, alias="format"),
    service: ReportsService = Depends(_get_service),
):
    items = await service.get_low_stock()
    if fmt == "csv":
        csv_content = service.low_stock_to_csv(items)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=low-stock.csv"},
        )
    return success_response([asdict(i) for i in items])


async def get_purchases_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    fmt: Optional[str] = Query(None, alias="format"),
    service: ReportsService = Depends(_get_service),
):
    report = await service.get_purchases_report(start_date, end_date)
    if fmt == "csv":
        csv_content = service.purchases_to_csv(report)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=purchases-report.csv"},
        )
    return success_response(asdict(report))


async def get_expenses_report(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    fmt: Optional[str] = Query(None, alias="format"),
    service: ReportsService = Depends(_get_service),
):
    report = await service.get_expenses_report(start_date, end_date)
    if fmt == "csv":
        csv_content = service.expenses_to_csv(report)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=expenses-report.csv"},
        )
    return success_response(asdict(report))


async def get_inventory_valuation(
    fmt: Optional[str] = Query(None, alias="format"),
    service: ReportsService = Depends(_get_service),
):
    report = await service.get_inventory_valuation()
    if fmt == "csv":
        csv_content = service.inventory_valuation_to_csv(report)
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=inventory-valuation.csv"},
        )
    return success_response(asdict(report))
