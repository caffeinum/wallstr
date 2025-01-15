import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from dyvy.auth.services import UserService


@pytest.fixture(scope="function")
def user_svc(db_session: AsyncSession) -> UserService:
    return UserService(db_session)
