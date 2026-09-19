from pydantic import ValidationError

from src.crud.user import (
    create_user,
    delete_user_hard,
    delete_user_soft,
    get_user_by_email,
    get_user_by_id,
    get_users,
    update_user,
)
from src.schemas.user import UserCreate, UserResponse, UserUpdate
from tests.test_base import BaseTestCase


class TestUserCRUD(BaseTestCase):
    """Test suite for User model, validation, and CRUD operations."""

    def test_create_user_success(self):
        user_in = UserCreate(
            name="Ahmed Hassan",
            email="ahmed@eldercare.test",
            password="StrongPassword123!",
            role="caregiver",
        )
        user = create_user(self.db, user_in)
        self.assertIsNotNone(user.id)
        self.assertEqual(user.name, "Ahmed Hassan")
        self.assertEqual(user.email, "ahmed@eldercare.test")
        self.assertEqual(user.role, "caregiver")
        self.assertIsNone(user.deleted_date)

    def test_create_user_with_prehashed_password(self):
        user_in = UserCreate(
            name="Sara Ali",
            email="sara@eldercare.test",
            password="plain_password",
            role="caregiver",
        )
        user = create_user(
            self.db, user_in, password_hash="$2b$12$precomputedhashvalue"
        )
        self.assertEqual(user.password_hash, "$2b$12$precomputedhashvalue")

    def test_invalid_email_validation(self):
        with self.assertRaises(ValidationError):
            UserCreate(
                name="Invalid Email",
                email="not-an-email-format",
                password="validpassword123",
                role="caregiver",
            )

    def test_short_password_validation(self):
        with self.assertRaises(ValidationError):
            UserCreate(
                name="Short Pass",
                email="short@eldercare.test",
                password="123",  # min_length is 6
                role="caregiver",
            )

    def test_user_response_serialization_excludes_secrets(self):
        user_in = UserCreate(
            name="Admin User",
            email="admin@eldercare.test",
            password="SuperSecretPassword!",
            role="admin",
        )
        user = create_user(self.db, user_in)
        resp = UserResponse.model_validate(user)
        self.assertEqual(resp.id, user.id)
        self.assertEqual(resp.email, "admin@eldercare.test")
        self.assertEqual(resp.role, "admin")
        self.assertFalse(hasattr(resp, "password_hash"))
        self.assertNotIn("password_hash", resp.model_dump())

    def test_get_user_by_id_and_email(self):
        user_in = UserCreate(
            name="Omar Khaled",
            email="omar@eldercare.test",
            password="Password123!",
            role="caregiver",
        )
        created = create_user(self.db, user_in)

        by_id = get_user_by_id(self.db, created.id)
        self.assertIsNotNone(by_id)
        self.assertEqual(by_id.email, "omar@eldercare.test")

        by_email = get_user_by_email(self.db, "omar@eldercare.test")
        self.assertIsNotNone(by_email)
        self.assertEqual(by_email.id, created.id)

    def test_update_user_partial(self):
        user_in = UserCreate(
            name="Mona Ibrahim",
            email="mona@eldercare.test",
            password="Password123!",
            role="caregiver",
        )
        created = create_user(self.db, user_in)

        update_in = UserUpdate(name="Mona K. Ibrahim", role="admin")
        updated = update_user(self.db, created.id, update_in)
        self.assertEqual(updated.name, "Mona K. Ibrahim")
        self.assertEqual(updated.role, "admin")
        self.assertEqual(updated.email, "mona@eldercare.test")

    def test_get_users_pagination(self):
        for i in range(5):
            create_user(
                self.db,
                UserCreate(
                    name=f"User {i}",
                    email=f"user{i}@eldercare.test",
                    password="Password123!",
                ),
            )
        users = get_users(self.db, skip=1, limit=3)
        self.assertEqual(len(users), 3)

    def test_soft_and_hard_delete_user(self):
        user_in = UserCreate(
            name="To Delete",
            email="delete@eldercare.test",
            password="Password123!",
        )
        user = create_user(self.db, user_in)

        # Soft delete
        soft = delete_user_soft(self.db, user.id)
        self.assertIsNotNone(soft.deleted_date)
        self.assertIsNone(get_user_by_id(self.db, user.id, include_deleted=False))
        self.assertIsNotNone(get_user_by_id(self.db, user.id, include_deleted=True))

        # Hard delete
        deleted = delete_user_hard(self.db, user.id)
        self.assertTrue(deleted)
        self.assertIsNone(get_user_by_id(self.db, user.id, include_deleted=True))
