from src.database import get_db
from src.models import User
from utils.utils import _utcnow
from sqlalchemy.orm import Session


def create_user(db: Session, name: str, email: str, password_hash: str, role: str):
    """Create a new user in the database.
    Arguments:
        db: The database session.
        name: The name of the user.
        email: The email of the user.
        password_hash: The hashed password of the user.
        role: The role of the user (e.g., 'admin', 'user').
    Returns:
        The created User object.
    """
    new_user = User(name=name, email=email, password_hash=password_hash, role=role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def get_user_by_email(db: Session, email: str):
    """Get a user by their email address.
    Arguments:
        db: The database session.
        email: The email of the user.
    Returns:
        The User object if found, otherwise None.
    """
    user = (
        db.query(User)
        .filter(User.email == email and User.deleted_date.is_(None))
        .first()
    )
    return user


def get_user_by_id(db: Session, user_id: int):
    """Get a user by their ID.
    Arguments:
        db: The database session.
        user_id: The ID of the user.
    Returns:
        The User object if found, otherwise None.
    """
    user = (
        db.query(User)
        .filter(User.id == user_id and User.deleted_date.is_(None))
        .first()
    )
    return user


def get_users(db: Session):
    """Get a list of all users.
    Arguments:
        db: The database session.
    Returns:
        A list of User objects.
    """
    users = db.query(User).all()
    return users


def update_user(
    db: Session,
    user_id: int,
    name: str = None,
    email: str = None,
    password_hash: str = None,
    role: str = None,
):
    """Update a user's information.
    Arguments:
        user_id: The ID of the user to update.
        name: The new name of the user (optional).
        email: The new email of the user (optional).
        password_hash: The new hashed password of the user (optional).
        role: The new role of the user (optional).
    Returns:
        The updated User object if found, otherwise None.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        if name is not None:
            user.name = name
        if email is not None:
            user.email = email
        if password_hash is not None:
            user.password_hash = password_hash
        if role is not None:
            user.role = role
        db.commit()
        db.refresh(user)
    return user


def delete_user_hard(db: Session, user_id: int):
    """Delete a user from the database.
    Arguments:
        db: The database session.
        user_id: The ID of the user to delete.
    Returns:
        True if the user was deleted, otherwise False.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return True
    return False


def delete_user_soft(db: Session, user_id: int):
    """Soft delete a user by setting their deleted_date to the current UTC time.
    Arguments:
        db: The database session.
        user_id: The ID of the user to soft delete.
    Returns:
        The updated User object if found, otherwise None.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user and user.deleted_date is None:
        user.deleted_date = _utcnow()
        db.commit()
        db.refresh(user)
    return user


if __name__ == "__main__":
    # Example usage of the CRUD functions
    db = next(get_db())
    new_user = create_user(
        db, "John Doe", "john.hoe@example.com", "hashed_password", "user"
    )

    print(
        f"Created user: {new_user.id}, {new_user.name}, {new_user.email}, {new_user.role}"
    )

    user = get_user_by_email(db, "john.doe@example.com")
    print(f"Retrieved user: {user.id}, {user.name}, {user.email}, {user.role}")

    updated_user = update_user(db, user.id, name="Johnathan Doe", role="admin")

    print(
        f"Updated user: {updated_user.id}, {updated_user.name}, {updated_user.email}, {updated_user.role}"
    )

    soft_deleted_user = delete_user_soft(db, user.id)
    print(
        f"Soft deleted user: {soft_deleted_user.id}, {soft_deleted_user.name}, {soft_deleted_user.email}, {soft_deleted_user.role}, Deleted Date: {soft_deleted_user.deleted_date}"
    )

    hard_deleted = delete_user_hard(db, user.id)
    print(f"Hard deleted user: {hard_deleted}")
