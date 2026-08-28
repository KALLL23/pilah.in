from datetime import datetime, timedelta, timezone

import jwt
from pwdlib.hashers.argon2 import Argon2Hasher
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.models import RefreshToken, User

hasher = Argon2Hasher()
settings = get_settings()


def hash_password(password: str) -> str:
    return hasher.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return hasher.verify(plain, hashed)


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    return jwt.encode(
        {"sub": user_id, "exp": expire, "type": "access"},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(user_id: str) -> tuple[str, datetime]:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days)
    token = jwt.encode(
        {"sub": user_id, "exp": expire, "type": "refresh"},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return token, expire


def register_user(db: Session, name: str, email: str, password: str) -> User:
    existing = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if existing:
        raise ValueError("Email sudah terdaftar.")

    user = User(name=name, email=email, password_hash=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if not user or not verify_password(password, user.password_hash):
        raise ValueError("Email atau sandi salah.")
    if not user.is_active:
        raise ValueError("Akun tidak aktif.")
    return user


def issue_tokens(db: Session, user: User) -> dict:
    user_id = str(user.id)

    access_token = create_access_token(user_id)
    refresh_token_str, expires_at = create_refresh_token(user_id)

    refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=hash_password(refresh_token_str),
        expires_at=expires_at,
    )
    db.add(refresh_token)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "token_type": "bearer",
    }
