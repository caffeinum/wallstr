from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer
from starlette.authentication import requires

from dyvy.auth.errors import AuthError, EmailAlreadyRegisteredError
from dyvy.auth.schemas import (
    AccessToken,
    RefreshToken,
    SignInRequest,
    SignUpRequest,
    User,
)
from dyvy.auth.services import AuthService, UserService
from dyvy.auth.utils import generate_jwt
from dyvy.conf import settings

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/signin")

logger = structlog.get_logger()


@router.post("/signup", response_model=User, status_code=status.HTTP_201_CREATED)
async def signup(
    data: SignUpRequest,
    auth_svc: Annotated[AuthService, Depends(AuthService.inject_svc)],
) -> User:
    try:
        user = await auth_svc.signup_with_password(data)
    except EmailAlreadyRegisteredError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        ) from e

    return User.model_validate(user)


@router.post("/signin", response_model=AccessToken)
async def signin(
    data: SignInRequest,
    request: Request,
    response: Response,
    auth_svc: Annotated[AuthService, Depends(AuthService.inject_svc)],
) -> AccessToken:
    try:
        access_token, refresh_token = await auth_svc.signin_with_password(
            data.email,
            data.password,
            user_agent=request.headers.get("User-Agent"),
            ip_addr=request.client.host if request.client else None,
        )
    except AuthError as e:
        logger.exception(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    response.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        max_age=settings.JWT.refresh_token_expire_days * 24 * 60 * 60,
    )
    return AccessToken(token=access_token)


@router.post("/refresh-token", response_model=AccessToken)
async def refresh_token(
    request: Request,
    response: Response,
    user_svc: Annotated[UserService, Depends(UserService.inject_svc)],
) -> AccessToken:
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # use access_token as csrf token
    exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid access token",
    )
    auth_header = request.headers.get("Authorization", "")
    try:
        access_token = AccessToken.from_auth_header(auth_header)
        if not access_token.can_renew:
            raise exception
        payload = access_token.decode()
    except ValueError:
        raise exception from None

    session = await user_svc.get_session_by_token(refresh_token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = payload.get("sub")
    if str(session.user_id) != user_id:
        logger.critical(f"User {user_id} uses session for {session.user_id}")
        raise exception

    # update refresh token if it's about to expire
    if session.is_expiring_soon:
        new_session = await user_svc.renew_session(
            session,
            user_agent=request.headers.get("User-Agent"),
            ip_addr=request.client.host if request.client else None,
        )
        response.set_cookie(
            "refresh_token",
            new_session.refresh_token,
            httponly=True,
            max_age=settings.JWT.refresh_token_expire_days * 24 * 60 * 60,
        )

    jwt_token = generate_jwt(session.user_id)
    return AccessToken(token=jwt_token)


@router.post("/signout", status_code=status.HTTP_204_NO_CONTENT)
async def signout(
    token: RefreshToken,
    user_svc: Annotated[UserService, Depends(UserService.inject_svc)],
) -> Response:
    await user_svc.revoke_session(token.token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=User)
@requires("authenticated")
async def get_current_user(
    request: Request,
    user_svc: Annotated[UserService, Depends(UserService.inject_svc)],
) -> User:
    auth_user = request.user
    user = await user_svc.get_user(UUID(auth_user.identity))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return User.model_validate(user)
