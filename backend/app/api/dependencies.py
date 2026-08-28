from uuid import UUID

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import ApiError
from app.core.config import Settings, get_settings
from app.core.security import (
    SecurityConfigurationError,
    TokenExpiredError,
    TokenInvalidError,
    TokenManager,
)
from app.db.session import get_db
from app.models.models import User, UserRole
from app.repositories.auth import AuthRepository

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
    session: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise ApiError(401, "INVALID_CREDENTIALS", "Access token diperlukan.")

    try:
        decoded = TokenManager(settings).decode(credentials.credentials, "access")
    except SecurityConfigurationError as error:
        raise ApiError(503, "SERVER_UNAVAILABLE", "Konfigurasi autentikasi server belum tersedia.") from error
    except TokenExpiredError as error:
        raise ApiError(401, "TOKEN_EXPIRED", "Access token sudah kedaluwarsa.") from error
    except TokenInvalidError as error:
        raise ApiError(401, "INVALID_CREDENTIALS", "Access token tidak valid.") from error

    user = await AuthRepository(session).get_user_by_id(decoded.subject)
    if user is None or not user.is_active or user.role != decoded.role:
        raise ApiError(401, "INVALID_CREDENTIALS", "Access token tidak valid.")
    return user


async def get_current_user_id(user: User = Depends(get_current_user)) -> UUID:
    return user.id


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise ApiError(403, "FORBIDDEN", "Akses ADMIN diperlukan.")
    return user
