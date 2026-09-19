from sqlalchemy.orm import Session

from src.models.user import User
from src.schemas.user import UserCreate, UserUpdate
from utils.utils import _utcnow


def create_user(
    db: Session,
    user_data: UserCreate,
    password_hash: str | None = None,
) -> User:
    """Create a new user in the database.

    Args:
        db: The database session.
        user_data: Pydantic schema containing user creation data.
        password_hash: Optional pre-hashed password. If not provided,
            uses user_data.password as a placeholder.

    Returns:
        The newly created User model instance.
    """
    stored_password_hash = (
        password_hash if password_hash is not None else user_data.password
    )

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        password_hash=stored_password_hash,
        role=user_data.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def get_user_by_id(
    db: Session,
    user_id: int,
    include_deleted: bool = False,
) -> User | None:
    """Retrieve a user by their unique primary key ID.

    Args:
        db: The database session.
        user_id: The ID of the user to retrieve.
        include_deleted: Whether to include soft-deleted users.

    Returns:
        The User object if found, otherwise None.
    """
    query = db.query(User).filter(User.id == user_id)
    if not include_deleted:
        query = query.filter(User.deleted_date.is_(None))
    return query.first()


def get_user_by_email(
    db: Session,
    email: str,
    include_deleted: bool = False,
) -> User | None:
    """Retrieve an active user by their email address.

    Args:
        db: The database session.
        email: The email of the user.
        include_deleted: Whether to include soft-deleted users.

    Returns:
        The User object if found, otherwise None.
    """
    query = db.query(User).filter(User.email == email)
    if not include_deleted:
        query = query.filter(User.deleted_date.is_(None))
    return query.first()


def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    include_deleted: bool = False,
) -> list[User]:
    """Retrieve a paginated list of users.

    Args:
        db: The database session.
        skip: Number of records to skip (offset).
        limit: Maximum number of records to return.
        include_deleted: Whether to include soft-deleted users.

    Returns:
        A list of User objects.
    """
    query = db.query(User)
    if not include_deleted:
        query = query.filter(User.deleted_date.is_(None))
    return query.offset(skip).limit(limit).all()


def update_user(
    db: Session,
    user_id: int,
    user_data: UserUpdate,
    password_hash: str | None = None,
) -> User | None:
    """Update an existing user's information using partial update data.

    Args:
        db: The database session.
        user_id: The ID of the user to update.
        user_data: Pydantic schema containing fields to update.
        password_hash: Optional pre-hashed password if updating credentials.

    Returns:
        The updated User object if found, otherwise None.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    update_dict = user_data.model_dump(exclude_unset=True)

    # Handle password updating
    if "password" in update_dict:
        new_password = update_dict.pop("password")
        user.password_hash = (
            password_hash if password_hash is not None else new_password
        )

    for field, value in update_dict.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user


def delete_user_soft(db: Session, user_id: int) -> User | None:
    """Soft delete a user by setting deleted_date to the current UTC timestamp.

    Args:
        db: The database session.
        user_id: The ID of the user to soft delete.

    Returns:
        The updated User object if found, or None if not found or already deleted.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.deleted_date is None:
        user.deleted_date = _utcnow()
        db.commit()
        db.refresh(user)
        return user
    return None


def delete_user_hard(db: Session, user_id: int) -> bool:
    """Permanently delete a user from the database.

    Args:
        db: The database session.
        user_id: The ID of the user to permanently delete.

    Returns:
        True if the user was deleted, False if not found.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False
