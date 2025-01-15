from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordBearer

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
            device_info=request.headers.get("User-Agent"),
            ip_address=request.client.host if request.client else None,
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


# TOOD: get token from cookies
@router.post("/refresh-token", response_model=AccessToken)
async def refresh_token(
    refresh_token: RefreshToken,
    response: Response,
    user_svc: Annotated[UserService, Depends(UserService.inject_svc)],
) -> AccessToken:
    session = await user_svc.get_session_by_token(refresh_token.token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    access_token = generate_jwt(session.user_id)
    return AccessToken(token=access_token)


@router.post("/signout", status_code=status.HTTP_204_NO_CONTENT)
async def signout(
    token: RefreshToken,
    user_svc: Annotated[UserService, Depends(UserService.inject_svc)],
) -> Response:
    await user_svc.revoke_session(token.token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
