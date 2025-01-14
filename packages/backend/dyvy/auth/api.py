from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from dyvy.auth.errors import AuthError, EmailAlreadyRegisteredError
from dyvy.auth.schemas import (
    AccessToken,
    RefreshToken,
    SignUpRequest,
    TokenPair,
    User,
)
from dyvy.auth.services import AuthService, UserService

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/signin")


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


@router.post("/signin", response_model=TokenPair)
async def signin(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_svc: Annotated[AuthService, Depends(AuthService.inject_svc)],
) -> TokenPair:
    try:
        access_token, refresh_token = await auth_svc.signin_with_password(
            form_data.username, form_data.password
        )
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    return TokenPair(
        access_token=AccessToken(token=access_token),
        refresh_token=RefreshToken(token=refresh_token),
    )


@router.post("/refresh-token", response_model=AccessToken)
async def refresh_token(
    refresh_token: RefreshToken,
    user_svc: Annotated[UserService, Depends(UserService.inject_svc)],
) -> AccessToken:
    session = await user_svc.get_session_by_token(refresh_token.token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    # TODO: create jwt token
    access_token = ""
    return AccessToken(token=access_token)


@router.post("/signout", status_code=status.HTTP_204_NO_CONTENT)
async def signout(
    token: RefreshToken,
    user_svc: Annotated[UserService, Depends(UserService.inject_svc)],
) -> Response:
    await user_svc.revoke_session(token.token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
