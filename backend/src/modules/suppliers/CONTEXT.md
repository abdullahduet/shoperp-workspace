# suppliers — Context

## Purpose
Manages supplier master data: contact info, payment terms, active status. Soft-deletes only. No hard deletes. Pagination on list, optional name/is_active filters.

## Key Files
- schemas.py → SupplierCreate, SupplierUpdate, SupplierResponse (camelCase mapping in model_validate)
- repository.py → DB queries: find_paginated, find_by_id, create, update, soft_delete
- service.py → Business logic: list, get_by_id, create, update, delete
- controller.py → FastAPI handler functions; also proxies supplier purchases via PurchaseOrderService
- router.py → APIRouter with prefix=/suppliers; action routes before bare /{id}

## Patterns
- model_validate overrides camelCase → snake_case mapping for Prisma objects
- Soft delete via `deletedAt` timestamp
- All list queries include `{"deletedAt": None}` in where clause

## Last Updated
2026-04-11 — initial implementation (task/0008)
