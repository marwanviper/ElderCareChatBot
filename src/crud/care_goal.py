from sqlalchemy.orm import Session

from src.models.care_goal import CareGoal
from src.schemas.care_goal import CareGoalCreate, CareGoalUpdate
from utils.utils import _utcnow


def create_care_goal(db: Session, goal_data: CareGoalCreate) -> CareGoal:
    """Create a new care goal in the database.

    Args:
        db: The database session.
        goal_data: Pydantic schema containing care goal details.

    Returns:
        The created CareGoal object.
    """
    new_goal = CareGoal(
        resident_id=goal_data.resident_id,
        goal=goal_data.goal,
        status=goal_data.status,
        created_at=_utcnow(),
    )
    db.add(new_goal)
    db.commit()
    db.refresh(new_goal)
    return new_goal


def get_care_goal_by_id(db: Session, goal_id: int) -> CareGoal | None:
    """Retrieve a care goal by its ID from the database.

    Args:
        db: The database session.
        goal_id: The ID of the care goal to retrieve.

    Returns:
        The retrieved CareGoal object, or None if not found.
    """
    return db.query(CareGoal).filter(CareGoal.id == goal_id).first()


def get_care_goals_by_resident(
    db: Session,
    resident_id: int,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[CareGoal]:
    """Retrieve care goals for a specific resident, optionally filtered by status.

    Args:
        db: The database session.
        resident_id: The ID of the resident.
        status: Optional status filter (e.g., 'active', 'achieved').
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        A list of CareGoal objects.
    """
    query = db.query(CareGoal).filter(CareGoal.resident_id == resident_id)
    if status is not None:
        query = query.filter(CareGoal.status == status)
    return query.offset(skip).limit(limit).all()


def get_all_care_goals(
    db: Session, skip: int = 0, limit: int = 100
) -> list[CareGoal]:
    """Retrieve all care goals from the database.

    Args:
        db: The database session.
        skip: Number of records to skip.
        limit: Maximum number of records to return.

    Returns:
        A list of all CareGoal objects.
    """
    return db.query(CareGoal).offset(skip).limit(limit).all()


def update_care_goal(
    db: Session, goal_id: int, goal_data: CareGoalUpdate
) -> CareGoal | None:
    """Update a care goal by its ID in the database.

    Args:
        db: The database session.
        goal_id: The ID of the care goal to update.
        goal_data: Pydantic schema containing the updated fields.

    Returns:
        The updated CareGoal object, or None if not found.
    """
    goal = db.query(CareGoal).filter(CareGoal.id == goal_id).first()
    if not goal:
        return None

    update_dict = goal_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(goal, key, value)

    db.commit()
    db.refresh(goal)
    return goal


def delete_care_goal(db: Session, goal_id: int) -> bool:
    """Delete a care goal by its ID from the database.

    Args:
        db: The database session.
        goal_id: The ID of the care goal to delete.

    Returns:
        True if the care goal was deleted, False if not found.
    """
    goal = db.query(CareGoal).filter(CareGoal.id == goal_id).first()
    if goal:
        db.delete(goal)
        db.commit()
        return True
    return False
