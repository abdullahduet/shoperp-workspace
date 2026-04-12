from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from src.core.exceptions import AppError
from src.core.responses import error_response
from src import database
from src.modules.health.router import router as health_router
from src.modules.auth.router import router as auth_router
from src.modules.categories.router import router as categories_router
from src.modules.products.router import router as products_router
from src.modules.inventory.router import router as inventory_router
from src.modules.suppliers.router import router as suppliers_router
from src.modules.purchase_orders.router import router as purchase_orders_router
from src.modules.promotions.router import router as promotions_router
from src.modules.sales.router import router as sales_router
from src.modules.accounting.router import router as accounting_router
from src.modules.expenses.router import router as expenses_router
from src.modules.reports.router import router as reports_router
from src.modules.dashboard.router import router as dashboard_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await database.connect()
    yield
    await database.disconnect()


app = FastAPI(
    title="ShopERP API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware must be registered before routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    details = getattr(exc, "details", None)
    return error_response(
        error=exc.message,
        code=exc.code,
        status_code=exc.status_code,
        details=details,
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    details = [
        {"field": ".".join(str(loc) for loc in err["loc"]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return error_response(
        error="Request validation failed",
        code="VALIDATION_ERROR",
        status_code=422,
        details=details,
    )


app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(categories_router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(inventory_router, prefix="/api")
app.include_router(suppliers_router, prefix="/api")
app.include_router(purchase_orders_router, prefix="/api")
app.include_router(promotions_router, prefix="/api")
app.include_router(sales_router, prefix="/api")
app.include_router(accounting_router, prefix="/api")
app.include_router(expenses_router, prefix="/api")
app.include_router(reports_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
