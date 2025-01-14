from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    username: str | None
    fullname: str | None


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    username: str
    fullname: str


class AccessToken(BaseModel):
    token: str
    token_type: str = "bearer"


class RefreshToken(BaseModel):
    token: str


class TokenPair(BaseModel):
    access_token: AccessToken
    refresh_token: RefreshToken
