import base64
import secrets
from datetime import timedelta
from uuid import UUID

from sqlalchemy import sql

from dyvy.auth.errors import (
    EmailAlreadyRegisteredError,
    EmailNotRegisteredError,
    InvalidPasswordError,
    PasswordNotSupportedError,
)
from dyvy.auth.models import SessionModel, UserModel
from dyvy.auth.schemas import SignUpRequest
from dyvy.auth.utils import generate_jwt
from dyvy.conf import settings
from dyvy.models.base import utc_now
from dyvy.services import BaseService


class AuthService(BaseService):
    async def signup_with_password(self, payload: SignUpRequest) -> UserModel:
        user_svc = UserService(self.db)
        async with self.tx():
            existing_user = await user_svc.get_user_by_email(payload.email)

            if existing_user:
                raise EmailAlreadyRegisteredError()

            return await user_svc.create_user(payload)

    async def signin_with_password(
        self, email: str, password: str, device_info: str | None, ip_address: str | None
    ) -> tuple[str, str]:
        user_svc = UserService(self.db)
        async with self.tx():
            user = await user_svc.get_user_by_email(email)
            if not user:
                raise EmailNotRegisteredError()

            if not user.password:
                raise PasswordNotSupportedError()

            if user.password != password:
                raise InvalidPasswordError()

            access_token = generate_jwt(user.id)
            session = await user_svc.create_session(user.id, device_info, ip_address)
        return access_token, session.refresh_token


class UserService(BaseService):
    async def get_user(self, id: UUID) -> UserModel | None:
        async with self.tx():
            result = await self.db.execute(sql.select(UserModel).filter_by(id=id))
        return result.scalar_one_or_none()

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
        self, user_id: UUID, device_info: str | None, ip_address: str | None
    ) -> SessionModel:
        refresh_token = secrets.token_bytes(64)
        async with self.tx():
            result = await self.db.execute(
                sql.insert(SessionModel)
                .values(
                    refresh_token=refresh_token,
                    user_id=user_id,
                    device_info=device_info,
                    ip_address=ip_address,
                    expires_at=utc_now()
                    + timedelta(days=settings.JWT.refresh_token_expire_days),
                )
                .returning(SessionModel)
            )
        return result.scalar_one()

    async def get_session_by_token(self, refresh_token: str) -> SessionModel | None:
        async with self.tx():
            result = await self.db.execute(
                sql.select(SessionModel).where(
                    SessionModel.refresh_token
                    == base64.urlsafe_b64decode(refresh_token),
                    SessionModel.expires_at > utc_now(),
                )
            )
        return result.scalar_one_or_none()

    async def renew_session(
        self, session: SessionModel, device_info: str | None, ip_address: str | None
    ) -> SessionModel:
        async with self.tx():
            result = await self.db.execute(
                sql.update(SessionModel)
                .filter_by(id=session.id)
                .values(
                    refresh_token=secrets.token_bytes(64),
                    device_info=device_info,
                    ip_address=ip_address,
                    expires_at=utc_now()
                    + timedelta(days=settings.JWT.refresh_token_expire_days),
                )
                .returning(SessionModel)
            )
        return result.scalar_one()

    async def revoke_session(self, refresh_token: str) -> None:
        async with self.tx():
            await self.db.execute(
                sql.delete(SessionModel).filter_by(
                    refresh_token=base64.urlsafe_b64decode(refresh_token)
                )
            )
