"""Inventory service — ALL business logic for stock management."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.inventory.repository import InventoryRepository
from src.modules.inventory.schemas import StockMovementResponse, ValuationResponse


@dataclass
class PaginatedMovements:
    items: list[StockMovementResponse]
    total: int


class InventoryService:
    def __init__(self, repo: InventoryRepository) -> None:
        self.repo = repo

    async def list_movements(
        self,
        page: int,
        limit: int,
        product_id: Optional[str],
        movement_type: Optional[str],
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> PaginatedMovements:
        """Return paginated stock movement history with optional filters."""
        where: dict = {}

        if product_id:
            where["productId"] = product_id
        if movement_type:
            where["movementType"] = movement_type

        # Date filters — createdAt range
        date_filter: dict = {}
        if start_date:
            dt_start = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            date_filter["gte"] = dt_start
        if end_date:
            dt_end = (
                datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                + timedelta(days=1)
            )
            date_filter["lt"] = dt_end
        if date_filter:
            where["createdAt"] = date_filter

        skip = (page - 1) * limit
        items, total = await self.repo.find_movements(skip=skip, take=limit, where=where)
        return PaginatedMovements(
            items=[StockMovementResponse.model_validate(m) for m in items],
            total=total,
        )

    async def adjust(
        self,
        product_id: str,
        quantity: int,
        notes: Optional[str],
        performed_by: str,
    ) -> StockMovementResponse:
        """Create a manual stock adjustment. Updates product stock atomically."""
        product = await self.repo.find_product_by_id(product_id)
        if product is None:
            raise NotFoundError("Product", product_id)
        if not product.isActive or product.deletedAt is not None:
            raise ValidationError("Cannot adjust stock for an inactive or deleted product")

        stock_before = product.stockQuantity
        stock_after = stock_before + quantity
        if stock_after < 0:
            raise ValidationError(
                f"Adjustment would result in negative stock ({stock_after}). "
                f"Current stock is {stock_before}."
            )

        movement = await self.repo.create_adjustment(
            product_id=product_id,
            quantity=quantity,
            stock_before=stock_before,
            stock_after=stock_after,
            notes=notes,
            performed_by=performed_by,
        )
        return StockMovementResponse.model_validate(movement)

    async def get_valuation(self) -> ValuationResponse:
        """Return total inventory value (stock_quantity × cost_price for all active products)."""
        products = await self.repo.get_active_products_for_valuation()
        total_value = sum(p.stockQuantity * p.costPrice for p in products)
        product_count = len(products)
        return ValuationResponse(total_value=total_value, product_count=product_count, currency="BDT")
