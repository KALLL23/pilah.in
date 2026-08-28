from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import RefreshToken, User, UserRole


class EmailAlreadyExistsError(Exception):
    pass


@dataclass(frozen=True)
class StoredRefreshToken:
    token: RefreshToken
    user: User


class AuthRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def create_user(self, *, name: str, email: str, password_hash: str) -> User:
        user = User(
            name=name,
            email=email,
            password_hash=password_hash,
            role=UserRole.USER,
            is_active=True,
        )
        self.session.add(user)
        try:
            await self.session.flush()
        except IntegrityError as error:
            await self.session.rollback()
            raise EmailAlreadyExistsError from error
        return user

    async def save_refresh_token(
        self,
        user: User,
        *,
        token_hash: str,
        expires_at: datetime,
    ) -> None:
        self.session.add(
            RefreshToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
            )
        )
        await self.session.commit()
        await self.session.refresh(user)

    async def get_refresh_token_for_update(self, token_hash: str) -> StoredRefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken, User)
            .join(User, User.id == RefreshToken.user_id)
            .where(RefreshToken.token_hash == token_hash)
            .with_for_update(of=RefreshToken)
        )
        row = result.one_or_none()
        return StoredRefreshToken(token=row[0], user=row[1]) if row else None

    async def rotate_refresh_token(
        self,
        stored: StoredRefreshToken,
        *,
        revoked_at: datetime,
        new_token_hash: str,
        new_expires_at: datetime,
    ) -> None:
        stored.token.revoked_at = revoked_at
        self.session.add(
            RefreshToken(
                user_id=stored.user.id,
                token_hash=new_token_hash,
                expires_at=new_expires_at,
            )
        )
        await self.session.commit()

    async def revoke_refresh_token(self, token_hash: str, revoked_at: datetime) -> None:
        stored = await self.get_refresh_token_for_update(token_hash)
        if stored is not None and stored.token.revoked_at is None:
            stored.token.revoked_at = revoked_at
            await self.session.commit()
