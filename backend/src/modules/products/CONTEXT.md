# products — Context

## Purpose
Manages products in the ERP system. Supports paginated listing with filters, low-stock reporting, CRUD operations, and CSV bulk import. Products are soft-deleted and prices are stored as integers in paisa.

## Key Files
- schemas.py → ProductCreate, ProductUpdate, ProductResponse, ImportResult Pydantic models
- repository.py → DB queries: find_paginated, find_low_stock, find_by_id, find_by_sku, find_by_barcode, create, update, soft_delete
- service.py → Business logic: list_products, get_low_stock, get_by_id, create, update, delete, import_from_csv
- controller.py → FastAPI handler functions; uses Query params for list filters; UploadFile for CSV import
- router.py → APIRouter prefix=/products; /low-stock and /import registered BEFORE /{product_id}

## Patterns
- Prices stored as integers (paisa). taxRate stored as Decimal in DB; converted to float in ProductResponse.model_validate.
- Prisma model attributes use camelCase (categoryId, unitPrice, stockQuantity, isActive, deletedAt, createdAt).
- Low-stock filtering is done in Python (Prisma cannot compare two columns in where clause).
- Soft delete: set deletedAt=datetime.now(timezone.utc) via prisma.product.update.
- list_products builds where dict conditionally — never passes None values into where.

## Last Updated
2026-04-11 — initial implementation (task/0004)
