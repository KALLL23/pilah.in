"""Password hashing and signed JWT primitives."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from pwdlib import PasswordHash

from app.core.config import Settings
from app.models.models import UserRole

JWT_ALGORITHM = "HS256"
JWT_ISSUER = "pilah.in"
JWT_AUDIENCE = "pilah.in-mobile"


class SecurityConfigurationError(Exception):
    pass


class TokenInvalidError(Exception):
    pass


class TokenExpiredError(TokenInvalidError):
    pass


@dataclass(frozen=True)
class DecodedToken:
    subject: UUID
    role: UserRole
    token_type: str
    token_id: UUID
    expires_at: datetime


@dataclass(frozen=True)
class IssuedTokenPair:
    access_token: str
    refresh_token: str
    access_expires_at: datetime
    refresh_expires_at: datetime


class PasswordManager:
    def __init__(self) -> None:
        self._hasher = PasswordHash.recommended()

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return self._hasher.verify(password, password_hash)
        except Exception:
            return False


# A valid hash keeps missing-email login attempts on the same Argon2 verification path.
DUMMY_PASSWORD_HASH = PasswordManager().hash("pilah.in-dummy-login-password")


class TokenManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def issue_pair(self, user_id: UUID, role: UserRole) -> IssuedTokenPair:
        now = datetime.now(timezone.utc)
        access_expires_at = now + timedelta(minutes=self.settings.access_token_minutes)
        refresh_expires_at = now + timedelta(days=self.settings.refresh_token_days)
        return IssuedTokenPair(
            access_token=self._encode(user_id, role, "access", now, access_expires_at),
            refresh_token=self._encode(user_id, role, "refresh", now, refresh_expires_at),
            access_expires_at=access_expires_at,
            refresh_expires_at=refresh_expires_at,
        )

    def decode(self, token: str, expected_type: str) -> DecodedToken:
        secret = self._secret()
        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=[JWT_ALGORITHM],
                audience=JWT_AUDIENCE,
                issuer=JWT_ISSUER,
                options={"require": ["sub", "role", "type", "jti", "iat", "exp"]},
            )
            token_type = str(payload["type"])
            if token_type != expected_type:
                raise TokenInvalidError
            return DecodedToken(
                subject=UUID(str(payload["sub"])),
                role=UserRole(str(payload["role"])),
                token_type=token_type,
                token_id=UUID(str(payload["jti"])),
                expires_at=datetime.fromtimestamp(float(payload["exp"]), timezone.utc),
            )
        except ExpiredSignatureError as error:
            raise TokenExpiredError from error
        except TokenInvalidError:
            raise
        except (InvalidTokenError, KeyError, TypeError, ValueError) as error:
            raise TokenInvalidError from error

    def _encode(
        self,
        user_id: UUID,
        role: UserRole,
        token_type: str,
        issued_at: datetime,
        expires_at: datetime,
    ) -> str:
        return jwt.encode(
            {
                "sub": str(user_id),
                "role": role.value,
                "type": token_type,
                "jti": str(uuid4()),
                "iat": issued_at,
                "exp": expires_at,
                "iss": JWT_ISSUER,
                "aud": JWT_AUDIENCE,
            },
            self._secret(),
            algorithm=JWT_ALGORITHM,
        )

    def _secret(self) -> str:
        if self.settings.jwt_secret is None:
            raise SecurityConfigurationError("JWT_SECRET is required")
        secret = self.settings.jwt_secret.get_secret_value()
        if len(secret) < 32:
            raise SecurityConfigurationError("JWT_SECRET must contain at least 32 characters")
        return secret


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
