from sqlalchemy.orm import Session

from src.models.resident import Resident
from src.schemas.resident import ResidentCreate, ResidentUpdate


def create_resident(db: Session, resident_data: ResidentCreate) -> Resident:
    """Create a new resident in the database.

    Args:
        db: The database session.
        resident_data: Pydantic schema containing resident creation details.

    Returns:
        The newly created Resident model instance.
    """
    new_resident = Resident(
        name=resident_data.name,
        date_of_birth=resident_data.date_of_birth,
        room_number=resident_data.room_number,
    )
    db.add(new_resident)
    db.commit()
    db.refresh(new_resident)
    return new_resident


def get_resident_by_id(db: Session, resident_id: int) -> Resident | None:
    """Retrieve a resident by their unique ID.

    Args:
        db: The database session.
        resident_id: The ID of the resident to retrieve.

    Returns:
        Resident if found, otherwise None.
    """
    return db.query(Resident).filter(Resident.id == resident_id).first()


def get_all_residents(
    db: Session, skip: int = 0, limit: int = 100
) -> list[Resident]:
    """Retrieve a paginated list of residents.

    Args:
        db: The database session.
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        A list of Resident model instances.
    """
    return db.query(Resident).offset(skip).limit(limit).all()


def update_resident(
    db: Session, resident_id: int, resident_data: ResidentUpdate
) -> Resident | None:
    """Update an existing resident's information using partial data.

    Args:
        db: The database session.
        resident_id: The ID of the resident to update.
        resident_data: Pydantic schema containing fields to update.

    Returns:
        The updated Resident object if found, otherwise None.
    """
    resident = db.query(Resident).filter(Resident.id == resident_id).first()
    if not resident:
        return None

    update_dict = resident_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(resident, key, value)

    db.commit()
    db.refresh(resident)
    return resident


def delete_resident(db: Session, resident_id: int) -> bool:
    """Delete a resident by their unique ID.

    Args:
        db: The database session.
        resident_id: The ID of the resident to delete.

    Returns:
        True if deleted, False if not found.
    """
    resident = db.query(Resident).filter(Resident.id == resident_id).first()
    if resident:
        db.delete(resident)
        db.commit()
        return True
    return False
