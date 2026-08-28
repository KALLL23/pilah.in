from uuid import uuid4

import pytest

from app.core.config import Settings
from app.core.security import (
    PasswordManager,
    SecurityConfigurationError,
    TokenInvalidError,
    TokenManager,
    hash_refresh_token,
)
from app.models.models import UserRole

JWT_SECRET = "0123456789abcdef0123456789abcdef"


def test_passwords_use_argon2id_and_verify_safely() -> None:
    manager = PasswordManager()
    password_hash = manager.hash("correct-horse-battery")

    assert password_hash.startswith("$argon2id$")
    assert manager.verify("correct-horse-battery", password_hash) is True
    assert manager.verify("wrong-password", password_hash) is False


@pytest.mark.parametrize("role", [UserRole.USER, UserRole.ADMIN])
def test_token_pair_contains_only_supported_database_role(role: UserRole) -> None:
    manager = TokenManager(Settings(jwt_secret=JWT_SECRET))
    user_id = uuid4()

    pair = manager.issue_pair(user_id, role)
    access = manager.decode(pair.access_token, "access")
    refresh = manager.decode(pair.refresh_token, "refresh")

    assert access.subject == user_id
    assert access.role == role
    assert access.token_type == "access"
    assert refresh.subject == user_id
    assert refresh.role == role
    assert refresh.token_type == "refresh"
    assert access.token_id != refresh.token_id


def test_refresh_token_cannot_be_used_as_access_token() -> None:
    manager = TokenManager(Settings(jwt_secret=JWT_SECRET))
    pair = manager.issue_pair(uuid4(), UserRole.USER)

    with pytest.raises(TokenInvalidError):
        manager.decode(pair.refresh_token, "access")


def test_refresh_token_hash_does_not_store_raw_token() -> None:
    raw_token = "signed-refresh-token"

    token_hash = hash_refresh_token(raw_token)

    assert token_hash != raw_token
    assert len(token_hash) == 64


def test_short_jwt_secret_is_rejected() -> None:
    manager = TokenManager(Settings(jwt_secret="too-short"))

    with pytest.raises(SecurityConfigurationError, match="at least 32"):
        manager.issue_pair(uuid4(), UserRole.USER)
