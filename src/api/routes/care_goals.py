from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.api.deps import (
    get_current_user,
    get_db,
    require_role,
    verify_resident_access,
)
from src.core.logging import logger
from src.crud.care_goal import (
    create_care_goal,
    delete_care_goal,
    get_care_goal_by_id,
    get_care_goals_by_resident,
    update_care_goal,
)
from src.models.care_goal import CareGoal
from src.models.user import User,Role
from src.schemas.care_goal import (
    CareGoalCreate,
    CareGoalResponse,
    CareGoalUpdate,
)

router = APIRouter(prefix="/care-goals", tags=["Care Goals"])


@router.post(
    "",
    response_model=CareGoalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new care goal",
)
def create_goal(
    goal_data: CareGoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CareGoal:
    """Create a new care goal for a resident. Access to the resident is required."""
    verify_resident_access(
        resident_id=goal_data.resident_id, current_user=current_user, db=db
    )
    goal = create_care_goal(db, goal_data=goal_data)
    logger.info("Care goal %s created for resident %s", goal.id, goal.resident_id)
    return goal


@router.get(
    "/resident/{resident_id}",
    response_model=list[CareGoalResponse],
    summary="List care goals for a specific resident",
)
def list_goals_for_resident(
    resident_id: int,
    status_filter: str | None = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[CareGoal]:
    """Retrieve care goals for a resident, optionally filtered by status ('active', 'achieved', etc.)."""
    verify_resident_access(
        resident_id=resident_id, current_user=current_user, db=db
    )
    return get_care_goals_by_resident(
        db,
        resident_id=resident_id,
        status=status_filter,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{goal_id}",
    response_model=CareGoalResponse,
    summary="Get care goal by ID",
)
def get_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CareGoal:
    """Retrieve details of a specific care goal."""
    goal = get_care_goal_by_id(db, goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Care goal with ID {goal_id} not found",
        )
    verify_resident_access(
        resident_id=goal.resident_id, current_user=current_user, db=db
    )
    return goal


@router.patch(
    "/{goal_id}",
    response_model=CareGoalResponse,
    summary="Update a care goal",
)
def modify_goal(
    goal_id: int,
    goal_data: CareGoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CareGoal:
    """Update goal description or transition status."""
    goal = get_care_goal_by_id(db, goal_id)
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Care goal with ID {goal_id} not found",
        )
    verify_resident_access(
        resident_id=goal.resident_id, current_user=current_user, db=db
    )
    updated = update_care_goal(db, goal_id=goal_id, goal_data=goal_data)
    logger.info("Care goal %s updated", goal_id)
    return updated


@router.delete(
    "/{goal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a care goal (Admin only)",
)
def remove_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(Role.ADMIN)),
) -> None:
    """Delete a care goal. Requires administrator role."""
    deleted = delete_care_goal(db, goal_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Care goal with ID {goal_id} not found",
        )
    logger.info("Care goal %s deleted by admin", goal_id)
