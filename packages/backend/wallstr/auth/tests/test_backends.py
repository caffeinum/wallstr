import secrets
from datetime import timedelta
from unittest import mock
from uuid import uuid4

import pytest
from fastapi.requests import HTTPConnection
from pydantic import SecretStr

from wallstr.auth.backends import AuthenticatedUser, JWTAuthenticationBackend
from wallstr.auth.utils import generate_jwt
from wallstr.conf import settings


@pytest.fixture
def auth_backend() -> JWTAuthenticationBackend:
    return JWTAuthenticationBackend()


def headers(data: dict[str, str]) -> list[tuple[bytes, bytes]]:
    _list: list[tuple[bytes, bytes]] = []
    for k, v in data.items():
        _list.append((k.lower().encode("latin-1"), v.encode("latin-1")))
    return _list


async def test_no_auth_header(auth_backend: JWTAuthenticationBackend) -> None:
    request = HTTPConnection({"type": "http", "headers": []})
    result = await auth_backend.authenticate(request)
    assert result is None


async def test_invalid_auth_header_format(
    auth_backend: JWTAuthenticationBackend,
) -> None:
    request = HTTPConnection(
        {"type": "http", "headers": headers({"Authorization": "invalid-format"})}
    )
    result = await auth_backend.authenticate(request)
    assert result is None


async def test_wrong_auth_scheme(auth_backend: JWTAuthenticationBackend) -> None:
    request = HTTPConnection(
        {"type": "http", "headers": headers({"Authorization": "Basic some-token"})}
    )
    result = await auth_backend.authenticate(request)
    assert result is None


async def test_invalid_token(auth_backend: JWTAuthenticationBackend) -> None:
    with mock.patch.object(
        settings, "SECRET_KEY", SecretStr(secrets.token_urlsafe(64))
    ):
        token = generate_jwt(uuid4())
    request = HTTPConnection(
        {"type": "http", "headers": headers({"Authorization": f"Bearer {token}"})}
    )
    result = await auth_backend.authenticate(request)
    assert result is None


async def test_expired_token(auth_backend: JWTAuthenticationBackend) -> None:
    token = generate_jwt(uuid4(), expires_in=timedelta(minutes=-5))
    request = HTTPConnection(
        {"type": "http", "headers": headers({"Authorization": f"Bearer {token}"})}
    )
    result = await auth_backend.authenticate(request)
    assert result is None


async def test_successful_authentication(
    auth_backend: JWTAuthenticationBackend, request: HTTPConnection
) -> None:
    user_id = uuid4()
    token = generate_jwt(user_id)
    request = HTTPConnection(
        {"type": "http", "headers": headers({"Authorization": f"Bearer {token}"})}
    )

    result = await auth_backend.authenticate(request)
    assert result is not None

    credentials, user = result
    assert credentials.scopes == ["authenticated"]
    assert isinstance(user, AuthenticatedUser)
    assert user.identity == str(user_id)
    assert user.is_authenticated is True
