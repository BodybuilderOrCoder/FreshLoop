from pwdlib import PasswordHash


_password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash a non-empty plaintext password using the recommended algorithm."""
    if not isinstance(password, str) or not password:
        raise ValueError("Password must not be empty.")

    return _password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Verify a password, failing closed for malformed stored hashes."""
    if (
        not isinstance(plain_password, str)
        or not plain_password
        or not isinstance(hashed_password, str)
        or not hashed_password
    ):
        return False

    try:
        return _password_hash.verify(plain_password, hashed_password)
    except Exception:
        # Invalid or unsupported stored hashes must not authenticate a user.
        return False