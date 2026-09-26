from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.deps import (
    get_current_user,
    get_db,
    verify_resident_access,
)
from src.core.logging import logger
from src.crud.care_report import (
    create_care_report,
    delete_care_report,
    get_all_care_reports,
    get_care_report_by_id,
    get_care_reports_by_resident,
    update_care_report,
)
from src.crud.user_resident_permission import get_permissions_by_user
from src.models.care_report import CareReport
from src.models.user import User
from src.schemas.care_report import (
    CareReportCreate,
    CareReportResponse,
    CareReportUpdate,
)

router = APIRouter(prefix="/care-reports", tags=["Care Reports"])


@router.post(
    "",
    response_model=CareReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a care report",
)
def create_report(
    report_data: CareReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CareReport:
    """Create a new clinical/daily care report. User must have access to the resident."""
    # Verify access to target resident
    verify_resident_access(
        resident_id=report_data.resident_id,
        current_user=current_user,
        db=db,
    )

    # Stamp author if not set
    if report_data.created_by is None or current_user.role != "admin":
        report_data.created_by = current_user.id

    report = create_care_report(db, report_data=report_data)
    logger.info(
        "Care report %s authored by user %s for resident %s",
        report.id,
        current_user.id,
        report.resident_id,
    )
    return report


@router.get(
    "",
    response_model=list[CareReportResponse],
    summary="List accessible care reports",
)
def list_care_reports(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CareReport]:
    """Retrieve care reports accessible to the current user."""
    if current_user.role == "admin":
        return get_all_care_reports(db, skip=skip, limit=limit)

    permissions = get_permissions_by_user(db, current_user.id)
    resident_ids = [p.resident_id for p in permissions]
    if not resident_ids:
        return []

    return (
        db.query(CareReport)
        .filter(CareReport.resident_id.in_(resident_ids))
        .order_by(CareReport.report_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get(
    "/resident/{resident_id}",
    response_model=list[CareReportResponse],
    summary="List reports for a specific resident",
)
def get_reports_for_resident(
    resident_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CareReport]:
    """Retrieve all reports for a specific resident, ordered by date descending."""
    verify_resident_access(resident_id=resident_id, current_user=current_user, db=db)
    return get_care_reports_by_resident(
        db, resident_id=resident_id, skip=skip, limit=limit
    )


@router.get(
    "/{report_id}",
    response_model=CareReportResponse,
    summary="Get care report by ID",
)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CareReport:
    """Retrieve a specific care report. Access is verified against resident permissions."""
    report = get_care_report_by_id(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Care report with ID {report_id} not found",
        )

    verify_resident_access(
        resident_id=report.resident_id, current_user=current_user, db=db
    )
    return report


@router.patch(
    "/{report_id}",
    response_model=CareReportResponse,
    summary="Update a care report",
)
def modify_report(
    report_id: int,
    report_data: CareReportUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CareReport:
    """Update care report content. Only the author or an admin may modify reports."""
    report = get_care_report_by_id(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Care report with ID {report_id} not found",
        )

    verify_resident_access(
        resident_id=report.resident_id, current_user=current_user, db=db
    )

    if current_user.role != "admin" and report.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to edit reports authored by someone else",
        )

    updated = update_care_report(
        db, report_id=report_id, report_data=report_data
    )
    logger.info("Care report %s updated by user %s", report_id, current_user.id)
    return updated


@router.delete(
    "/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a care report",
)
def remove_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a care report. Only the author or an admin may delete."""
    report = get_care_report_by_id(db, report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Care report with ID {report_id} not found",
        )

    verify_resident_access(
        resident_id=report.resident_id, current_user=current_user, db=db
    )

    if current_user.role != "admin" and report.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to delete reports authored by someone else",
        )

    delete_care_report(db, report_id)
    logger.info("Care report %s deleted by user %s", report_id, current_user.id)
