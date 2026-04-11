from __future__ import annotations

import math
from typing import Any

from fastapi.responses import JSONResponse


def success_response(
    data: Any,
    message: str = "OK",
    status_code: int = 200,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"success": True, "data": data, "message": message},
    )


def paginated_response(
    data: list,
    page: int,
    limit: int,
    total: int,
) -> JSONResponse:
    total_pages = math.ceil(total / limit) if limit > 0 else 0
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "data": data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages,
            },
        },
    )


def error_response(
    error: str,
    code: str,
    status_code: int,
    details: list | None = None,
) -> JSONResponse:
    body: dict[str, Any] = {"success": False, "error": error, "code": code}
    if details:
        body["details"] = details
    return JSONResponse(status_code=status_code, content=body)
