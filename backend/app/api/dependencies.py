import uuid

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import ExpiredSignatureError, InvalidTokenError

from app.api.errors import ApiError
from app.core.config import Settings, get_settings

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_settings),
) -> uuid.UUID:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise ApiError(401, "INVALID_CREDENTIALS", "Access token diperlukan.")
    if settings.jwt_secret is None:
        raise ApiError(503, "SERVER_UNAVAILABLE", "Konfigurasi autentikasi server belum tersedia.")

    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret.get_secret_value(),
            algorithms=["HS256"],
        )
        return uuid.UUID(str(payload["sub"]))
    except ExpiredSignatureError as error:
        raise ApiError(401, "TOKEN_EXPIRED", "Access token sudah kedaluwarsa.") from error
    except (InvalidTokenError, KeyError, TypeError, ValueError) as error:
        raise ApiError(401, "INVALID_CREDENTIALS", "Access token tidak valid.") from error
