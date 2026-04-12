"""Categories service — ALL business logic for category management."""
from __future__ import annotations

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.categories.repository import CategoryRepository
from src.modules.categories.schemas import (
    CategoryCreate,
    CategoryResponse,
    CategoryTreeNode,
    CategoryUpdate,
)


class CategoryService:
    def __init__(self, repo: CategoryRepository) -> None:
        self.repo = repo

    async def list_all(self) -> list[CategoryResponse]:
        """Return all non-deleted categories as a flat list."""
        categories = await self.repo.find_all()
        return [CategoryResponse.model_validate(c) for c in categories]

    async def get_tree(self) -> list[CategoryTreeNode]:
        """Fetch all categories and build a nested tree in memory."""
        categories = await self.repo.find_all()

        # Build lookup by id
        nodes: dict[str, CategoryTreeNode] = {}
        for cat in categories:
            nodes[cat.id] = CategoryTreeNode(
                id=cat.id,
                name=cat.name,
                description=cat.description,
                sort_order=cat.sortOrder,
                children=[],
            )

        roots: list[CategoryTreeNode] = []
        for cat in categories:
            node = nodes[cat.id]
            if cat.parentId is None:
                roots.append(node)
            else:
                parent = nodes.get(cat.parentId)
                if parent is not None:
                    parent.children.append(node)

        return roots

    async def get_by_id(self, category_id: str) -> CategoryResponse:
        """Return a single category or raise NotFoundError."""
        cat = await self.repo.find_by_id(category_id)
        if cat is None:
            raise NotFoundError("Category", category_id)
        return CategoryResponse.model_validate(cat)

    async def create(self, input: CategoryCreate) -> CategoryResponse:
        """Create a new category. Validates parent exists if parent_id provided."""
        if input.parent_id is not None:
            parent = await self.repo.find_by_id(input.parent_id)
            if parent is None:
                raise NotFoundError("Category", input.parent_id)

        data: dict = {
            "name": input.name,
            "sortOrder": input.sort_order,
        }
        if input.description is not None:
            data["description"] = input.description
        if input.parent_id is not None:
            data["parentId"] = input.parent_id

        cat = await self.repo.create(data)
        return CategoryResponse.model_validate(cat)

    async def update(self, category_id: str, input: CategoryUpdate) -> CategoryResponse:
        """Update a category. Raises NotFoundError if not found."""
        existing = await self.repo.find_by_id(category_id)
        if existing is None:
            raise NotFoundError("Category", category_id)

        data: dict = {}
        if input.name is not None:
            data["name"] = input.name
        if input.description is not None:
            data["description"] = input.description
        if input.parent_id is not None:
            data["parentId"] = input.parent_id
        if input.sort_order is not None:
            data["sortOrder"] = input.sort_order

        cat = await self.repo.update(category_id, data)
        return CategoryResponse.model_validate(cat)

    async def delete(self, category_id: str) -> None:
        """Soft-delete a category. Raises ValidationError if it has active products."""
        existing = await self.repo.find_by_id(category_id)
        if existing is None:
            raise NotFoundError("Category", category_id)

        if await self.repo.has_active_products(category_id):
            raise ValidationError(
                "Cannot delete category with active products",
                details=[{"field": "category_id", "message": "Category has active products"}],
            )

        await self.repo.soft_delete(category_id)
