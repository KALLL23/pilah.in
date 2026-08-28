from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.api.errors import ApiError
from app.core.config import Settings, get_settings
from app.core.security import SecurityConfigurationError
from app.db.session import get_db
from app.models.models import User
from app.repositories.auth import AuthRepository, EmailAlreadyExistsError
from app.schemas.auth import (
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth import (
    AuthService,
    ExpiredRefreshTokenError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])


def get_auth_service(
    session: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthService:
    return AuthService(AuthRepository(session), settings)


def raise_auth_api_error(error: Exception) -> None:
    if isinstance(error, EmailAlreadyExistsError):
        raise ApiError(409, "EMAIL_ALREADY_REGISTERED", "Email sudah terdaftar.") from error
    if isinstance(error, InvalidCredentialsError):
        raise ApiError(401, "INVALID_CREDENTIALS", "Email atau password tidak valid.") from error
    if isinstance(error, ExpiredRefreshTokenError):
        raise ApiError(401, "TOKEN_EXPIRED", "Refresh token sudah kedaluwarsa.") from error
    if isinstance(error, InvalidRefreshTokenError):
        raise ApiError(401, "INVALID_CREDENTIALS", "Refresh token tidak valid.") from error
    if isinstance(error, InactiveUserError):
        raise ApiError(403, "FORBIDDEN", "Akun pengguna tidak aktif.") from error
    if isinstance(error, SecurityConfigurationError):
        raise ApiError(503, "SERVER_UNAVAILABLE", "Konfigurasi autentikasi server belum tersedia.") from error
    raise error


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    payload: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        return await service.register(payload)
    except (EmailAlreadyExistsError, SecurityConfigurationError) as error:
        raise_auth_api_error(error)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        return await service.login(payload)
    except (InvalidCredentialsError, SecurityConfigurationError) as error:
        raise_auth_api_error(error)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        return await service.refresh(payload.refresh_token)
    except (
        ExpiredRefreshTokenError,
        InactiveUserError,
        InvalidRefreshTokenError,
        SecurityConfigurationError,
    ) as error:
        raise_auth_api_error(error)


@router.post("/logout", status_code=204)
async def logout(
    payload: LogoutRequest,
    service: AuthService = Depends(get_auth_service),
) -> Response:
    await service.logout(payload.refresh_token)
    return Response(status_code=204)


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(user)
