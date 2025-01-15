from datetime import datetime
from uuid import UUID

from pydantic import EmailStr
from sqlalchemy import ForeignKey, Unicode
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_utils.types import PasswordType

from dyvy.models.base import HashType, RecordModel, string_column


class UserModel(RecordModel):
    __tablename__ = "auth_users"

    email: Mapped[EmailStr] = mapped_column(unique=True, index=True, nullable=False)
    username: Mapped[str] = string_column(32)
    fullname: Mapped[str] = string_column(128)
    password: Mapped[str | None] = mapped_column(
        PasswordType(
            schemes=["pbkdf2_sha512"],
            pdbkdf2_sha512__salt_size=16,
            pdbkdf2_sha512__rounds=25000,
        ),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_verified: Mapped[bool] = mapped_column(default=False, nullable=False)

    sessions: Mapped[list["SessionModel"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class SessionModel(RecordModel):
    __tablename__ = "auth_sessions"

    refresh_token: Mapped[str] = mapped_column(
        HashType(), unique=True, nullable=False, index=True
    )
    expires_at: Mapped[datetime] = mapped_column(nullable=False)

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("auth_users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user: Mapped[UserModel] = relationship(back_populates="sessions")

    device_info: Mapped[str | None] = string_column(255)
    ip_address: Mapped[str | None] = mapped_column(
        Unicode(50), nullable=False, default=""
    )
