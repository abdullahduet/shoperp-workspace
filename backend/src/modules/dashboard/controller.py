"""Dashboard controller — call service, format response."""
from __future__ import annotations

from dataclasses import asdict

from fastapi import Depends

from src.core.responses import success_response
from src.database import get_db
from src.modules.dashboard.repository import DashboardRepository
from src.modules.dashboard.service import DashboardService


def _get_service(db=Depends(get_db)) -> DashboardService:
    repo = DashboardRepository(db)
    return DashboardService(repo)


async def get_summary(service: DashboardService = Depends(_get_service)):
    summary = await service.get_summary()
    return success_response(asdict(summary))


async def get_trends(service: DashboardService = Depends(_get_service)):
    trends = await service.get_trends()
    return success_response([asdict(t) for t in trends])
