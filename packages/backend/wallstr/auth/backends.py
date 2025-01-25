from uuid import UUID

from fastapi.requests import HTTPConnection
from starlette.authentication import AuthCredentials, AuthenticationBackend, BaseUser

from wallstr.auth.errors import TokenExpiredError
from wallstr.auth.schemas import AccessToken
from wallstr.models.base import utc_now


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
            access_token = AccessToken.from_auth_header(auth_header)
            payload = access_token.decode()

            if payload["exp"] < utc_now().timestamp():
                raise TokenExpiredError()

            user_id = str(payload["sub"])
            user = AuthenticatedUser(
                user_id=UUID(user_id),
            )
            return AuthCredentials(["authenticated"]), user
        except (ValueError, TokenExpiredError):
            return None
