"""
Unit tests for src/modules/suppliers/service.py

All repository calls are mocked. Tests verify business logic only.
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.exceptions import NotFoundError
from src.modules.suppliers.repository import SupplierRepository
from src.modules.suppliers.schemas import SupplierCreate, SupplierResponse, SupplierUpdate
from src.modules.suppliers.service import PaginatedSuppliers, SupplierService


def _make_fake_supplier(
    *,
    supplier_id: str = "supplier-uuid-1",
    name: str = "Test Supplier",
    contact_person: str | None = "Jane Doe",
    phone: str | None = "01711000000",
    email: str | None = "test@supplier.com",
    address: str | None = "123 Main St",
    city: str | None = "Dhaka",
    country: str | None = "Bangladesh",
    payment_terms: str | None = "Net 30",
    is_active: bool = True,
    notes: str | None = None,
    created_at: datetime | None = None,
) -> MagicMock:
    """Create a MagicMock that mimics a Prisma Supplier model (camelCase attrs)."""
    supplier = MagicMock()
    supplier.id = supplier_id
    supplier.name = name
    supplier.contactPerson = contact_person
    supplier.phone = phone
    supplier.email = email
    supplier.address = address
    supplier.city = city
    supplier.country = country
    supplier.paymentTerms = payment_terms
    supplier.isActive = is_active
    supplier.notes = notes
    supplier.createdAt = created_at or datetime(2024, 1, 1, tzinfo=timezone.utc)
    supplier.deletedAt = None
    return supplier


def _make_service() -> tuple[SupplierService, AsyncMock]:
    repo = AsyncMock(spec=SupplierRepository)
    service = SupplierService(repo)
    return service, repo


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

class TestList:
    @pytest.mark.asyncio
    async def test_returns_paginated_suppliers(self):
        service, repo = _make_service()
        fake_supplier = _make_fake_supplier()
        repo.find_paginated.return_value = ([fake_supplier], 1)

        result = await service.list(page=1, limit=20, search=None, is_active=None)

        assert isinstance(result, PaginatedSuppliers)
        assert result.total == 1
        assert len(result.items) == 1
        assert isinstance(result.items[0], SupplierResponse)

    @pytest.mark.asyncio
    async def test_applies_search_filter(self):
        service, repo = _make_service()
        repo.find_paginated.return_value = ([], 0)

        await service.list(page=1, limit=20, search="acme", is_active=None)

        call_kwargs = repo.find_paginated.call_args.args
        where = call_kwargs[2]
        assert "name" in where
        assert where["name"]["contains"] == "acme"

    @pytest.mark.asyncio
    async def test_applies_is_active_filter(self):
        service, repo = _make_service()
        repo.find_paginated.return_value = ([], 0)

        await service.list(page=1, limit=20, search=None, is_active=True)

        call_kwargs = repo.find_paginated.call_args.args
        where = call_kwargs[2]
        assert where["isActive"] is True

    @pytest.mark.asyncio
    async def test_calculates_correct_skip(self):
        service, repo = _make_service()
        repo.find_paginated.return_value = ([], 0)

        await service.list(page=3, limit=10, search=None, is_active=None)

        call_kwargs = repo.find_paginated.call_args.args
        assert call_kwargs[0] == 20  # (3-1)*10


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------

class TestGetById:
    @pytest.mark.asyncio
    async def test_returns_supplier_response_when_found(self):
        service, repo = _make_service()
        fake_supplier = _make_fake_supplier()
        repo.find_by_id.return_value = fake_supplier

        result = await service.get_by_id("supplier-uuid-1")

        assert isinstance(result, SupplierResponse)
        assert result.name == fake_supplier.name

    @pytest.mark.asyncio
    async def test_raises_not_found_when_supplier_missing(self):
        service, repo = _make_service()
        repo.find_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.get_by_id("nonexistent-id")


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

class TestCreate:
    @pytest.mark.asyncio
    async def test_creates_and_returns_supplier_response(self):
        service, repo = _make_service()
        fake_supplier = _make_fake_supplier()
        repo.create.return_value = fake_supplier

        result = await service.create(
            SupplierCreate(name="Test Supplier", country="Bangladesh")
        )

        assert isinstance(result, SupplierResponse)
        repo.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_maps_snake_case_to_camel_case_in_data(self):
        service, repo = _make_service()
        fake_supplier = _make_fake_supplier()
        repo.create.return_value = fake_supplier

        await service.create(
            SupplierCreate(
                name="Test Supplier",
                contact_person="John",
                payment_terms="Net 60",
            )
        )

        data_passed = repo.create.call_args.args[0]
        assert "contactPerson" in data_passed
        assert data_passed["contactPerson"] == "John"
        assert "paymentTerms" in data_passed
        assert data_passed["paymentTerms"] == "Net 60"


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

class TestUpdate:
    @pytest.mark.asyncio
    async def test_updates_and_returns_supplier_response(self):
        service, repo = _make_service()
        fake_supplier = _make_fake_supplier()
        updated_supplier = _make_fake_supplier(name="Updated Supplier")
        repo.find_by_id.return_value = fake_supplier
        repo.update.return_value = updated_supplier

        result = await service.update("supplier-uuid-1", SupplierUpdate(name="Updated Supplier"))

        assert isinstance(result, SupplierResponse)
        repo.update.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_raises_not_found_when_supplier_missing(self):
        service, repo = _make_service()
        repo.find_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.update("nonexistent-id", SupplierUpdate(name="X"))


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

class TestDelete:
    @pytest.mark.asyncio
    async def test_soft_deletes_supplier(self):
        service, repo = _make_service()
        fake_supplier = _make_fake_supplier()
        repo.find_by_id.return_value = fake_supplier

        await service.delete("supplier-uuid-1")

        repo.soft_delete.assert_awaited_once_with("supplier-uuid-1")

    @pytest.mark.asyncio
    async def test_raises_not_found_when_supplier_missing(self):
        service, repo = _make_service()
        repo.find_by_id.return_value = None

        with pytest.raises(NotFoundError):
            await service.delete("nonexistent-id")
