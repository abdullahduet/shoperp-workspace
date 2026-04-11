"""Suppliers service — ALL business logic for supplier management."""
from __future__ import annotations

from dataclasses import dataclass

from src.core.exceptions import NotFoundError
from src.modules.suppliers.repository import SupplierRepository
from src.modules.suppliers.schemas import SupplierCreate, SupplierResponse, SupplierUpdate


@dataclass
class PaginatedSuppliers:
    items: list[SupplierResponse]
    total: int


class SupplierService:
    def __init__(self, repo: SupplierRepository) -> None:
        self.repo = repo

    async def list(
        self,
        page: int,
        limit: int,
        search: str | None,
        is_active: bool | None,
    ) -> PaginatedSuppliers:
        """Return a paginated list of suppliers with optional filters."""
        where: dict = {"deletedAt": None}

        if search:
            where["name"] = {"contains": search, "mode": "insensitive"}
        if is_active is not None:
            where["isActive"] = is_active

        skip = (page - 1) * limit
        items, total = await self.repo.find_paginated(skip, limit, where, {"name": "asc"})
        return PaginatedSuppliers(
            items=[SupplierResponse.model_validate(s) for s in items],
            total=total,
        )

    async def get_by_id(self, supplier_id: str) -> SupplierResponse:
        """Return a single supplier or raise NotFoundError."""
        s = await self.repo.find_by_id(supplier_id)
        if s is None:
            raise NotFoundError("Supplier", supplier_id)
        return SupplierResponse.model_validate(s)

    async def create(self, input: SupplierCreate) -> SupplierResponse:
        """Create a new supplier and return it."""
        data: dict = {"name": input.name, "isActive": input.is_active}
        for field, col in [
            ("contact_person", "contactPerson"),
            ("phone", "phone"),
            ("email", "email"),
            ("address", "address"),
            ("city", "city"),
            ("country", "country"),
            ("payment_terms", "paymentTerms"),
            ("notes", "notes"),
        ]:
            val = getattr(input, field)
            if val is not None:
                data[col] = val
        return SupplierResponse.model_validate(await self.repo.create(data))

    async def update(self, supplier_id: str, input: SupplierUpdate) -> SupplierResponse:
        """Update a supplier. Raises NotFoundError if not found."""
        if await self.repo.find_by_id(supplier_id) is None:
            raise NotFoundError("Supplier", supplier_id)
        data: dict = {}
        for field, col in [
            ("name", "name"),
            ("contact_person", "contactPerson"),
            ("phone", "phone"),
            ("email", "email"),
            ("address", "address"),
            ("city", "city"),
            ("country", "country"),
            ("payment_terms", "paymentTerms"),
            ("notes", "notes"),
            ("is_active", "isActive"),
        ]:
            val = getattr(input, field)
            if val is not None:
                data[col] = val
        return SupplierResponse.model_validate(await self.repo.update(supplier_id, data))

    async def delete(self, supplier_id: str) -> None:
        """Soft-delete a supplier. Raises NotFoundError if not found."""
        if await self.repo.find_by_id(supplier_id) is None:
            raise NotFoundError("Supplier", supplier_id)
        await self.repo.soft_delete(supplier_id)
