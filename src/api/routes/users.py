from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_db, require_role
from src.core.logging import logger
from src.core.security import hash_password
from src.crud.user import (
    create_user,
    delete_user_hard,
    delete_user_soft,
    get_user_by_email,
    get_user_by_id,
    get_users,
    update_user,
)
from src.models.user import User
from src.schemas.user import UserCreate, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "",
    response_model=list[UserResponse],
    summary="List all users (Admin only)",
)
def list_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    include_deleted: bool = False,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
) -> list[User]:
    """Retrieve a paginated list of users. Requires administrator role."""
    return get_users(
        db, skip=skip, limit=limit, include_deleted=include_deleted
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """Retrieve details of a user. Admins can view any user; caregivers can only view themselves."""
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view another user's profile",
        )

    user = get_user_by_id(db, user_id=user_id, include_deleted=True)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )
    return user


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user (Admin only)",
)
def admin_create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
) -> User:
    """Create a new user with an assigned role. Requires administrator role."""
    existing = get_user_by_email(db, user_data.email, include_deleted=True)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists",
        )

    hashed_pwd = hash_password(user_data.password)
    user = create_user(db, user_data=user_data, password_hash=hashed_pwd)
    logger.info("Admin created new user with ID %s", user.id)
    return user


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user details",
)
def modify_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    """Update a user's details. Caregivers can only update their own profile and cannot change roles."""
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update another user's profile",
        )

    # Non-admins cannot alter role
    if current_user.role != "admin" and user_data.role is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot change your own role",
        )

    # If updating email, ensure it's not already used
    if user_data.email is not None:
        existing = get_user_by_email(db, user_data.email, include_deleted=True)
        if existing and existing.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email address is already in use by another account",
            )

    pwd_hash = (
        hash_password(user_data.password) if user_data.password else None
    )
    updated = update_user(
        db, user_id=user_id, user_data=user_data, password_hash=pwd_hash
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )
    return updated


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user (Admin only)",
)
def remove_user(
    user_id: int,
    hard: bool = Query(default=False, description="Whether to permanently hard-delete"),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
) -> None:
    """Soft-delete (default) or hard-delete a user account. Requires administrator role."""
    user = get_user_by_id(db, user_id, include_deleted=True)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found",
        )

    if hard:
        delete_user_hard(db, user_id)
        logger.info("Admin permanently hard-deleted user %s", user_id)
    else:
        delete_user_soft(db, user_id)
        logger.info("Admin soft-deleted user %s", user_id)
