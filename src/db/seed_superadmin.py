from sqlalchemy import select
from src.db.base import SessionLocal
from src.db.models import User, AuthIdentity, ProviderEnum, Role, Permission
from src.core.security import hash_password

import unicodedata
from dotenv import load_dotenv

load_dotenv()


def normalize_identifier(provider: ProviderEnum, raw: str) -> str:
    """Normalize identifier for case-insensitive matching."""
    s = unicodedata.normalize("NFKC", raw).strip()
    if provider in {ProviderEnum.email, ProviderEnum.username, ProviderEnum.room}:
        s = s.casefold()
    return s


def ensure_superadmin_role(db):
    superadmin = db.scalar(select(Role).where(Role.name == "superadmin"))
    if not superadmin:
        superadmin = Role(name="superadmin", description="Super-Administrator, with full access persmissions")
        p_assign = Permission(code="user:assign-role", description="Assign roles to users")
        p_read = Permission(code="user:read", description="Read users")
        p_write = Permission(code="user:write", description="Modify users")
        superadmin.permissions = [p_assign, p_read, p_write]
        db.add_all([superadmin, p_assign, p_read, p_write])
        db.flush()
    return superadmin
