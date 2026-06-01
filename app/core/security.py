import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Any, Union
from jose import jwt
from app.core.config import settings

# No longer using passlib due to PEP 594 and internal bug in newer bcrypt versions

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )

# A fixed bcrypt hash of a throwaway value (NOT a secret). Used to spend the
# same bcrypt time on the "no such user" path as on a real comparison, so login
# response timing doesn't reveal whether an email is registered.
_DUMMY_PASSWORD_HASH = "$2b$12$20vTUENjImRUc5QGH6636eaRFqMb8A.Esf7Vua1BNTO.0YaqBv8DC"

def fake_verify_password(plain_password: str) -> None:
    """Run a throwaway bcrypt comparison to equalize timing with the real path."""
    bcrypt.checkpw(plain_password.encode("utf-8"), _DUMMY_PASSWORD_HASH.encode("utf-8"))

def get_password_hash(password: str) -> str:
    # Hash a password for the first time
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
