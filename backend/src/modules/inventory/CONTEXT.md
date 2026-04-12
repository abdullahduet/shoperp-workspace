# Inventory — Context

## Purpose
Manages stock movement history and inventory valuation for the ShopERP system. Provides endpoints to list stock movements with filtering, create manual stock adjustments (atomically updating product stock), and compute total inventory value.

## Key Files
- `schemas.py` → Pydantic models: AdjustmentRequest (input), StockMovementResponse, ValuationResponse
- `repository.py` → DB queries: paginated movements, product lookup, transactional adjustment creation, valuation computation
- `service.py` → Business logic: pagination+filtering, adjustment validation (no negative stock, inactive products), valuation aggregation
- `controller.py` → Thin HTTP layer: parse query params, call service, format response
- `router.py` → Route wiring: GET /movements (any auth), POST /adjust (admin/manager), GET /valuation (admin/manager)

## Patterns
- All Prisma model access uses camelCase attributes: `obj.productId`, `obj.movementType`, `obj.stockBefore`, `obj.stockAfter`
- Prisma model for `stock_movements` table is accessed as `self.prisma.stockmovement` (no underscore)
- Stock adjustments use `self.prisma.tx()` async context manager for atomicity
- `StockMovementResponse.model_validate()` overrides Pydantic to map camelCase Prisma attrs to snake_case fields
- Money (costPrice, unitPrice) stored as integers in paisa — no floats
- Valuation = sum(stockQuantity × costPrice) for all active non-deleted products with stock > 0

## Last Updated
2026-04-11 — initial implementation: movements list, adjust, valuation endpoints
