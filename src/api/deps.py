from collections.abc import Generator
from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from src.core.logging import logger
from src.core.security import decode_access_token
from src.crud.resident import get_resident_by_id
from src.crud.user import get_user_by_id
from src.crud.user_resident_permission import get_user_resident_permission
from src.database import SessionLocal
from src.models.resident import Resident
from src.models.user import Role, User

# OAuth2 scheme pointing to our login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db() -> Generator[Session, None, None]:
    """Dependency yielding a database session for request scope."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Validate bearer token and retrieve the active authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        logger.warning("Token decoding failed or token expired")
        raise credentials_exception

    user_id: int | None = payload.get("user_id")
    if user_id is None:
        logger.warning("Token missing user_id claim")
        raise credentials_exception

    user = get_user_by_id(db, user_id=user_id, include_deleted=False)
    if user is None:
        logger.warning("User with id %s not found or deactivated", user_id)
        raise credentials_exception

    return user


def require_role(*allowed_roles: str | Role) -> Callable[[User], User]:
    """Dependency factory enforcing Role-Based Access Control (RBAC)."""

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            logger.warning(
                "Access denied for user %s with role '%s'. Required one of: %s",
                current_user.id,
                current_user.role,
                allowed_roles,
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for your role",
            )
        return current_user

    return role_checker


def verify_resident_access(
    resident_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Resident:
    """Verify that the resident exists and the current user is authorized to access them."""
    resident = get_resident_by_id(db, resident_id)
    if not resident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resident with ID {resident_id} not found",
        )

    # Admins have global access to all residents
    if current_user.role == Role.ADMIN:
        return resident

    # Caregivers must have explicit permission in user_resident_permissions
    perm = get_user_resident_permission(
        db, user_id=current_user.id, resident_id=resident_id
    )
    if not perm:
        logger.warning(
            "Caregiver %s denied access to resident %s (no permission link)",
            current_user.id,
            resident_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this resident's data",
        )

    return resident
