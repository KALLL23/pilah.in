from contextlib import AbstractContextManager
from types import SimpleNamespace

from pydantic import SecretStr

from app.models.models import User, UserRole
from app.scripts import bootstrap_admin as module


class FakeResult:
    def __init__(self, user: User | None) -> None:
        self.user = user

    def scalar_one_or_none(self) -> User | None:
        return self.user


class FakeSession(AbstractContextManager):
    def __init__(self) -> None:
        self.user: User | None = None
        self.commits = 0

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, _statement) -> FakeResult:
        return FakeResult(self.user)

    def add(self, user: User) -> None:
        self.user = user

    def commit(self) -> None:
        self.commits += 1


def test_admin_bootstrap_is_idempotent(monkeypatch) -> None:
    session = FakeSession()
    settings = SimpleNamespace(
        admin_email="ADMIN@EXAMPLE.COM",
        admin_password=SecretStr("strong-admin-password"),
    )
    monkeypatch.setattr(module, "get_settings", lambda: settings)
    monkeypatch.setattr(module, "get_session_factory", lambda: lambda: session)

    module.bootstrap_admin()
    first_hash = session.user.password_hash
    module.bootstrap_admin()

    assert session.user.email == "admin@example.com"
    assert session.user.role == UserRole.ADMIN
    assert session.user.is_active is True
    assert session.user.password_hash.startswith("$argon2id$")
    assert session.user.password_hash == first_hash
    assert session.commits == 1


def test_admin_bootstrap_promotes_configured_existing_user(monkeypatch) -> None:
    session = FakeSession()
    session.user = User(
        name="Existing User",
        email="admin@example.com",
        password_hash="existing-password-hash",
        role=UserRole.USER,
        is_active=False,
    )
    settings = SimpleNamespace(
        admin_email="admin@example.com",
        admin_password=SecretStr("strong-admin-password"),
    )
    monkeypatch.setattr(module, "get_settings", lambda: settings)
    monkeypatch.setattr(module, "get_session_factory", lambda: lambda: session)

    module.bootstrap_admin()

    assert session.user.role == UserRole.ADMIN
    assert session.user.is_active is True
    assert session.user.password_hash == "existing-password-hash"
    assert session.commits == 1
