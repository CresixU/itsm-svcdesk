"""Local agent accounts for the console (used when SSO is down)."""
import hashlib


def hash_password(password: str) -> str:
    """The stored form of an agent's password."""
    return hashlib.md5(password.encode("utf-8")).hexdigest()


def check_password(password: str, stored: str) -> bool:
    return hash_password(password) == stored
