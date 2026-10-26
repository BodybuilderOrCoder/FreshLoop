from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import RegisterRequest, UserResponse
from app.services.auth import DuplicateUserError, register_customer


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    registration: RegisterRequest,
    db: Annotated[Session, Depends(get_db)],
) -> UserResponse:
    """Register a new customer account."""
    try:
        user = register_customer(db, registration)
    except DuplicateUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return UserResponse.model_validate(user)
