"""Auth service — ALL business logic for login, registration, and password change."""
from __future__ import annotations

from dataclasses import dataclass

from prisma.models import User

from src.core.auth import (
    create_access_token,
    hash_password,
    verify_password,
)
from src.core.exceptions import AuthError, ConflictError
from src.modules.auth.repository import AuthRepository
from src.modules.auth.schemas import UserResponse


@dataclass
class LoginResult:
    user: UserResponse
    token: str


class AuthService:
    def __init__(self, repo: AuthRepository) -> None:
        self.repo = repo

    async def login(self, email: str, password: str) -> LoginResult:
        """Verify credentials, stamp last_login_at, and return a signed JWT."""
        user = await self.repo.find_by_email(email)
        if user is None or not verify_password(password, user.passwordHash):
            raise AuthError("Invalid email or password")

        token = create_access_token({"sub": str(user.id), "role": user.role})
        await self.repo.update_last_login(user.id)

        return LoginResult(user=UserResponse.model_validate(user), token=token)

    async def register(
        self,
        email: str,
        password: str,
        name: str,
        role: str,
    ) -> UserResponse:
        """Create a new user.  Raises ConflictError if email already exists."""
        if len(password) < 8:
            raise AuthError("Password must be at least 8 characters")
        if not name.strip():
            raise AuthError("Name must not be blank")

        if await self.repo.email_exists(email):
            raise ConflictError("Email already registered")

        password_hash = hash_password(password)
        user = await self.repo.create(
            email=email,
            password_hash=password_hash,
            name=name,
            role=role,
        )
        return UserResponse.model_validate(user)

    async def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str,
    ) -> None:
        """Verify current_password then replace the hash.

        Raises AuthError if current_password is wrong.
        """
        if len(new_password) < 8:
            raise AuthError("New password must be at least 8 characters")

        if not verify_password(current_password, user.passwordHash):
            raise AuthError("Invalid email or password")

        new_hash = hash_password(new_password)
        await self.repo.update_password(user.id, new_hash)
