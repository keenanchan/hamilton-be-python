from sqlalchemy import select
from src.db.base import SessionLocal
from src.db.models import User, AuthIdentity, ProviderEnum, Role, Permission
from src.core.security import hash_password

import unicodedata
from typing import Optional
from dotenv import load_dotenv
import os

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


def upsert_user_with_identity(
    db,
    *,  # force keyword arguments
    full_name: Optional[str] = None,
    provider: ProviderEnum,
    identifier: str,
    password_plaintext: str,
    email_for_profile: Optional[str] = None,
    make_superadmin: bool = False,
    is_primary: bool = True,
):
    """Create or update a user and their auth identity."""
    identifier_norm = normalize_identifier(provider, identifier)

    identity = db.scalar(
        select(AuthIdentity).where(
            AuthIdentity.provider == provider,
            AuthIdentity.identifier_norm == identifier_norm,
            AuthIdentity.is_active == True,  # noqa: E712
        )
    )

    # Update existing user/identity or create new
    if identity:
        user = identity.user
        if full_name and user.full_name != full_name:
            user.full_name = full_name
        if email_for_profile and user.email != email_for_profile:
            user.email = email_for_profile
        if password_plaintext:
            identity.password_hash = hash_password(password_plaintext)
        db.flush()
        return user

    user = User(
        full_name=full_name,
        email=email_for_profile,
        is_active=True
    )

    db.add(user)
    db.flush()  # to get user.id

    identity = AuthIdentity(
        user_id=user.id,
        provider=provider,
        identifier=identifier,
        identifier_norm=identifier_norm,
        password_hash=hash_password(password_plaintext),
        is_active=True,
        is_primary=is_primary,
        user=user
    )
    db.add(identity)

    if make_superadmin:
        superadmin_role = ensure_superadmin_role(db)
        if superadmin_role not in user.roles:
            user.roles.append(superadmin_role)

    db.flush()
    return user


def run():
    db = SessionLocal()
    try:
        superadmin_role = ensure_superadmin_role(db)

        if not os.getenv("SUPERADMIN_EMAIL") or not os.getenv("SUPERADMIN_PASSWORD"):
            raise ValueError("SUPERADMIN_EMAIL and SUPERADMIN_PASSWORD must be set in environment variables")

        # --- SUPERADMIN (email login) ---
        superadmin_user = upsert_user_with_identity(
            db,
            full_name="Superadmin",
            provider=ProviderEnum.email,
            identifier=os.getenv("SUPERADMIN_EMAIL"),
            password_plaintext=os.getenv("SUPERADMIN_PASSWORD"),
            email_for_profile=os.getenv("SUPERADMIN_EMAIL"),
            make_superadmin=True,
            is_primary=True
        )

        if superadmin_role not in superadmin_user.roles:
            superadmin_user.roles.append(superadmin_role)
        
        db.commit()
        print(f"Superadmin user ensured: {superadmin_user.full_name} ({superadmin_user.email})")

        # --- (Optional) STAFF (username login) ---
        # staff_user = upsert_user_with_identity(
        #     db,
        #     full_name="Front Desk",
        #     provider=ProviderEnum.username,
        #     identifier="concierge01",
        #     password_plaintext="FrontDesk#1",
        #     email_for_profile=None,
        # )

        # --- (Optional) RESIDENT (room+PIN login) ---
        # resident_user = upsert_user_with_identity(
        #     db,
        #     full_name="Lee, Mei",
        #     provider=ProviderEnum.room,
        #     identifier="101",             # room number
        #     password_plaintext="1234",    # short PIN; add rate limiting in API
        #     email_for_profile=None,
        # )

        # db.commit()
        # print(f"Staff user ensured: {staff_user.full_name} ({staff_user.identities[0].identifier})")
        # print(f"Resident user ensured: {resident_user.full_name} ({resident_user.identities[0].identifier})")

        print("Seeding completed.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
