from sqlalchemy.orm import Session

from src.models.incident import Incident
from src.schemas.incident import IncidentCreate, IncidentUpdate
from utils.utils import _utcnow


def create_incident(db: Session, incident_data: IncidentCreate) -> Incident:
    """Create a new incident in the database.

    Args:
        db: The database session.
        incident_data: Pydantic schema containing incident details.

    Returns:
        The created Incident object.
    """
    incident_dict = incident_data.model_dump(exclude_unset=True)
    if "incident_date" not in incident_dict or incident_dict["incident_date"] is None:
        incident_dict["incident_date"] = _utcnow()

    new_incident = Incident(**incident_dict)
    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)
    return new_incident


def get_incident_by_id(db: Session, incident_id: int) -> Incident | None:
    """Retrieve an incident by its ID from the database.

    Args:
        db: The database session.
        incident_id: The ID of the incident to retrieve.

    Returns:
        The retrieved Incident object, or None if not found.
    """
    return db.query(Incident).filter(Incident.id == incident_id).first()


def get_incidents_by_resident(
    db: Session, resident_id: int, skip: int = 0, limit: int = 100
) -> list[Incident]:
    """Retrieve all incidents for a specific resident ordered by date descending.

    Args:
        db: The database session.
        resident_id: The ID of the resident.
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        A list of Incident objects.
    """
    return (
        db.query(Incident)
        .filter(Incident.resident_id == resident_id)
        .order_by(Incident.incident_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_all_incidents(
    db: Session, skip: int = 0, limit: int = 100
) -> list[Incident]:
    """Retrieve all incidents from the database.

    Args:
        db: The database session.
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        A list of all Incident objects.
    """
    return db.query(Incident).offset(skip).limit(limit).all()


def update_incident(
    db: Session, incident_id: int, incident_data: IncidentUpdate
) -> Incident | None:
    """Update an incident by its ID in the database.

    Args:
        db: The database session.
        incident_id: The ID of the incident to update.
        incident_data: Pydantic schema containing the updated fields.

    Returns:
        The updated Incident object, or None if not found.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        return None

    update_dict = incident_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(incident, key, value)

    db.commit()
    db.refresh(incident)
    return incident


def delete_incident(db: Session, incident_id: int) -> bool:
    """Delete an incident by its ID from the database.

    Args:
        db: The database session.
        incident_id: The ID of the incident to delete.

    Returns:
        True if the incident was deleted, False if not found.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident:
        db.delete(incident)
        db.commit()
        return True
    return False
