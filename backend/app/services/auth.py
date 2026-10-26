
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.schema import User
from app.schemas.auth import RegisterRequest
from app.security.passwords import hash_password


class DuplicateUserError(Exception):
    """Raised when an email or phone number is already registered."""


def register_customer(
    db: Session,
    registration: RegisterRequest,
) -> User:
    """
    Register a customer using a hashed password.

    The role is assigned by the backend and can never be selected by
    the registration request.
    """
    email = str(registration.email).strip().lower()
    phone = registration.phone.strip()

    existing_user = db.scalar(
        select(User).where(
            or_(
                func.lower(User.email) == email,
                User.phone == phone,
            )
        )
    )

    if existing_user is not None:
        if existing_user.email.strip().lower() == email:
            raise DuplicateUserError("Email is already registered.")

        raise DuplicateUserError("Phone number is already registered.")

    user = User(
        email=email,
        password_hash=hash_password(registration.password),
        name=registration.name,
        phone=phone,
        address=registration.address,
        role="CUSTOMER",
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        # Protect against concurrent registrations that pass the
        # duplicate check before either transaction commits.
        db.rollback()
        raise DuplicateUserError(
            "Email or phone number is already registered."
        ) from None

    db.refresh(user)
    return user
