from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import sql
from sqlalchemy.ext.asyncio import AsyncSession

from dyvy.auth.models import UserModel
from dyvy.auth.services import AuthService, UserService


@pytest.fixture
def auth_svc(db_session: AsyncSession) -> AuthService:
    return AuthService(db_session)


@pytest.fixture
def user_svc(db_session: AsyncSession) -> UserService:
    return UserService(db_session)


@pytest_asyncio.fixture
async def user(db_session: AsyncSession) -> AsyncGenerator[UserModel]:
    async with db_session.begin():
        result = await db_session.execute(
            sql.insert(UserModel)
            .values(email="test@example.com", password="password123")
            .returning(UserModel)
        )
        user = result.scalar_one()
    yield user

    async with db_session.begin():
        await db_session.execute(sql.delete(UserModel).filter_by(id=user.id))


@pytest.mark.asyncio
async def test_get_user_by_email(user_svc: UserService, user: UserModel) -> None:
    email = "test@example.com"

    result = await user_svc.get_user_by_email(email)
    assert result == user
