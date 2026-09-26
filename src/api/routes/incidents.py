from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.deps import (
    get_current_user,
    get_db,
    require_role,
    verify_resident_access,
)
from src.core.logging import logger
from src.crud.incident import (
    create_incident,
    delete_incident,
    get_incident_by_id,
    get_incidents_by_resident,
    update_incident,
)
from src.models.incident import Incident
from src.models.user import User
from src.schemas.incident import (
    IncidentCreate,
    IncidentResponse,
    IncidentUpdate,
)

router = APIRouter(prefix="/incidents", tags=["Incidents"])


@router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log a new incident",
)
def report_incident(
    incident_data: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Incident:
    """Log an adverse event or incident concerning a resident."""
    verify_resident_access(
        resident_id=incident_data.resident_id,
        current_user=current_user,
        db=db,
    )
    incident = create_incident(db, incident_data=incident_data)
    logger.warning(
        "Incident %s (%s) logged for resident %s by user %s",
        incident.id,
        incident.type,
        incident.resident_id,
        current_user.id,
    )
    return incident


@router.get(
    "/resident/{resident_id}",
    response_model=list[IncidentResponse],
    summary="List incidents for a specific resident",
)
def list_incidents_for_resident(
    resident_id: int,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Incident]:
    """Retrieve all incident records for a specific resident in reverse chronological order."""
    verify_resident_access(
        resident_id=resident_id, current_user=current_user, db=db
    )
    return get_incidents_by_resident(
        db, resident_id=resident_id, skip=skip, limit=limit
    )


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Get incident by ID",
)
def get_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Incident:
    """Retrieve details of a specific incident record."""
    incident = get_incident_by_id(db, incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID {incident_id} not found",
        )
    verify_resident_access(
        resident_id=incident.resident_id, current_user=current_user, db=db
    )
    return incident


@router.patch(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Update incident details",
)
def modify_incident(
    incident_id: int,
    incident_data: IncidentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Incident:
    """Update description or follow-up notes on an incident."""
    incident = get_incident_by_id(db, incident_id)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID {incident_id} not found",
        )
    verify_resident_access(
        resident_id=incident.resident_id, current_user=current_user, db=db
    )
    updated = update_incident(
        db, incident_id=incident_id, incident_data=incident_data
    )
    logger.info("Incident %s updated", incident_id)
    return updated


@router.delete(
    "/{incident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an incident record (Admin only)",
)
def remove_incident(
    incident_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role("admin")),
) -> None:
    """Delete an incident record. Requires administrator role."""
    deleted = delete_incident(db, incident_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident with ID {incident_id} not found",
        )
    logger.info("Incident %s deleted by admin", incident_id)
