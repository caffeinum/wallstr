from uuid import UUID

from authlib.jose import jwt
from authlib.jose.errors import BadSignatureError, DecodeError
from fastapi.requests import HTTPConnection
from starlette.authentication import AuthCredentials, AuthenticationBackend, BaseUser

from dyvy.auth.errors import TokenExpiredError
from dyvy.conf import settings
from dyvy.models.base import utc_now


class AuthenticatedUser(BaseUser):
    def __init__(self, user_id: UUID) -> None:
        self.user_id = user_id

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def display_name(self) -> str:
        return str(self.user_id)

    @property
    def identity(self) -> str:
        return str(self.user_id)


class JWTAuthenticationBackend(AuthenticationBackend):
    async def authenticate(
        self, conn: HTTPConnection
    ) -> tuple[AuthCredentials, BaseUser] | None:
        auth_header = conn.headers.get("Authorization")
        if not auth_header:
            return None

        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                return None
        except ValueError:
            return None

        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY.get_secret_value(),
            )
            exp = payload.get("exp")
            if not exp:
                raise ValueError("Missed exp claim")

            if exp < utc_now().timestamp():
                raise TokenExpiredError()

            user_id = payload.get("sub")
            user = AuthenticatedUser(
                user_id=UUID(user_id),
            )
            return AuthCredentials(["authenticated"]), user
        except (BadSignatureError, DecodeError, ValueError, TokenExpiredError):
            return None
