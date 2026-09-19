from src.database import get_db
from src.models import UserResidentPermission
from utils.utils import _utcnow
from sqlalchemy.orm import Session


def create_user_resident_permission(
    db: Session, user_resident_permission: UserResidentPermission
):
    """Create a new user resident permission in the database.
    Args:
        db (Session): The database session.
        user_resident_permission (UserResidentPermission): The user resident permission object to be created.
    Returns:
        UserResidentPermission: The created user resident permission object.
    """
    db.add(user_resident_permission)
    db.commit()
    db.refresh(user_resident_permission)
    return user_resident_permission


def get_user_resident_permission_by_id(db: Session, user_resident_permission_id: int):
    """Retrieve a user resident permission by its ID from the database.
    Args:
        db (Session): The database session.
        user_resident_permission_id (int): The ID of the user resident permission to retrieve.
    Returns:
        UserResidentPermission | None: The retrieved user resident permission object, or None if not found.
    """
    return (
        db.query(UserResidentPermission)
        .filter(UserResidentPermission.id == user_resident_permission_id)
        .first()
    )


def get_all_user_resident_permissions(db: Session):
    """Retrieve all user resident permissions from the database.
    Args:
        db (Session): The database session.
    Returns:
        list[UserResidentPermission]: A list of all user resident permission objects.
    """
    return db.query(UserResidentPermission).all()


def delete_user_resident_permission(db: Session, user_resident_permission_id: int):
    """Delete a user resident permission by its ID from the database.
    Args:
        db (Session): The database session.
        user_resident_permission_id (int): The ID of the user resident permission to delete.
    Returns:
        bool: True if the user resident permission was deleted, False if not found.
    """
    user_resident_permission = (
        db.query(UserResidentPermission)
        .filter(UserResidentPermission.id == user_resident_permission_id)
        .first()
    )
    if user_resident_permission:
        db.delete(user_resident_permission)
        db.commit()
        return True
    return False


def update_user_resident_permission(
    db: Session, user_resident_permission_id: int, updated_data: dict
):
    """Update a user resident permission by its ID in the database.
    Args:
        db (Session): The database session.
        user_resident_permission_id (int): The ID of the user resident permission to update.
        updated_data (dict): A dictionary containing the updated data for the user resident permission.
    Returns:
        UserResidentPermission | None: The updated user resident permission object, or None if not found.
    """
    user_resident_permission = (
        db.query(UserResidentPermission)
        .filter(UserResidentPermission.id == user_resident_permission_id)
        .first()
    )
    if user_resident_permission:
        for key, value in updated_data.items():
            setattr(user_resident_permission, key, value)
        db.commit()
        db.refresh(user_resident_permission)
        return user_resident_permission
    return None
