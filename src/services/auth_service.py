from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.db.models import User, AuthIdentity, ProviderEnum
from src.core.security import verify_password
from src.core.jwt_tools import issue_access_token
from ._normalize import normalize_identifier


class AuthService:
    
    # If no provider is given, try all providers in this order
    DEFAULT_PROVIDER_ORDER = [
        ProviderEnum.email,
        ProviderEnum.username,
        ProviderEnum.room
    ]

    def _auto_pick_provider(self, raw_identifier: str) -> List[ProviderEnum]:
        """Heuristic to pick provider based on identifier format."""
        s = raw_identifier.strip()
        if "@" in s:
            return [ProviderEnum.email]
        # Could add more heuristics here
        return self.DEFAULT_PROVIDER_ORDER
    
    def login(
        self,
        db: Session,
        *,
        identifier: str,
        password: str,
        provider: Optional[ProviderEnum] = None,
    ) -> Optional[str]:
        """Attempt to log in a user and return an access token if successful."""
        if not identifier or not password:
            return None
        
        providers = [provider] if provider else self._auto_pick_provider(identifier)

        # Try in order of providers until an active identity is found
        found_identity: Optional[AuthIdentity] = None
        for prov in providers:
            ident_norm = normalize_identifier(prov, identifier)
            stmt = (
                select(AuthIdentity)
                .where(
                    AuthIdentity.provider == prov,
                    AuthIdentity.identifier_normalized == ident_norm,
                    AuthIdentity.is_active == True,  # noqa: E712
                )
                .order_by(AuthIdentity.is_primary.desc())
                .limit(1)  # prefer primary identity if multiple
            )

            found_identity = db.scalar(stmt)
            if found_identity:
                break
        
        # No active identity found
        if not found_identity or not found_identity.password_hash:
            return None

        # Unable to verify password
        if not verify_password(password, found_identity.password_hash):
            return None
        
        user = found_identity.user

        # Inactive user
        if not user or not user.is_active:
            return None
        
        # Success - issue token
        # Gather roles and permissions
        roles = [role.name for role in user.roles if role]
        permissions = sorted({perm.code for role in user.roles if role for perm in role.permissions if perm})
        
        jwt = issue_access_token(
            sub=str(user.id),
            email=user.email or "",
            roles=roles,
            perms=permissions
        )

        return jwt