from src.database import get_db
from src.models import Incident
from utils.utils import _utcnow
from sqlalchemy.orm import Session


def create_incident(db: Session, incident: Incident):
    """Create a new incident in the database.
    Args:
        db (Session): The database session.
        incident (Incident): The incident object to be created.
    Returns:
        Incident: The created incident object.
    """
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def get_incident_by_id(db: Session, incident_id: int):
    """Retrieve an incident by its ID from the database.
    Args:
        db (Session): The database session.
        incident_id (int): The ID of the incident to retrieve.
    Returns:
        Incident | None: The retrieved incident object, or None if not found.
    """
    return db.query(Incident).filter(Incident.id == incident_id).first()


def get_all_incidents(db: Session):
    """Retrieve all incidents from the database.
    Args:
        db (Session): The database session.
    Returns:
        list[Incident]: A list of all incident objects.
    """
    return db.query(Incident).all()


def delete_incident(db: Session, incident_id: int):
    """Delete an incident by its ID from the database.
    Args:
        db (Session): The database session.
        incident_id (int): The ID of the incident to delete.
    Returns:
        bool: True if the incident was deleted, False if not found.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident:
        db.delete(incident)
        db.commit()
        return True
    return False


def update_incident(db: Session, incident_id: int, updated_data: dict):
    """Update an incident by its ID in the database.
    Args:
        db (Session): The database session.
        incident_id (int): The ID of the incident to update.
        updated_data (dict): A dictionary containing the updated data for the incident.
    Returns:
        Incident | None: The updated incident object, or None if not found.
    """
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if incident:
        for key, value in updated_data.items():
            setattr(incident, key, value)
        db.commit()
        db.refresh(incident)
        return incident
    return None
