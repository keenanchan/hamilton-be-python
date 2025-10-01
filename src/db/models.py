from sqlalchemy import String, Integer, Boolean, ForeignKey, Index, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
import enum
from .base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # NOT unique here
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    identities: Mapped[list["AuthIdentity"]] = relationship("AuthIdentity", back_populates="user", cascade="all, delete-orphan")
    roles: Mapped[list["Role"]] = relationship("Role", secondary="user_roles", back_populates="users")


# Partial unique index on email WHEN email is not null
Index(
    "uq_users_email_not_null",
    User.email,
    unique=True,
    postgresql_where=User.email.isnot(None)
)


# Provider Enum denoting type of login
class ProviderEnum(str, enum.Enum):
    email = "email"
    username = "username"
    room = "room"
    phone = "phone"     # Future
    sso = "sso"         # Future


class AuthIdentity(Base):
    __tablename__ = "auth_identities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider: Mapped[ProviderEnum] = mapped_column(Enum(ProviderEnum), index=True)
    identifier: Mapped[str] = mapped_column(String(255))  # e.g. email address, username, room name
    identifier_normalized: Mapped[str] = mapped_column(String(255), index=True)  # normalized for case-insensitive matching
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # nullable for SSO or passwordless logins
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)  # primary identity for the user

    user: Mapped[User] = relationship("User", back_populates="identities")

    __table_args__ = (
        # One active identity per provider per identifier_normalized
        UniqueConstraint("provider", "identifier_normalized", name="uq_identity_provider_identifier"),
    )