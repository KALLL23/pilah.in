"""Create or reconcile the first ADMIN account idempotently."""

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import PasswordManager
from app.db.session import get_session_factory
from app.models.models import User, UserRole
from app.schemas.auth import normalize_email


def bootstrap_admin() -> None:
    settings = get_settings()
    if settings.admin_email is None and settings.admin_password is None:
        print("Admin bootstrap skipped: ADMIN_EMAIL and ADMIN_PASSWORD are not configured")
        return
    if settings.admin_email is None or settings.admin_password is None:
        raise RuntimeError("ADMIN_EMAIL and ADMIN_PASSWORD must be configured together")

    email = normalize_email(settings.admin_email)
    password = settings.admin_password.get_secret_value()
    if len(password) < 8 or len(password) > 128:
        raise RuntimeError("ADMIN_PASSWORD must contain between 8 and 128 characters")

    with get_session_factory()() as session:
        existing = session.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if existing is not None:
            changed = False
            if existing.role != UserRole.ADMIN:
                existing.role = UserRole.ADMIN
                changed = True
            if not existing.is_active:
                existing.is_active = True
                changed = True
            if changed:
                session.commit()
                print("Admin bootstrap reconciled the configured account")
            else:
                print("Admin bootstrap verified the existing ADMIN account")
            return

        session.add(
            User(
                name="Administrator",
                email=email,
                password_hash=PasswordManager().hash(password),
                role=UserRole.ADMIN,
                is_active=True,
            )
        )
        session.commit()
        print("Admin bootstrap created the initial ADMIN account")


if __name__ == "__main__":
    bootstrap_admin()
