from sqlalchemy import String, Integer, Boolean, Table, ForeignKey, Index, Enum, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
import enum
from .base import Base


# -- ASSOCIATION TABLES --
user_roles = Table(
    "user_roles",
    Base.metadata,
    mapped_column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    mapped_column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    UniqueConstraint("user_id", "role_id", name="uq_user_role")
)


role_permissions = Table(
    "role_permissions",
    Base.metadata,
    mapped_column("role_id", ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    mapped_column("permission_id", ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
    UniqueConstraint("role_id", "permission_id", name="uq_role_permission")
)


# -- MODELS --
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


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    description: Mapped[Optional[str]]

    users: Mapped[list[User]] = relationship("User", secondary=user_roles, back_populates="roles")
    permissions: Mapped[list["Permission"]] = relationship("Permission", secondary=role_permissions, back_populates="roles")


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(128), unique=True, index=True)  # e.g. "user:read", "user:assign-role"
    description: Mapped[Optional[str]]

    roles: Mapped[list[Role]] = relationship("Role", secondary=role_permissions, back_populates="permissions")