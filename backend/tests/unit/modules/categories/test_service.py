"""
Unit tests for src/modules/categories/service.py

All repository calls are mocked. Tests verify business logic only.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.categories.repository import CategoryRepository
from src.modules.categories.schemas import CategoryCreate, CategoryResponse, CategoryTreeNode, CategoryUpdate
from src.modules.categories.service import CategoryService


def _make_fake_category(
    *,
    cat_id: str = "cat-uuid-1",
    name: str = "Test Category",
    description: str | None = None,
    parent_id: str | None = None,
    sort_order: int = 0,
    created_at: datetime | None = None,
    deleted_at: datetime | None = None,
) -> MagicMock:
    """Create a MagicMock that mimics a Prisma Category model."""
    cat = MagicMock()
    cat.id = cat_id
    cat.name = name
    cat.description = description
    cat.parentId = parent_id
    cat.sortOrder = sort_order
    cat.createdAt = created_at or datetime(2024, 1, 1, tzinfo=timezone.utc)
    cat.deletedAt = deleted_at
    return cat


def _make_service() -> tuple[CategoryService, AsyncMock]:
    repo = AsyncMock(spec=CategoryRepository)
    service = CategoryService(repo)
    return service, repo


# ---------------------------------------------------------------------------
# list_all
# ---------------------------------------------------------------------------

class TestListAll:
    @pytest.mark.asyncio
    async def test_returns_list_of_category_responses(self):
        service, repo = _make_service()
        fake_cat = _make_fake_category()
        repo.find_all.return_value = [fake_cat]

        result = await service.list_all()

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], CategoryResponse)
        assert result[0].name == fake_cat.name

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_categories(self):
        service, repo = _make_service()
        repo.find_all.return_value = []

        result = await service.list_all()

        assert result == []


# ---------------------------------------------------------------------------
# get_tree
# ---------------------------------------------------------------------------

class TestGetTree:
    @pytest.mark.asyncio
    async def test_builds_tree_with_one_parent_and_one_child(self):
        service, repo = _make_service()
        parent = _make_fake_category(cat_id="parent-id", name="Parent")
        child = _make_fake_category(cat_id="child-id", name="Child", parent_id="parent-id")
        repo.find_all.return_value = [parent, child]

        result = await service.get_tree()

        assert len(result) == 1
        assert result[0].id == "parent-id"
        assert len(result[0].children) == 1
        assert result[0].children[0].id == "child-id"

    @pytest.mark.asyncio
    async def test_returns_multiple_roots_when_no_parent(self):
        service, repo = _make_service()
        cat1 = _make_fake_category(cat_id="id-1", name="Cat 1")
        cat2 = _make_fake_category(cat_id="id-2", name="Cat 2")
        repo.find_all.return_value = [cat1, cat2]

        result = await service.get_tree()

        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_categories(self):
        service, repo = _make_service()
        repo.find_all.return_value = []

        result = await service.get_tree()

        assert result == []

    @pytest.mark.asyncio
    async def test_tree_nodes_are_category_tree_node_instances(self):
        service, repo = _make_service()
        cat = _make_fake_category()
        repo.find_all.return_value = [cat]

        result = await service.get_tree()

        assert isinstance(result[0], CategoryTreeNode)


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

class TestCreate:
    @pytest.mark.asyncio
    async def test_creates_and_returns_category_response(self):
        service, repo = _make_service()
        fake_cat = _make_fake_category(name="New Category")
        repo.create.return_value = fake_cat

        result = await service.create(CategoryCreate(name="New Category"))

        assert isinstance(result, CategoryResponse)
        assert result.name == "New Category"
        repo.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_not_found_when_parent_does_not_exist(self):
        service, repo = _make_service()
        repo.find_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.create(CategoryCreate(name="Child", parent_id="nonexistent-parent"))

    @pytest.mark.asyncio
    async def test_validates_parent_exists_before_creating(self):
        service, repo = _make_service()
        parent = _make_fake_category(cat_id="parent-id")
        repo.find_by_id.return_value = parent
        repo.create.return_value = _make_fake_category(parent_id="parent-id")

        await service.create(CategoryCreate(name="Child", parent_id="parent-id"))

        repo.find_by_id.assert_awaited_once_with("parent-id")


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

class TestUpdate:
    @pytest.mark.asyncio
    async def test_updates_and_returns_category_response(self):
        service, repo = _make_service()
        existing = _make_fake_category(cat_id="cat-id", name="Old Name")
        updated = _make_fake_category(cat_id="cat-id", name="New Name")
        repo.find_by_id.return_value = existing
        repo.update.return_value = updated

        result = await service.update("cat-id", CategoryUpdate(name="New Name"))

        assert isinstance(result, CategoryResponse)
        assert result.name == "New Name"

    @pytest.mark.asyncio
    async def test_raises_not_found_when_category_missing(self):
        service, repo = _make_service()
        repo.find_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.update("nonexistent-id", CategoryUpdate(name="X"))


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

class TestDelete:
    @pytest.mark.asyncio
    async def test_soft_deletes_category(self):
        service, repo = _make_service()
        existing = _make_fake_category(cat_id="cat-id")
        repo.find_by_id.return_value = existing
        repo.has_active_products.return_value = False
        repo.soft_delete.return_value = existing

        await service.delete("cat-id")

        repo.soft_delete.assert_awaited_once_with("cat-id")

    @pytest.mark.asyncio
    async def test_raises_validation_error_when_has_active_products(self):
        service, repo = _make_service()
        existing = _make_fake_category(cat_id="cat-id")
        repo.find_by_id.return_value = existing
        repo.has_active_products.return_value = True

        with pytest.raises(ValidationError):
            await service.delete("cat-id")

    @pytest.mark.asyncio
    async def test_raises_not_found_when_category_missing(self):
        service, repo = _make_service()
        repo.find_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.delete("nonexistent-id")
