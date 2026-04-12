# Promotions — Context

## Purpose
Manages promotional discounts for the ShopERP retail system. Supports three discount types: percentage-based, fixed-amount, and buy-one-get-one-free (BOGO). Promotions can apply to all products or to a specific set of products.

## Key Files
- `schemas.py` → Pydantic models: PromotionCreate, PromotionUpdate, PromotionResponse
- `repository.py` → DB queries via Prisma: find_paginated, find_active, find_by_id, create_with_products, update_with_products, soft_delete
- `service.py` → Business logic: list, get_active, get_by_id, create, update, delete, calculate_discount, get_best_discount
- `controller.py` → HTTP layer: parse request, call service, return JSON response
- `router.py` → FastAPI APIRouter with /promotions prefix; /active registered BEFORE /{promotion_id}

## Patterns
- Prisma model: `prisma.promotion`, `prisma.promotionproduct` (lowercase, no underscores)
- Camelcase attributes from Prisma: `startDate`, `endDate`, `minPurchaseAmount`, `appliesTo`, `isActive`, `promotionProducts`
- DateTime fields parsed with `datetime.fromisoformat()` before passing to Prisma
- Transaction pattern: `async with self.prisma.tx() as tx:` followed by fresh `find_first` with includes
- After transaction, always do fresh `find_first` to load includes (promotionProducts)
- BOGO discount: `qty // 2` integer division for free item count

## Last Updated
2026-04-11 — added get_best_discount() for sales integration (task/0012)
