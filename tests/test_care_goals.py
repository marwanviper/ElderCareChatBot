from src.crud.care_goal import (
    create_care_goal,
    delete_care_goal,
    get_all_care_goals,
    get_care_goal_by_id,
    get_care_goals_by_resident,
    update_care_goal,
)
from src.crud.resident import create_resident
from src.schemas.care_goal import (
    CareGoalCreate,
    CareGoalResponse,
    CareGoalUpdate,
)
from src.schemas.resident import ResidentCreate
from tests.test_base import BaseTestCase


class TestCareGoalCRUD(BaseTestCase):
    """Test suite for CareGoal model and CRUD operations."""

    def setUp(self):
        super().setUp()
        self.resident = create_resident(
            self.db, ResidentCreate(name="Giovanni Bianchi", room_number="106")
        )

    def test_create_and_get_care_goal(self):
        goal_in = CareGoalCreate(
            resident_id=self.resident.id,
            goal="Improve balance by participating in daily gentle yoga.",
            status="active",
        )
        goal = create_care_goal(self.db, goal_in)
        self.assertIsNotNone(goal.id)
        self.assertEqual(goal.resident_id, self.resident.id)
        self.assertEqual(goal.status, "active")

        fetched = get_care_goal_by_id(self.db, goal.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.goal, goal_in.goal)

    def test_care_goal_response_serialization(self):
        goal = create_care_goal(
            self.db,
            CareGoalCreate(
                resident_id=self.resident.id,
                goal="Drink 1.5L of water daily.",
            ),
        )
        resp = CareGoalResponse.model_validate(goal)
        self.assertEqual(resp.id, goal.id)
        self.assertEqual(resp.status, "active")
        self.assertEqual(resp.goal, "Drink 1.5L of water daily.")

    def test_get_care_goals_by_resident_and_status(self):
        create_care_goal(
            self.db,
            CareGoalCreate(
                resident_id=self.resident.id, goal="Goal 1", status="active"
            ),
        )
        create_care_goal(
            self.db,
            CareGoalCreate(
                resident_id=self.resident.id, goal="Goal 2", status="achieved"
            ),
        )

        all_goals = get_care_goals_by_resident(self.db, self.resident.id)
        self.assertEqual(len(all_goals), 2)

        active_goals = get_care_goals_by_resident(
            self.db, self.resident.id, status="active"
        )
        self.assertEqual(len(active_goals), 1)
        self.assertEqual(active_goals[0].goal, "Goal 1")

    def test_update_and_delete_care_goal(self):
        goal = create_care_goal(
            self.db,
            CareGoalCreate(
                resident_id=self.resident.id,
                goal="Walk 100m daily",
                status="active",
            ),
        )
        # Update
        updated = update_care_goal(
            self.db, goal.id, CareGoalUpdate(status="achieved")
        )
        self.assertEqual(updated.status, "achieved")

        # Delete
        deleted = delete_care_goal(self.db, goal.id)
        self.assertTrue(deleted)
        self.assertIsNone(get_care_goal_by_id(self.db, goal.id))
