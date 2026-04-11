"""Products service — ALL business logic for product management."""
from __future__ import annotations

import csv
import io
from dataclasses import dataclass

from src.core.exceptions import ConflictError, NotFoundError
from src.modules.products.repository import ProductRepository
from src.modules.products.schemas import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)


@dataclass
class PaginatedProducts:
    items: list[ProductResponse]
    total: int


_SORT_FIELD_MAP = {
    "name": "name",
    "sku": "sku",
    "stock_quantity": "stockQuantity",
    "unit_price": "unitPrice",
}


class ProductService:
    def __init__(self, repo: ProductRepository) -> None:
        self.repo = repo

    async def list_products(
        self,
        page: int,
        limit: int,
        search: str | None,
        category_id: str | None,
        is_active: bool | None,
        sort: str,
        order: str,
    ) -> PaginatedProducts:
        """Return a paginated list of products with optional filters."""
        where: dict = {"deletedAt": None}

        if search:
            where["OR"] = [
                {"name": {"contains": search, "mode": "insensitive"}},
                {"sku": {"contains": search, "mode": "insensitive"}},
            ]
        if category_id is not None:
            where["categoryId"] = category_id
        if is_active is not None:
            where["isActive"] = is_active

        sort_key = _SORT_FIELD_MAP.get(sort, "name")
        order_by = {sort_key: order}

        skip = (page - 1) * limit
        items, total = await self.repo.find_paginated(
            skip=skip,
            take=limit,
            where=where,
            order_by=order_by,
        )
        return PaginatedProducts(
            items=[ProductResponse.model_validate(p) for p in items],
            total=total,
        )

    async def get_low_stock(self) -> list[ProductResponse]:
        """Return all active products where stock is below minimum level."""
        products = await self.repo.find_low_stock()
        return [ProductResponse.model_validate(p) for p in products]

    async def get_by_id(self, product_id: str) -> ProductResponse:
        """Return a single product or raise NotFoundError."""
        product = await self.repo.find_by_id(product_id)
        if product is None:
            raise NotFoundError("Product", product_id)
        return ProductResponse.model_validate(product)

    async def create(self, input: ProductCreate) -> ProductResponse:
        """Create a new product. Raises ConflictError on duplicate SKU or barcode."""
        if await self.repo.find_by_sku(input.sku):
            raise ConflictError(f"SKU already exists: {input.sku}")

        if input.barcode is not None and await self.repo.find_by_barcode(input.barcode):
            raise ConflictError(f"Barcode already exists: {input.barcode}")

        data: dict = {
            "name": input.name,
            "sku": input.sku,
            "unitPrice": input.unit_price,
            "costPrice": input.cost_price,
            "taxRate": input.tax_rate,
            "stockQuantity": input.stock_quantity,
            "minStockLevel": input.min_stock_level,
            "unitOfMeasure": input.unit_of_measure,
            "isActive": input.is_active,
        }
        if input.barcode is not None:
            data["barcode"] = input.barcode
        if input.category_id is not None:
            data["categoryId"] = input.category_id
        if input.description is not None:
            data["description"] = input.description
        if input.image_url is not None:
            data["imageUrl"] = input.image_url

        product = await self.repo.create(data)
        return ProductResponse.model_validate(product)

    async def update(self, product_id: str, input: ProductUpdate) -> ProductResponse:
        """Update a product. Raises NotFoundError or ConflictError as appropriate."""
        existing = await self.repo.find_by_id(product_id)
        if existing is None:
            raise NotFoundError("Product", product_id)

        if input.sku is not None:
            dup = await self.repo.find_by_sku(input.sku)
            if dup is not None and dup.id != product_id:
                raise ConflictError(f"SKU already exists: {input.sku}")

        if input.barcode is not None:
            dup = await self.repo.find_by_barcode(input.barcode)
            if dup is not None and dup.id != product_id:
                raise ConflictError(f"Barcode already exists: {input.barcode}")

        data: dict = {}
        if input.name is not None:
            data["name"] = input.name
        if input.sku is not None:
            data["sku"] = input.sku
        if input.barcode is not None:
            data["barcode"] = input.barcode
        if input.category_id is not None:
            data["categoryId"] = input.category_id
        if input.description is not None:
            data["description"] = input.description
        if input.unit_price is not None:
            data["unitPrice"] = input.unit_price
        if input.cost_price is not None:
            data["costPrice"] = input.cost_price
        if input.tax_rate is not None:
            data["taxRate"] = input.tax_rate
        if input.stock_quantity is not None:
            data["stockQuantity"] = input.stock_quantity
        if input.min_stock_level is not None:
            data["minStockLevel"] = input.min_stock_level
        if input.unit_of_measure is not None:
            data["unitOfMeasure"] = input.unit_of_measure
        if input.image_url is not None:
            data["imageUrl"] = input.image_url
        if input.is_active is not None:
            data["isActive"] = input.is_active

        product = await self.repo.update(product_id, data)
        return ProductResponse.model_validate(product)

    async def delete(self, product_id: str) -> None:
        """Soft-delete a product. Raises NotFoundError if not found."""
        existing = await self.repo.find_by_id(product_id)
        if existing is None:
            raise NotFoundError("Product", product_id)
        await self.repo.soft_delete(product_id)

    async def import_from_csv(self, contents: bytes) -> dict:
        """Bulk-import products from CSV. Returns ImportResult dict."""
        reader = csv.DictReader(io.StringIO(contents.decode("utf-8")))
        created = 0
        skipped = 0
        errors: list[dict] = []

        for row_num, row in enumerate(reader, start=2):  # start=2 since row 1 is header
            name = row.get("name", "").strip()
            sku = row.get("sku", "").strip()

            if not name or not sku:
                errors.append({
                    "row": row_num,
                    "sku": sku or "",
                    "reason": "Missing required field",
                })
                continue

            if await self.repo.find_by_sku(sku):
                skipped += 1
                continue

            data: dict = {
                "name": name,
                "sku": sku,
                "unitPrice": int(row.get("unit_price", 0) or 0),
                "costPrice": int(row.get("cost_price", 0) or 0),
                "taxRate": float(row.get("tax_rate", 0.0) or 0.0),
                "stockQuantity": int(row.get("stock_quantity", 0) or 0),
                "minStockLevel": int(row.get("min_stock_level", 0) or 0),
                "unitOfMeasure": row.get("unit_of_measure", "pcs").strip() or "pcs",
                "isActive": True,
            }

            barcode = row.get("barcode", "").strip()
            if barcode:
                data["barcode"] = barcode

            description = row.get("description", "").strip()
            if description:
                data["description"] = description

            await self.repo.create(data)
            created += 1

        return {"created": created, "skipped": skipped, "errors": errors}
