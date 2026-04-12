"""
Integration tests for categories endpoints:
  GET    /api/categories
  GET    /api/categories/tree
  POST   /api/categories
  PUT    /api/categories/:id
  DELETE /api/categories/:id

Tests run against the FastAPI TestClient with the Prisma DB layer mocked.
No live database is required.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from src.core.auth import create_access_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def body(response) -> dict:
    return json.loads(response.content)


def _make_fake_category(
    *,
    cat_id: str = "cat-uuid-1",
    name: str = "Test Category",
    description: str | None = None,
    parent_id: str | None = None,
    sort_order: int = 0,
) -> MagicMock:
    """Create a MagicMock that mimics a Prisma Category model."""
    cat = MagicMock()
    cat.id = cat_id
    cat.name = name
    cat.description = description
    cat.parentId = parent_id
    cat.sortOrder = sort_order
    cat.createdAt = datetime(2024, 1, 1, tzinfo=timezone.utc)
    cat.deletedAt = None
    return cat


def _make_fake_user(
    *,
    user_id: str = "user-uuid-1",
    role: str = "admin",
) -> MagicMock:
    user = MagicMock()
    user.id = user_id
    user.email = f"{role}@test.com"
    user.name = f"{role.title()} User"
    user.role = role
    user.isActive = True
    user.lastLoginAt = None
    user.createdAt = datetime(2024, 1, 1, tzinfo=timezone.utc)
    user.deletedAt = None
    return user


def _make_category_db(
    find_many_return=None,
    find_first_return=None,
    create_return=None,
    update_return=None,
    count_return: int = 0,
) -> MagicMock:
    """Build a mock Prisma client with category method stubs."""
    db = MagicMock()
    db.category.find_many = AsyncMock(return_value=find_many_return or [])
    db.category.find_first = AsyncMock(return_value=find_first_return)
    db.category.create = AsyncMock(return_value=create_return)
    db.category.update = AsyncMock(return_value=update_return)
    db.category.count = AsyncMock(return_value=count_return)
    # product.count is used by has_active_products check in delete
    db.product.count = AsyncMock(return_value=0)
    # user.find_first is needed for auth checks
    db.user.find_first = AsyncMock(return_value=None)
    return db


def _make_client(mock_db: MagicMock) -> TestClient:
    """Return a FastAPI TestClient with the given mock DB injected."""
    with patch("src.database._db", mock_db), \
         patch("src.database.connect", new_callable=AsyncMock), \
         patch("src.database.disconnect", new_callable=AsyncMock):
        import src.main as main_module
        return TestClient(main_module.app, raise_server_exceptions=False)


def _admin_token() -> tuple[str, MagicMock]:
    user = _make_fake_user(role="admin")
    token = create_access_token({"sub": user.id, "role": "admin"})
    return token, user


def _manager_token() -> tuple[str, MagicMock]:
    user = _make_fake_user(user_id="manager-uuid", role="manager")
    token = create_access_token({"sub": user.id, "role": "manager"})
    return token, user


def _staff_token() -> tuple[str, MagicMock]:
    user = _make_fake_user(user_id="staff-uuid", role="staff")
    token = create_access_token({"sub": user.id, "role": "staff"})
    return token, user


# ---------------------------------------------------------------------------
# GET /api/categories
# ---------------------------------------------------------------------------

class TestListCategories:
    def test_returns_200_with_list(self):
        fake_cat = _make_fake_category()
        token, user = _admin_token()
        db = _make_category_db(find_many_return=[fake_cat])
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/categories", cookies={"access_token": token})

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        assert isinstance(b["data"], list)

    def test_returns_401_without_auth(self):
        db = _make_category_db()
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/categories")

        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/categories/tree
# ---------------------------------------------------------------------------

class TestGetTree:
    def test_returns_200_with_tree(self):
        parent = _make_fake_category(cat_id="parent-id", name="Parent")
        child = _make_fake_category(cat_id="child-id", name="Child", parent_id="parent-id")
        token, user = _admin_token()
        db = _make_category_db(find_many_return=[parent, child])
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.get("/api/categories/tree", cookies={"access_token": token})

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True
        # Should have 1 root with 1 child
        assert len(b["data"]) == 1
        assert len(b["data"][0]["children"]) == 1


# ---------------------------------------------------------------------------
# POST /api/categories
# ---------------------------------------------------------------------------

class TestCreateCategory:
    def test_admin_can_create_category_returns_201(self):
        fake_cat = _make_fake_category(name="Electronics")
        token, user = _admin_token()
        db = _make_category_db(create_return=fake_cat)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/categories",
                json={"name": "Electronics"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 201
        b = body(resp)
        assert b["success"] is True

    def test_manager_can_create_category_returns_201(self):
        fake_cat = _make_fake_category(name="Clothing")
        token, user = _manager_token()
        db = _make_category_db(create_return=fake_cat)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/categories",
                json={"name": "Clothing"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 201

    def test_staff_cannot_create_category_returns_403(self):
        token, user = _staff_token()
        db = _make_category_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/categories",
                json={"name": "Forbidden"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 403

    def test_missing_name_returns_422(self):
        token, user = _admin_token()
        db = _make_category_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.post(
                "/api/categories",
                json={},
                cookies={"access_token": token},
            )

        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PUT /api/categories/:id
# ---------------------------------------------------------------------------

class TestUpdateCategory:
    def test_manager_can_update_category_returns_200(self):
        existing = _make_fake_category(cat_id="cat-id", name="Old Name")
        updated = _make_fake_category(cat_id="cat-id", name="New Name")
        token, user = _manager_token()
        db = _make_category_db(find_first_return=existing, update_return=updated)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.put(
                "/api/categories/cat-id",
                json={"name": "New Name"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True

    def test_nonexistent_category_returns_404(self):
        token, user = _admin_token()
        db = _make_category_db(find_first_return=None)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.put(
                "/api/categories/nonexistent-id",
                json={"name": "Updated"},
                cookies={"access_token": token},
            )

        assert resp.status_code == 404
        assert body(resp)["code"] == "NOT_FOUND"


# ---------------------------------------------------------------------------
# DELETE /api/categories/:id
# ---------------------------------------------------------------------------

class TestDeleteCategory:
    def test_admin_can_delete_category_returns_200(self):
        existing = _make_fake_category(cat_id="cat-id")
        token, user = _admin_token()
        db = _make_category_db(find_first_return=existing, update_return=existing)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.delete(
                "/api/categories/cat-id",
                cookies={"access_token": token},
            )

        assert resp.status_code == 200
        b = body(resp)
        assert b["success"] is True

    def test_manager_cannot_delete_category_returns_403(self):
        token, user = _manager_token()
        db = _make_category_db()
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.delete(
                "/api/categories/some-id",
                cookies={"access_token": token},
            )

        assert resp.status_code == 403

    def test_delete_with_active_products_returns_422(self):
        existing = _make_fake_category(cat_id="cat-id")
        token, user = _admin_token()
        db = _make_category_db(find_first_return=existing)
        # Simulate category having active products — guard must fire
        db.product.count = AsyncMock(return_value=1)
        db.user.find_first = AsyncMock(return_value=user)
        client = _make_client(db)

        with patch("src.database._db", db), \
             patch("src.database.connect", new_callable=AsyncMock), \
             patch("src.database.disconnect", new_callable=AsyncMock):
            resp = client.delete(
                "/api/categories/cat-id",
                cookies={"access_token": token},
            )

        assert resp.status_code == 422
