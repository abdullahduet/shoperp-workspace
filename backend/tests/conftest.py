"""
Shared test fixtures and configuration.

Unit tests run without a live database — all Prisma calls are mocked.
Integration tests use the FastAPI TestClient with mocked DB calls.
"""
import os
import sys

# Ensure src/ is importable from the backend/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Set required env vars before any app imports so pydantic-settings does not
# raise a validation error when DATABASE_URL / JWT_SECRET are absent.
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("JWT_SECRET", "test_secret_for_unit_tests")
os.environ.setdefault("ENVIRONMENT", "test")
