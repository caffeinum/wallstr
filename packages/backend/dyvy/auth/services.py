import secrets
from datetime import timedelta
from uuid import UUID

from sqlalchemy import sql

from dyvy.auth.models import SessionModel, UserModel
from dyvy.auth.schemas import SignUpRequest
from dyvy.models.base import utc_now
from dyvy.services import BaseService


class AuthService(BaseService):
    async def get_user_by_email(self, email: str) -> UserModel | None:
        async with self.tx():
            result = await self.db.execute(sql.select(UserModel).filter_by(email=email))
        return result.scalar_one_or_none()

    async def create_user(self, payload: SignUpRequest) -> UserModel:
        async with self.tx():
            result = await self.db.execute(
                sql.insert(UserModel)
                .values(**payload.model_dump())
                .returning(UserModel)
            )
        return result.scalar_one()

    async def create_session(
        self, user_id: UUID, device_info: str | None = None
    ) -> SessionModel:
        refresh_token = secrets.token_urlsafe(32)
        async with self.tx():
            result = await self.db.execute(
                sql.insert(SessionModel)
                .values(
                    refresh_token=refresh_token,
                    user_id=user_id,
                    device_info=device_info,
                    # TODO: move 7 days to settings
                    expires_at=utc_now() + timedelta(days=7),
                )
                .returning(SessionModel)
            )
        return result.scalar_one()

    async def get_session_by_token(self, refresh_token: str) -> SessionModel | None:
        async with self.tx():
            result = await self.db.execute(
                sql.select(SessionModel).where(
                    SessionModel.refresh_token == refresh_token,
                    SessionModel.expires_at > utc_now(),
                )
            )
        return result.scalar_one_or_none()

    async def revoke_session(self, refresh_token: str) -> None:
        async with self.tx():
            await self.db.execute(
                sql.delete(SessionModel).filter_by(refresh_token=refresh_token)
            )
