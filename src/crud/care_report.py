from sqlalchemy.orm import Session

from src.models.care_report import CareReport
from src.schemas.care_report import CareReportCreate, CareReportUpdate
from utils.utils import _utcnow


def create_care_report(
    db: Session, report_data: CareReportCreate
) -> CareReport:
    """Create a new care report in the database.

    Args:
        db: The database session.
        report_data: Pydantic schema containing care report creation details.

    Returns:
        The created CareReport object.
    """
    report_dict = report_data.model_dump(exclude_unset=True)
    if "report_date" not in report_dict or report_dict["report_date"] is None:
        report_dict["report_date"] = _utcnow()

    new_report = CareReport(**report_dict)
    db.add(new_report)
    db.commit()
    db.refresh(new_report)
    return new_report


def get_care_report_by_id(db: Session, report_id: int) -> CareReport | None:
    """Retrieve a care report by its ID from the database.

    Args:
        db: The database session.
        report_id: The ID of the care report to retrieve.

    Returns:
        The retrieved CareReport object, or None if not found.
    """
    return db.query(CareReport).filter(CareReport.id == report_id).first()


def get_care_reports_by_resident(
    db: Session, resident_id: int, skip: int = 0, limit: int = 100
) -> list[CareReport]:
    """Retrieve all care reports for a specific resident.

    Args:
        db: The database session.
        resident_id: The ID of the resident.
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        A list of CareReport objects ordered by report_date descending.
    """
    return (
        db.query(CareReport)
        .filter(CareReport.resident_id == resident_id)
        .order_by(CareReport.report_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_all_care_reports(
    db: Session, skip: int = 0, limit: int = 100
) -> list[CareReport]:
    """Retrieve all care reports from the database.

    Args:
        db: The database session.
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        A list of all CareReport objects.
    """
    return db.query(CareReport).offset(skip).limit(limit).all()


def update_care_report(
    db: Session, report_id: int, report_data: CareReportUpdate
) -> CareReport | None:
    """Update a care report by its ID in the database.

    Args:
        db: The database session.
        report_id: The ID of the care report to update.
        report_data: Pydantic schema containing the updated fields.

    Returns:
        The updated CareReport object, or None if not found.
    """
    report = db.query(CareReport).filter(CareReport.id == report_id).first()
    if not report:
        return None

    update_dict = report_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(report, key, value)

    db.commit()
    db.refresh(report)
    return report


def delete_care_report(db: Session, report_id: int) -> bool:
    """Delete a care report by its ID from the database.

    Args:
        db: The database session.
        report_id: The ID of the care report to delete.

    Returns:
        True if the care report was deleted, False if not found.
    """
    report = db.query(CareReport).filter(CareReport.id == report_id).first()
    if report:
        db.delete(report)
        db.commit()
        return True
    return False
