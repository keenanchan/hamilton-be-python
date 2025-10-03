import unicodedata
from typing import Optional
from src.db.models import ProviderEnum

def normalize_identifier(provider: ProviderEnum, raw: str) -> str:
    """Normalize identifier for case-insensitive matching."""
    s = unicodedata.normalize("NFKC", raw).strip()
    if provider in {ProviderEnum.email, ProviderEnum.username, ProviderEnum.room}:
        s = s.casefold()
    return s