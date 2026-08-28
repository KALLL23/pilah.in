from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.core.security import PasswordManager, TokenManager, hash_refresh_token
from app.models.models import RefreshToken, User, UserRole
from app.repositories.auth import StoredRefreshToken
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth import AuthService, InvalidCredentialsError, InvalidRefreshTokenError

JWT_SECRET = "0123456789abcdef0123456789abcdef"


def make_user(*, email: str, password_hash: str, role: UserRole = UserRole.USER) -> User:
    now = datetime.now(timezone.utc)
    user = User(
        id=uuid4(),
        name="Test User",
        email=email,
        password_hash=password_hash,
        role=role,
        is_active=True,
    )
    user.created_at = now
    user.updated_at = now
    return user


class FakeAuthRepository:
    def __init__(self) -> None:
        self.users: dict[str, User] = {}
        self.tokens: dict[str, StoredRefreshToken] = {}

    async def create_user(self, *, name: str, email: str, password_hash: str) -> User:
        user = make_user(email=email, password_hash=password_hash)
        user.name = name
        self.users[email] = user
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        return self.users.get(email)

    async def get_user_by_id(self, user_id):
        return next((user for user in self.users.values() if user.id == user_id), None)

    async def save_refresh_token(self, user: User, *, token_hash: str, expires_at: datetime) -> None:
        token = RefreshToken(
            id=uuid4(),
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            revoked_at=None,
        )
        self.tokens[token_hash] = StoredRefreshToken(token=token, user=user)

    async def get_refresh_token_for_update(self, token_hash: str) -> StoredRefreshToken | None:
        return self.tokens.get(token_hash)

    async def rotate_refresh_token(
        self,
        stored: StoredRefreshToken,
        *,
        revoked_at: datetime,
        new_token_hash: str,
        new_expires_at: datetime,
    ) -> None:
        stored.token.revoked_at = revoked_at
        token = RefreshToken(
            id=uuid4(),
            user_id=stored.user.id,
            token_hash=new_token_hash,
            expires_at=new_expires_at,
            revoked_at=None,
        )
        self.tokens[new_token_hash] = StoredRefreshToken(token=token, user=stored.user)

    async def revoke_refresh_token(self, token_hash: str, revoked_at: datetime) -> None:
        stored = self.tokens.get(token_hash)
        if stored is not None:
            stored.token.revoked_at = revoked_at


def make_service(repository: FakeAuthRepository) -> AuthService:
    settings = Settings(jwt_secret=JWT_SECRET)
    return AuthService(repository, settings)


@pytest.mark.asyncio
async def test_register_always_creates_user_role_and_stores_hashed_refresh_token() -> None:
    repository = FakeAuthRepository()
    service = make_service(repository)

    response = await service.register(
        RegisterRequest(name="  Test   User ", email="USER@EXAMPLE.COM", password="strong-password")
    )

    user = repository.users["user@example.com"]
    assert user.role == UserRole.USER
    assert user.password_hash.startswith("$argon2id$")
    assert response.user.role == UserRole.USER
    assert response.refresh_token not in repository.tokens
    assert hash_refresh_token(response.refresh_token) in repository.tokens


@pytest.mark.asyncio
async def test_login_rejects_wrong_password() -> None:
    repository = FakeAuthRepository()
    password_manager = PasswordManager()
    repository.users["user@example.com"] = make_user(
        email="user@example.com",
        password_hash=password_manager.hash("correct-password"),
    )
    service = make_service(repository)

    with pytest.raises(InvalidCredentialsError):
        await service.login(LoginRequest(email="user@example.com", password="wrong-password"))


@pytest.mark.asyncio
async def test_refresh_rotates_token_and_rejects_replay() -> None:
    repository = FakeAuthRepository()
    service = make_service(repository)
    registered = await service.register(
        RegisterRequest(name="Test User", email="user@example.com", password="strong-password")
    )

    refreshed = await service.refresh(registered.refresh_token)

    assert refreshed.refresh_token != registered.refresh_token
    old_stored = repository.tokens[hash_refresh_token(registered.refresh_token)]
    assert old_stored.token.revoked_at is not None
    with pytest.raises(InvalidRefreshTokenError):
        await service.refresh(registered.refresh_token)


@pytest.mark.asyncio
async def test_refresh_rejects_token_when_database_role_has_changed() -> None:
    repository = FakeAuthRepository()
    service = make_service(repository)
    registered = await service.register(
        RegisterRequest(name="Test User", email="user@example.com", password="strong-password")
    )
    repository.users["user@example.com"].role = UserRole.ADMIN

    with pytest.raises(InvalidRefreshTokenError):
        await service.refresh(registered.refresh_token)


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token_idempotently() -> None:
    repository = FakeAuthRepository()
    service = make_service(repository)
    registered = await service.register(
        RegisterRequest(name="Test User", email="user@example.com", password="strong-password")
    )

    await service.logout(registered.refresh_token)
    await service.logout(registered.refresh_token)

    stored = repository.tokens[hash_refresh_token(registered.refresh_token)]
    assert stored.token.revoked_at is not None
