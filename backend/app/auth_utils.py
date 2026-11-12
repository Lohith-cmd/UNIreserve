import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Tuple
import bcrypt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException, status
from jose import JWTError, jwt
from app.config import settings

# Global in-memory cache for loaded RSA keys
_rsa_keys: Optional[Tuple[str, str]] = None


def hash_password(password: str) -> str:
    """
    Hashes a password using bcrypt with standard salt rounds.
    Truncates to 72 bytes as per bcrypt specification.
    """
    salt = bcrypt.gensalt(rounds=12)
    pwd_bytes = password.encode("utf-8")[:72]
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    Verifies a password against a stored hash.
    Supports standard bcrypt hashes ($2b$, $2a$, $2y$) and plaintext fallback
    for the database seed demo accounts (e.g. 'Bits@1').
    """
    pwd_bytes = plain_password.encode("utf-8")[:72]
    if stored_hash.startswith(("$2b$", "$2a$", "$2y$")):
        try:
            return bcrypt.checkpw(pwd_bytes, stored_hash.encode("utf-8"))
        except Exception:
            return False
    # Seed data fallback (plaintext string)
    return secrets.compare_digest(plain_password, stored_hash)


def get_jwt_keys() -> Tuple[str, str]:
    """
    Retrieves or generates the RSA keypair for RS256 token signing/verification.
    Returns (private_key_pem, public_key_pem).
    """
    global _rsa_keys
    if _rsa_keys is not None:
        return _rsa_keys

    project_root = Path(__file__).resolve().parent.parent.parent
    priv_path = Path(settings.JWT_PRIVATE_KEY_PATH)
    if not priv_path.is_absolute():
        priv_path = project_root / priv_path

    pub_path = Path(settings.JWT_PUBLIC_KEY_PATH)
    if not pub_path.is_absolute():
        pub_path = project_root / pub_path

    if priv_path.exists() and pub_path.exists():
        priv_pem = priv_path.read_text(encoding="utf-8")
        pub_pem = pub_path.read_text(encoding="utf-8")
        _rsa_keys = (priv_pem, pub_pem)
        return _rsa_keys

    # Auto-generate RSA 2048-bit keypair if not present
    priv_path.parent.mkdir(parents=True, exist_ok=True)
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    pub_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    priv_path.write_text(priv_pem, encoding="utf-8")
    pub_path.write_text(pub_pem, encoding="utf-8")
    _rsa_keys = (priv_pem, pub_pem)
    return _rsa_keys


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates an RS256 signed JWT token."""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now})
    priv_pem, _ = get_jwt_keys()
    return jwt.encode(to_encode, priv_pem, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decodes and validates an RS256 JWT token."""
    _, pub_pem = get_jwt_keys()
    try:
        payload = jwt.decode(token, pub_pem, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
