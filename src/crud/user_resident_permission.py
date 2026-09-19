from sqlalchemy.orm import Session

from src.models.user_resident_permission import UserResidentPermission
from src.schemas.user_resident_permission import UserResidentPermissionCreate


def create_user_resident_permission(
    db: Session, permission_data: UserResidentPermissionCreate
) -> UserResidentPermission:
    """Create a new user resident permission record.

    Args:
        db: The database session.
        permission_data: Pydantic schema containing user_id and resident_id.

    Returns:
        The created UserResidentPermission object.
    """
    new_perm = UserResidentPermission(
        user_id=permission_data.user_id,
        resident_id=permission_data.resident_id,
    )
    db.add(new_perm)
    db.commit()
    db.refresh(new_perm)
    return new_perm


def get_user_resident_permission(
    db: Session, user_id: int, resident_id: int
) -> UserResidentPermission | None:
    """Retrieve a specific permission record by composite primary key.

    Args:
        db: The database session.
        user_id: The ID of the user.
        resident_id: The ID of the resident.

    Returns:
        UserResidentPermission if found, otherwise None.
    """
    return (
        db.query(UserResidentPermission)
        .filter(
            UserResidentPermission.user_id == user_id,
            UserResidentPermission.resident_id == resident_id,
        )
        .first()
    )


def get_permissions_by_user(
    db: Session, user_id: int
) -> list[UserResidentPermission]:
    """Retrieve all resident permissions granted to a specific user.

    Args:
        db: The database session.
        user_id: The ID of the user.

    Returns:
        A list of UserResidentPermission objects.
    """
    return (
        db.query(UserResidentPermission)
        .filter(UserResidentPermission.user_id == user_id)
        .all()
    )


def get_permissions_by_resident(
    db: Session, resident_id: int
) -> list[UserResidentPermission]:
    """Retrieve all users with permission to access a specific resident.

    Args:
        db: The database session.
        resident_id: The ID of the resident.

    Returns:
        A list of UserResidentPermission objects.
    """
    return (
        db.query(UserResidentPermission)
        .filter(UserResidentPermission.resident_id == resident_id)
        .all()
    )


def get_all_user_resident_permissions(
    db: Session, skip: int = 0, limit: int = 100
) -> list[UserResidentPermission]:
    """Retrieve a paginated list of all user-resident permission records.

    Args:
        db: The database session.
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        A list of UserResidentPermission objects.
    """
    return (
        db.query(UserResidentPermission)
        .offset(skip)
        .limit(limit)
        .all()
    )


def delete_user_resident_permission(
    db: Session, user_id: int, resident_id: int
) -> bool:
    """Revoke/delete a user resident permission by its composite primary key.

    Args:
        db: The database session.
        user_id: The ID of the user.
        resident_id: The ID of the resident.

    Returns:
        True if the permission was deleted, False if not found.
    """
    perm = (
        db.query(UserResidentPermission)
        .filter(
            UserResidentPermission.user_id == user_id,
            UserResidentPermission.resident_id == resident_id,
        )
        .first()
    )
    if perm:
        db.delete(perm)
        db.commit()
        return True
    return False
