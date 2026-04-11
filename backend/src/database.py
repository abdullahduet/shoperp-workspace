from __future__ import annotations

from prisma import Prisma

_db: Prisma | None = None


def get_client() -> Prisma:
    if _db is None:
        raise RuntimeError("Database client not initialised. Call connect() first.")
    return _db


async def connect() -> None:
    global _db
    _db = Prisma()
    await _db.connect()


async def disconnect() -> None:
    global _db
    if _db is not None:
        await _db.disconnect()
        _db = None


async def get_db() -> Prisma:
    """FastAPI dependency that yields the Prisma client."""
    yield get_client()
