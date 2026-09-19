from src.database import get_db
from src.models import Resident
from utils.utils import _utcnow
from sqlalchemy.orm import Session


def create_resident(db: Session, resident: Resident):
    """Create a new resident in the database.
    Args:
        db (Session): The database session.
        resident (Resident): The resident object to be created.
    Returns:
        Resident: The created resident object.
    """
    db.add(resident)
    db.commit()
    db.refresh(resident)
    return resident


def get_resident_by_id(db: Session, resident_id: int):
    """Retrieve a resident by its ID from the database.
    Args:
        db (Session): The database session.
        resident_id (int): The ID of the resident to retrieve.
    Returns:
        Resident | None: The retrieved resident object, or None if not found.
    """
    return db.query(Resident).filter(Resident.id == resident_id).first()


def get_all_residents(db: Session):
    """Retrieve all residents from the database.
    Args:
        db (Session): The database session.
    Returns:
        list[Resident]: A list of all resident objects.
    """
    return db.query(Resident).all()


def delete_resident(db: Session, resident_id: int):
    """Delete a resident by its ID from the database.
    Args:
        db (Session): The database session.
        resident_id (int): The ID of the resident to delete.
    Returns:
        bool: True if the resident was deleted, False if not found.
    """
    resident = db.query(Resident).filter(Resident.id == resident_id).first()
    if resident:
        db.delete(resident)
        db.commit()
        return True
    return False


def update_resident(db: Session, resident_id: int, updated_data: dict):
    """Update a resident by its ID in the database.
    Args:
        db (Session): The database session.
        resident_id (int): The ID of the resident to update.
        updated_data (dict): A dictionary containing the updated data for the resident.
    Returns:
        Resident | None: The updated resident object, or None if not found.
    """
    resident = db.query(Resident).filter(Resident.id == resident_id).first()
    if resident:
        for key, value in updated_data.items():
            setattr(resident, key, value)
        db.commit()
        db.refresh(resident)
        return resident
    return None
