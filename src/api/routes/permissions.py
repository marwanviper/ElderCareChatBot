from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.deps import get_current_user, get_db, require_role
from src.core.logging import logger
from src.crud.resident import get_resident_by_id
from src.crud.user import get_user_by_id
from src.crud.user_resident_permission import (
    create_user_resident_permission,
    delete_user_resident_permission,
    get_all_user_resident_permissions,
    get_permissions_by_resident,
    get_permissions_by_user,
    get_user_resident_permission,
)
from src.models.user import User
from src.models.user_resident_permission import UserResidentPermission
from src.schemas.user_resident_permission import (
    UserResidentPermissionCreate,
    UserResidentPermissionResponse,
)

router = APIRouter(prefix="/permissions", tags=["Permissions"])


@router.post(
    "",
    response_model=UserResidentPermissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign resident permission to user (Admin only)",
)
def assign_permission(
    permission_data: UserResidentPermissionCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
) -> UserResidentPermission:
    """Grant a user permission to access a resident's records. Requires admin role."""
    # Ensure user exists
    user = get_user_by_id(db, permission_data.user_id, include_deleted=False)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {permission_data.user_id} not found",
        )

    # Ensure resident exists
    resident = get_resident_by_id(db, permission_data.resident_id)
    if not resident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resident with ID {permission_data.resident_id} not found",
        )

    # Check if already assigned
    existing = get_user_resident_permission(
        db, user_id=permission_data.user_id, resident_id=permission_data.resident_id
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already has permission for this resident",
        )

    perm = create_user_resident_permission(db, permission_data=permission_data)
    logger.info(
        "Admin granted permission for user %s to resident %s",
        perm.user_id,
        perm.resident_id,
    )
    return perm


@router.get(
    "",
    response_model=list[UserResidentPermissionResponse],
    summary="List all permissions (Admin only)",
)
def list_permissions(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
) -> list[UserResidentPermission]:
    """List all user-resident permission links. Requires administrator role."""
    return get_all_user_resident_permissions(db, skip=skip, limit=limit)


@router.get(
    "/user/{user_id}",
    response_model=list[UserResidentPermissionResponse],
    summary="List permissions assigned to a user",
)
def list_user_permissions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[UserResidentPermission]:
    """Retrieve all resident permissions assigned to a specific user."""
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to view another user's permissions",
        )
    return get_permissions_by_user(db, user_id)


@router.get(
    "/resident/{resident_id}",
    response_model=list[UserResidentPermissionResponse],
    summary="List users assigned to a resident (Admin only)",
)
def list_resident_permissions(
    resident_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
) -> list[UserResidentPermission]:
    """Retrieve all users authorized to access a specific resident."""
    return get_permissions_by_resident(db, resident_id)


@router.delete(
    "/{user_id}/{resident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke resident permission from user (Admin only)",
)
def revoke_permission(
    user_id: int,
    resident_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
) -> None:
    """Revoke access permission for a resident from a user. Requires admin role."""
    deleted = delete_user_resident_permission(
        db, user_id=user_id, resident_id=resident_id
    )
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission record not found",
        )
    logger.info("Admin revoked permission for user %s to resident %s", user_id, resident_id)
