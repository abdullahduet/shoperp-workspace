# categories — Context

## Purpose
Manages product categories with optional parent-child hierarchy. Supports flat list and tree views. Categories are soft-deleted and can only be removed if they have no active products.

## Key Files
- schemas.py → CategoryCreate, CategoryUpdate, CategoryResponse, CategoryTreeNode Pydantic models
- repository.py → DB queries: find_all, find_by_id, create, update, soft_delete, has_active_products
- service.py → Business logic: list_all, get_tree, get_by_id, create, update, delete
- controller.py → FastAPI handler functions; thin layer calling service
- router.py → APIRouter with prefix=/categories; /tree registered before /{category_id}

## Patterns
- Prisma model attributes use camelCase (parentId, sortOrder, deletedAt, createdAt).
- CategoryResponse.model_validate translates camelCase Prisma obj → snake_case schema fields.
- Tree is built in-memory from a single find_all query — no recursive DB queries.
- Soft delete: set deletedAt=datetime.now(timezone.utc) via prisma.category.update.

## Last Updated
2026-04-11 — initial implementation (task/0004)
