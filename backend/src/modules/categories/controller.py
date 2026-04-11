"""Categories controller — thin layer: validate input, call service, return response."""
from __future__ import annotations

from fastapi import Depends
from fastapi.responses import JSONResponse

from src.core.responses import success_response
from src.database import get_db
from src.modules.categories.repository import CategoryRepository
from src.modules.categories.schemas import CategoryCreate, CategoryUpdate
from src.modules.categories.service import CategoryService


def _get_service(db=Depends(get_db)) -> CategoryService:
    return CategoryService(CategoryRepository(db))


async def list_categories(
    service: CategoryService = Depends(_get_service),
) -> JSONResponse:
    categories = await service.list_all()
    return success_response(
        data=[c.model_dump(mode="json") for c in categories],
        message="Categories retrieved",
    )


async def get_tree(
    service: CategoryService = Depends(_get_service),
) -> JSONResponse:
    tree = await service.get_tree()
    return success_response(
        data=[node.model_dump(mode="json") for node in tree],
        message="Category tree retrieved",
    )


async def get_category(
    category_id: str,
    service: CategoryService = Depends(_get_service),
) -> JSONResponse:
    cat = await service.get_by_id(category_id)
    return success_response(
        data=cat.model_dump(mode="json"),
        message="Category retrieved",
    )


async def create_category(
    body: CategoryCreate,
    service: CategoryService = Depends(_get_service),
) -> JSONResponse:
    cat = await service.create(body)
    return success_response(
        data=cat.model_dump(mode="json"),
        message="Category created",
        status_code=201,
    )


async def update_category(
    category_id: str,
    body: CategoryUpdate,
    service: CategoryService = Depends(_get_service),
) -> JSONResponse:
    cat = await service.update(category_id, body)
    return success_response(
        data=cat.model_dump(mode="json"),
        message="Category updated",
    )


async def delete_category(
    category_id: str,
    service: CategoryService = Depends(_get_service),
) -> JSONResponse:
    await service.delete(category_id)
    return success_response(data=None, message="Category deleted")
