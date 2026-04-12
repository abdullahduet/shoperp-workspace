"""Promotions service — ALL business logic for promotion management."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.promotions.repository import PromotionRepository
from src.modules.promotions.schemas import (
    PromotionCreate,
    PromotionResponse,
    PromotionUpdate,
)


@dataclass
class PaginatedPromotions:
    items: list[PromotionResponse]
    total: int


class PromotionService:
    def __init__(self, repo: PromotionRepository) -> None:
        self.repo = repo

    async def list(
        self,
        page: int,
        limit: int,
        is_active: bool | None,
        type: str | None,
    ) -> PaginatedPromotions:
        """Return a paginated list of promotions with optional filters."""
        where: dict = {"deletedAt": None}
        if is_active is not None:
            where["isActive"] = is_active
        if type is not None:
            where["type"] = type
        skip = (page - 1) * limit
        items, total = await self.repo.find_paginated(skip, limit, where)
        return PaginatedPromotions(
            items=[PromotionResponse.model_validate(p) for p in items],
            total=total,
        )

    async def get_active(self) -> list[PromotionResponse]:
        """Return all currently active promotions."""
        now = datetime.now(timezone.utc)
        promotions = await self.repo.find_active(now)
        return [PromotionResponse.model_validate(p) for p in promotions]

    async def get_by_id(self, promotion_id: str) -> PromotionResponse:
        """Return a single promotion or raise NotFoundError."""
        promotion = await self.repo.find_by_id(promotion_id)
        if promotion is None:
            raise NotFoundError("Promotion", promotion_id)
        return PromotionResponse.model_validate(promotion)

    async def create(self, input: PromotionCreate) -> PromotionResponse:
        """Create a new promotion with optional product associations.

        Validates:
        - end_date must be after start_date
        - applies_to='specific' requires non-empty product_ids
        """
        start_dt = datetime.fromisoformat(input.start_date)
        end_dt = datetime.fromisoformat(input.end_date)

        if end_dt <= start_dt:
            raise ValidationError("end_date must be after start_date")

        if input.applies_to == "specific" and not input.product_ids:
            raise ValidationError(
                "product_ids must not be empty when applies_to is 'specific'"
            )

        promo_data: dict = {
            "name": input.name,
            "type": input.type,
            "value": input.value,
            "startDate": start_dt,
            "endDate": end_dt,
            "minPurchaseAmount": input.min_purchase_amount,
            "appliesTo": input.applies_to,
            "isActive": input.is_active,
        }

        promotion = await self.repo.create_with_products(promo_data, input.product_ids)
        return PromotionResponse.model_validate(promotion)

    async def update(self, promotion_id: str, input: PromotionUpdate) -> PromotionResponse:
        """Update a promotion. Only provided fields are updated."""
        existing = await self.repo.find_by_id(promotion_id)
        if existing is None:
            raise NotFoundError("Promotion", promotion_id)

        promo_data: dict = {}
        if input.name is not None:
            promo_data["name"] = input.name
        if input.type is not None:
            promo_data["type"] = input.type
        if input.value is not None:
            promo_data["value"] = input.value
        if input.start_date is not None:
            promo_data["startDate"] = datetime.fromisoformat(input.start_date)
        if input.end_date is not None:
            promo_data["endDate"] = datetime.fromisoformat(input.end_date)
        if input.min_purchase_amount is not None:
            promo_data["minPurchaseAmount"] = input.min_purchase_amount
        if input.applies_to is not None:
            promo_data["appliesTo"] = input.applies_to
        if input.is_active is not None:
            promo_data["isActive"] = input.is_active

        promotion = await self.repo.update_with_products(
            promotion_id, promo_data, input.product_ids
        )
        return PromotionResponse.model_validate(promotion)

    async def delete(self, promotion_id: str) -> None:
        """Soft-delete a promotion."""
        promotion = await self.repo.find_by_id(promotion_id)
        if promotion is None:
            raise NotFoundError("Promotion", promotion_id)
        await self.repo.soft_delete(promotion_id)

    async def get_best_discount(
        self,
        subtotal: int,
        items: list[dict],
    ) -> tuple[str | None, int]:
        """Find the best active promotion. Returns (promotion_id, discount_amount).

        Returns (None, 0) if no promotion applies or gives discount > 0.
        Items must be: [{"product_id": str, "quantity": int, "unit_price": int}]
        """
        now = datetime.now(timezone.utc)
        promotions = await self.repo.find_active(now)
        best_id: str | None = None
        best_discount = 0
        for promo in promotions:
            discount = self.calculate_discount(promo, subtotal, items)
            if discount > best_discount:
                best_discount = discount
                best_id = promo.id
        return best_id, best_discount

    def calculate_discount(
        self,
        promotion,
        subtotal: int,
        items: list[dict],
    ) -> int:
        """Calculate discount amount in paisa.

        Args:
            promotion: Prisma Promotion object with promotionProducts loaded.
            subtotal: Total order value in paisa.
            items: List of dicts with keys: product_id, quantity, unit_price (paisa).

        Returns:
            Discount amount in paisa (0 if min_purchase_amount not met).
        """
        if subtotal < promotion.minPurchaseAmount:
            return 0

        if promotion.type == "percentage":
            return int(subtotal * promotion.value / 100)

        if promotion.type == "fixed":
            return min(promotion.value, subtotal)

        # bogo
        if promotion.appliesTo == "all":
            qualifying = items
        else:
            qualifying_ids = {pp.productId for pp in promotion.promotionProducts}
            qualifying = [i for i in items if i["product_id"] in qualifying_ids]

        discount = 0
        for item in qualifying:
            free_count = item["quantity"] // 2
            discount += free_count * item["unit_price"]
        return discount
