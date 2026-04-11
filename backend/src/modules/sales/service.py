"""Sales service — ALL business logic for sale recording and retrieval."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.promotions.service import PromotionService
from src.modules.sales.repository import SalesRepository
from src.modules.sales.schemas import (
    DailySummaryResponse,
    SaleCreate,
    SaleResponse,
)


@dataclass
class PaginatedSales:
    items: list[SaleResponse]
    total: int


class SalesService:
    def __init__(self, repo: SalesRepository, promotion_service: PromotionService) -> None:
        self.repo = repo
        self.promotion_service = promotion_service

    async def list(
        self,
        page: int,
        limit: int,
        start_date: str | None,
        end_date: str | None,
        payment_method: str | None,
    ) -> PaginatedSales:
        """Return a paginated list of sales with optional filters."""
        where: dict = {"deletedAt": None}
        if start_date is not None:
            start_dt = datetime.fromisoformat(start_date).replace(tzinfo=timezone.utc)
            where.setdefault("saleDate", {})["gte"] = start_dt
        if end_date is not None:
            end_dt = datetime.fromisoformat(end_date).replace(tzinfo=timezone.utc)
            where.setdefault("saleDate", {})["lte"] = end_dt
        if payment_method is not None:
            where["paymentMethod"] = payment_method
        skip = (page - 1) * limit
        items, total = await self.repo.find_paginated(skip, limit, where)
        return PaginatedSales(
            items=[SaleResponse.model_validate(s) for s in items],
            total=total,
        )

    async def get_by_id(self, sale_id: str) -> SaleResponse:
        """Return a single sale with items or raise NotFoundError."""
        sale = await self.repo.find_by_id(sale_id)
        if sale is None:
            raise NotFoundError("Sale", sale_id)
        return SaleResponse.model_validate(sale)

    async def get_daily_summary(self) -> DailySummaryResponse:
        """Compute today's sales totals and payment breakdown."""
        today = date.today()
        today_start = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
        today_end = today_start + timedelta(days=1)
        sales = await self.repo.find_today_sales(today_start, today_end)
        total_sales = sum(s.totalAmount for s in sales)
        transaction_count = len(sales)
        payment_breakdown: dict[str, int] = {"cash": 0, "card": 0, "mobile": 0, "credit": 0}
        for s in sales:
            method = s.paymentMethod if s.paymentMethod in payment_breakdown else "cash"
            payment_breakdown[method] += s.totalAmount
        return DailySummaryResponse(
            date=today.isoformat(),
            total_sales=total_sales,
            transaction_count=transaction_count,
            payment_breakdown=payment_breakdown,
        )

    async def record_sale(self, input: SaleCreate, recorded_by: str) -> SaleResponse:
        """Validate items, compute totals, apply best promotion, record atomically."""
        # Step 1: Validate each product and load for tax computation
        products = []
        for item in input.items:
            product = await self.repo.find_product_by_id(item.product_id)
            if product is None or product.deletedAt is not None:
                raise ValidationError(f"Product not found: {item.product_id}")
            if not product.isActive:
                raise ValidationError(f"Product is inactive: {item.product_id}")
            if product.stockQuantity < item.quantity:
                raise ValidationError(
                    f"Insufficient stock for product {item.product_id}: "
                    f"available {product.stockQuantity}, requested {item.quantity}"
                )
            products.append(product)

        # Step 2: Compute subtotal
        subtotal = sum(item.quantity * item.unit_price for item in input.items)

        # Step 3: Build items for discount calculation
        items_for_discount = [
            {
                "product_id": i.product_id,
                "quantity": i.quantity,
                "unit_price": i.unit_price,
            }
            for i in input.items
        ]

        # Step 4: Get best promotion discount
        promotion_id, discount_amount = await self.promotion_service.get_best_discount(
            subtotal, items_for_discount
        )

        # Step 5: Compute tax from each product's taxRate (Decimal → float)
        tax_amount = sum(
            int(item.quantity * item.unit_price * float(product.taxRate) / 100)
            for item, product in zip(input.items, products)
        )

        # Step 6: Total
        total_amount = subtotal - discount_amount + tax_amount

        # Step 7: Generate sale number
        sale_number = await self._generate_sale_number()

        # Step 8: Generate journal entry number
        entry_number = await self._generate_entry_number()

        # Step 9: Look up accounts
        cash_account = await self.repo.find_account_by_code("1000")
        revenue_account = await self.repo.find_account_by_code("4000")
        if cash_account is None or revenue_account is None:
            raise ValidationError("Chart of accounts not seeded")

        # Step 10: Build data structures
        sale_data: dict = {
            "saleNumber": sale_number,
            "subtotal": subtotal,
            "discountAmount": discount_amount,
            "taxAmount": tax_amount,
            "totalAmount": total_amount,
            "paymentMethod": input.payment_method,
            "recordedBy": recorded_by,
        }
        if input.customer_name:
            sale_data["customerName"] = input.customer_name
        if promotion_id:
            sale_data["promotionId"] = promotion_id
        if input.notes:
            sale_data["notes"] = input.notes

        items_data = [
            {
                "productId": item.product_id,
                "quantity": item.quantity,
                "unitPrice": item.unit_price,
                "discount": 0,
                "totalPrice": item.quantity * item.unit_price,
            }
            for item in input.items
        ]

        stock_updates = []
        for item, product in zip(input.items, products):
            stock_before = product.stockQuantity
            stock_after = stock_before - item.quantity
            stock_updates.append(
                {
                    "product_id": item.product_id,
                    "qty": item.quantity,
                    "stock_before": stock_before,
                    "stock_after": stock_after,
                    "performed_by": recorded_by,
                }
            )

        journal_data = {
            "entry_number": entry_number,
            "description": f"Sale recorded: {sale_number}",
            "created_by": recorded_by,
            "debit_account_id": cash_account.id,
            "credit_account_id": revenue_account.id,
            "amount": total_amount,
        }

        # Step 11: Atomic transaction
        sale = await self.repo.create_sale_atomic(sale_data, items_data, stock_updates, journal_data)

        # Step 12: Return response
        return SaleResponse.model_validate(sale)

    async def _generate_sale_number(self) -> str:
        """Generate a sequential sale number for today: SALE-YYYYMMDD-NNN."""
        today_str = date.today().strftime("%Y%m%d")
        count = await self.repo.count_today_sales(today_str)
        return f"SALE-{today_str}-{count + 1:03d}"

    async def _generate_entry_number(self) -> str:
        """Generate a sequential journal entry number for today: JE-YYYYMMDD-NNN."""
        today_str = date.today().strftime("%Y%m%d")
        count = await self.repo.count_today_journal_entries(today_str)
        return f"JE-{today_str}-{count + 1:03d}"
