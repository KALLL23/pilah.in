from uuid import uuid4

import pytest

from app.api.dependencies import require_admin
from app.api.errors import ApiError
from app.models.models import User, UserRole


def make_user(role: UserRole) -> User:
    return User(
        id=uuid4(),
        name="Authorization Test",
        email=f"{role.value.lower()}@example.com",
        password_hash="unused-in-authorization-test",
        role=role,
        is_active=True,
    )


@pytest.mark.asyncio
async def test_require_admin_accepts_admin() -> None:
    admin = make_user(UserRole.ADMIN)

    assert await require_admin(admin) is admin


@pytest.mark.asyncio
async def test_require_admin_rejects_user() -> None:
    with pytest.raises(ApiError) as captured:
        await require_admin(make_user(UserRole.USER))

    assert captured.value.status_code == 403
    assert captured.value.code == "FORBIDDEN"
