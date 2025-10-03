from passlib.context import CryptContext


pwd_ctx = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(plaintext: str) -> str:
    """Hash a plaintext password using bcrypt."""
    if isinstance(plaintext, (bytes, bytearray)):
        plaintext = plaintext.decode("utf-8")
    return pwd_ctx.hash(plaintext)


def verify_password(plaintext: str, hashed: str) -> bool:
    """Verify a plaintext password against a hashed password."""
    if isinstance(plaintext, (bytes, bytearray)):
        plaintext = plaintext.decode("utf-8")
    return pwd_ctx.verify(plaintext, hashed)
