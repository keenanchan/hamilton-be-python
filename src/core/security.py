from passlib.hash import bcrypt


def hash_password(plaintext: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return bcrypt.using(rounds=12).hash(plaintext)


def verify_password(plaintext: str, hashed: str) -> bool:
    """Verify a plaintext password against a hashed password."""
    return bcrypt.verify(plaintext, hashed)
