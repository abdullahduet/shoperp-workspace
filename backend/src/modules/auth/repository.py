"""Auth repository — database queries for the users table only."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from prisma import Prisma
from prisma.models import User


class AuthRepository:
    def __init__(self, prisma: Prisma) -> None:
        self.prisma = prisma

    async def find_by_email(self, email: str) -> Optional[User]:
        """Return an active, non-deleted user matching *email*, or None."""
        return await self.prisma.user.find_first(
            where={"email": email, "deletedAt": None, "isActive": True}
        )

    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Return an active, non-deleted user matching *user_id*, or None."""
        return await self.prisma.user.find_first(
            where={"id": user_id, "deletedAt": None, "isActive": True}
        )

    async def email_exists(self, email: str) -> bool:
        """Return True if any user (active or inactive) has this email."""
        user = await self.prisma.user.find_first(
            where={"email": email, "deletedAt": None}
        )
        return user is not None

    async def create(
        self,
        email: str,
        password_hash: str,
        name: str,
        role: str,
    ) -> User:
        """Insert a new user record and return it."""
        return await self.prisma.user.create(
            data={
                "email": email,
                "passwordHash": password_hash,
                "name": name,
                "role": role,
            }
        )

    async def update_last_login(self, user_id: str) -> None:
        """Stamp last_login_at with the current UTC time."""
        await self.prisma.user.update(
            where={"id": user_id},
            data={"lastLoginAt": datetime.now(timezone.utc)},
        )

    async def update_password(self, user_id: str, password_hash: str) -> None:
        """Replace the stored password hash."""
        await self.prisma.user.update(
            where={"id": user_id},
            data={"passwordHash": password_hash},
        )
