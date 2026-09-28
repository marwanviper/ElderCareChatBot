from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.deps import (
    get_current_user,
    get_db,
    require_role,
    verify_resident_access,
)
from src.core.logging import logger
from src.crud.resident import (
    create_resident,
    delete_resident,
    get_all_residents,
    get_resident_by_id,
    update_resident,
)
from src.crud.user_resident_permission import get_permissions_by_user
from src.models.resident import Resident
from src.models.user import User, Role
from src.schemas.resident import (
    ResidentCreate,
    ResidentResponse,
    ResidentUpdate,
)

router = APIRouter(prefix="/residents", tags=["Residents"])


@router.get(
    "",
    response_model=list[ResidentResponse],
    summary="List accessible residents",
)
def list_residents(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Resident]:
    """Retrieve residents accessible to the current user.

    Admins receive all residents; caregivers receive only assigned residents.
    """
    if current_user.role == Role.ADMIN:
        return get_all_residents(db, skip=skip, limit=limit)

    # For caregivers, retrieve only assigned residents
    permissions = get_permissions_by_user(db, current_user.id)
    resident_ids = [p.resident_id for p in permissions]

    if not resident_ids:
        return []

    # Filter residents assigned to caregiver
    return (
        db.query(Resident)
        .filter(Resident.id.in_(resident_ids))
        .offset(skip)
        .limit(limit)
        .all()
    )


@router.get(
    "/{resident_id}",
    response_model=ResidentResponse,
    summary="Get resident by ID",
)
def get_resident(
    resident_id: int,
    resident: Resident = Depends(verify_resident_access),
) -> Resident:
    """Retrieve details of a specific resident. Verified against user permissions."""
    return resident


@router.post(
    "",
    response_model=ResidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Admit/create a new resident (Admin only)",
)
def create_new_resident(
    resident_data: ResidentCreate,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(Role.ADMIN)),
) -> Resident:
    """Create a new resident record. Requires administrator role."""
    resident = create_resident(db, resident_data=resident_data)
    logger.info("New resident admitted with ID %s", resident.id)
    return resident


@router.patch(
    "/{resident_id}",
    response_model=ResidentResponse,
    summary="Update resident information",
)
def modify_resident(
    resident_id: int,
    resident_data: ResidentUpdate,
    db: Session = Depends(get_db),
    _verified: Resident = Depends(verify_resident_access),
) -> Resident:
    """Update details of an assigned resident."""
    updated = update_resident(
        db, resident_id=resident_id, resident_data=resident_data
    )
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resident with ID {resident_id} not found",
        )
    logger.info("Resident %s updated", resident_id)
    return updated


@router.delete(
    "/{resident_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a resident record (Admin only)",
)
def remove_resident(
    resident_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(Role.ADMIN)),
) -> None:
    """Permanently delete a resident record. Requires administrator role."""
    deleted = delete_resident(db, resident_id=resident_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resident with ID {resident_id} not found",
        )
    logger.info("Resident %s deleted by admin", resident_id)
