"""Authentication and authorization dependencies for API routes."""

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session
from jwt.exceptions import InvalidTokenError

from app.database import get_db
from app.models.schema import User
from app.security.tokens import decode_access_token


_bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Return the database user identified by a valid access token."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(payload["sub"])
    except (InvalidTokenError, KeyError, TypeError, ValueError):
        raise _unauthorized() from None

    user = db.scalar(select(User).where(User.user_id == user_id))
    if user is None:
        raise _unauthorized()

    return user


def require_customer(user: User = Depends(get_current_user)) -> User:
    """Allow only users whose current database role is CUSTOMER."""
    if user.role != "CUSTOMER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions.",
        )
    return user


def require_staff_or_admin(user: User = Depends(get_current_user)) -> User:
    """Allow users whose current database role is STAFF or ADMIN."""
    if user.role not in {"STAFF", "ADMIN"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions.",
        )
    return user


def require_authenticated_user(user: User = Depends(get_current_user)) -> User:
    """Allow any authenticated user."""
    return user
