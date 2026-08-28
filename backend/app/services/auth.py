from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.core.config import Settings
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    IssuedTokenPair,
    PasswordManager,
    SecurityConfigurationError,
    TokenExpiredError,
    TokenInvalidError,
    TokenManager,
    hash_refresh_token,
)
from app.models.models import User, UserRole
from app.repositories.auth import AuthRepository, EmailAlreadyExistsError
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse


class InvalidCredentialsError(Exception):
    pass


class InvalidRefreshTokenError(Exception):
    pass


class ExpiredRefreshTokenError(InvalidRefreshTokenError):
    pass


class InactiveUserError(Exception):
    pass


class AuthService:
    def __init__(
        self,
        repository: AuthRepository,
        settings: Settings,
        password_manager: PasswordManager | None = None,
        token_manager: TokenManager | None = None,
    ) -> None:
        self.repository = repository
        self.settings = settings
        self.password_manager = password_manager or PasswordManager()
        self.token_manager = token_manager or TokenManager(settings)

    async def register(self, request: RegisterRequest) -> TokenResponse:
        password_hash = self.password_manager.hash(request.password.get_secret_value())
        user = await self.repository.create_user(
            name=request.name,
            email=request.email,
            password_hash=password_hash,
        )
        return await self._issue_and_store(user)

    async def login(self, request: LoginRequest) -> TokenResponse:
        user = await self.repository.get_user_by_email(request.email)
        password_matches = self.password_manager.verify(
            request.password.get_secret_value(),
            user.password_hash if user is not None else DUMMY_PASSWORD_HASH,
        )
        if user is None or not password_matches:
            raise InvalidCredentialsError
        if not user.is_active:
            raise InvalidCredentialsError
        return await self._issue_and_store(user)

    async def refresh(self, refresh_token: str) -> TokenResponse:
        try:
            decoded = self.token_manager.decode(refresh_token, "refresh")
        except TokenExpiredError as error:
            raise ExpiredRefreshTokenError from error
        except TokenInvalidError as error:
            raise InvalidRefreshTokenError from error

        stored = await self.repository.get_refresh_token_for_update(hash_refresh_token(refresh_token))
        now = datetime.now(timezone.utc)
        if (
            stored is None
            or stored.token.revoked_at is not None
            or stored.token.expires_at <= now
            or stored.user.id != decoded.subject
            or stored.user.role != decoded.role
        ):
            raise InvalidRefreshTokenError
        if not stored.user.is_active:
            raise InactiveUserError

        pair = self.token_manager.issue_pair(stored.user.id, stored.user.role)
        await self.repository.rotate_refresh_token(
            stored,
            revoked_at=now,
            new_token_hash=hash_refresh_token(pair.refresh_token),
            new_expires_at=pair.refresh_expires_at,
        )
        return self._response(stored.user, pair)

    async def logout(self, refresh_token: str) -> None:
        await self.repository.revoke_refresh_token(
            hash_refresh_token(refresh_token),
            datetime.now(timezone.utc),
        )

    async def get_active_user(self, user_id: UUID) -> User:
        user = await self.repository.get_user_by_id(user_id)
        if user is None or not user.is_active:
            raise InactiveUserError
        return user

    async def _issue_and_store(self, user: User) -> TokenResponse:
        pair = self.token_manager.issue_pair(user.id, user.role)
        await self.repository.save_refresh_token(
            user,
            token_hash=hash_refresh_token(pair.refresh_token),
            expires_at=pair.refresh_expires_at,
        )
        return self._response(user, pair)

    def _response(self, user: User, pair: IssuedTokenPair) -> TokenResponse:
        now = datetime.now(timezone.utc)
        return TokenResponse(
            access_token=pair.access_token,
            refresh_token=pair.refresh_token,
            access_expires_in=max(1, int((pair.access_expires_at - now).total_seconds())),
            refresh_expires_in=max(1, int((pair.refresh_expires_at - now).total_seconds())),
            user=UserResponse.model_validate(user),
        )


__all__ = [
    "AuthService",
    "EmailAlreadyExistsError",
    "ExpiredRefreshTokenError",
    "InactiveUserError",
    "InvalidCredentialsError",
    "InvalidRefreshTokenError",
    "SecurityConfigurationError",
    "UserRole",
]
