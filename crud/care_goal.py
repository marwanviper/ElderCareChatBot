from src.database import get_db
from src.models import CareGoal
from utils.utils import _utcnow
from sqlalchemy.orm import Session


def create_care_goal(db: Session, care_goal: CareGoal):
    """Create a new care goal in the database.
    Args:
        db (Session): The database session.
        care_goal (CareGoal): The care goal object to be created.
    Returns:
        CareGoal: The created care goal object.
    """
    db.add(care_goal)
    db.commit()
    db.refresh(care_goal)
    return care_goal


def get_care_goal_by_id(db: Session, care_goal_id: int):
    """Retrieve a care goal by its ID from the database.
    Args:
        db (Session): The database session.
        care_goal_id (int): The ID of the care goal to retrieve.
    Returns:
        CareGoal | None: The retrieved care goal object, or None if not found.
    """
    return db.query(CareGoal).filter(CareGoal.id == care_goal_id).first()


def get_all_care_goals(db: Session):
    """Retrieve all care goals from the database.
    Args:
        db (Session): The database session.
    Returns:
        list[CareGoal]: A list of all care goal objects.
    """
    return db.query(CareGoal).all()


def delete_care_goal(db: Session, care_goal_id: int):
    """Delete a care goal by its ID from the database.
    Args:
        db (Session): The database session.
        care_goal_id (int): The ID of the care goal to delete.
    Returns:
        bool: True if the care goal was deleted, False if not found.
    """
    care_goal = db.query(CareGoal).filter(CareGoal.id == care_goal_id).first()
    if care_goal:
        db.delete(care_goal)
        db.commit()
        return True
    return False


def update_care_goal(db: Session, care_goal_id: int, updated_data: dict):
    """Update a care goal by its ID in the database.
    Args:
        db (Session): The database session.
        care_goal_id (int): The ID of the care goal to update.
        updated_data (dict): A dictionary containing the updated data for the care goal.
    Returns:
        CareGoal | None: The updated care goal object, or None if not found.
    """
    care_goal = db.query(CareGoal).filter(CareGoal.id == care_goal_id).first()
    if care_goal:
        for key, value in updated_data.items():
            setattr(care_goal, key, value)
        db.commit()
        db.refresh(care_goal)
        return care_goal
    return None
