from src.database import get_db
from src.models import CareReport
from utils.utils import _utcnow
from sqlalchemy.orm import Session


def create_care_report(db: Session, care_report: CareReport):
    """Create a new care report in the database.
    Args:
        db (Session): The database session.
        care_report (CareReport): The care report object to be created.
    Returns:
        CareReport: The created care report object.
    """
    db.add(care_report)
    db.commit()
    db.refresh(care_report)
    return care_report


def get_care_report_by_id(db: Session, care_report_id: int):
    """Retrieve a care report by its ID from the database.
    Args:
        db (Session): The database session.
        care_report_id (int): The ID of the care report to retrieve.
    Returns:
        CareReport | None: The retrieved care report object, or None if not found.
    """
    return db.query(CareReport).filter(CareReport.id == care_report_id).first()


def get_all_care_reports(db: Session):
    """Retrieve all care reports from the database.
    Args:
        db (Session): The database session.
    Returns:
        list[CareReport]: A list of all care report objects.
    """
    return db.query(CareReport).all()


def delete_care_report(db: Session, care_report_id: int):
    """Delete a care report by its ID from the database.
    Args:
        db (Session): The database session.
        care_report_id (int): The ID of the care report to delete.
    Returns:
        bool: True if the care report was deleted, False if not found.
    """
    care_report = db.query(CareReport).filter(CareReport.id == care_report_id).first()
    if care_report:
        db.delete(care_report)
        db.commit()
        return True
    return False


def update_care_report(db: Session, care_report_id: int, updated_data: dict):
    """Update a care report by its ID in the database.
    Args:
        db (Session): The database session.
        care_report_id (int): The ID of the care report to update.
        updated_data (dict): A dictionary containing the updated data for the care report.
    Returns:
        CareReport | None: The updated care report object, or None if not found.
    """
    care_report = db.query(CareReport).filter(CareReport.id == care_report_id).first()
    if care_report:
        for key, value in updated_data.items():
            setattr(care_report, key, value)
        db.commit()
        db.refresh(care_report)
        return care_report
    return None
