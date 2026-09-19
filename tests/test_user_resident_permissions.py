from src.crud.resident import create_resident
from src.crud.user import create_user
from src.crud.user_resident_permission import (
    create_user_resident_permission,
    delete_user_resident_permission,
    get_all_user_resident_permissions,
    get_permissions_by_resident,
    get_permissions_by_user,
    get_user_resident_permission,
)
from src.schemas.resident import ResidentCreate
from src.schemas.user import UserCreate
from src.schemas.user_resident_permission import (
    UserResidentPermissionCreate,
    UserResidentPermissionResponse,
)
from tests.test_base import BaseTestCase


class TestUserResidentPermissionCRUD(BaseTestCase):
    """Test suite for UserResidentPermission composite primary key and CRUD operations."""

    def setUp(self):
        super().setUp()
        self.user1 = create_user(
            self.db,
            UserCreate(
                name="Caregiver One",
                email="cg1@eldercare.test",
                password="password123",
            ),
        )
        self.user2 = create_user(
            self.db,
            UserCreate(
                name="Caregiver Two",
                email="cg2@eldercare.test",
                password="password123",
            ),
        )
        self.resident1 = create_resident(
            self.db, ResidentCreate(name="Resident A", room_number="201")
        )
        self.resident2 = create_resident(
            self.db, ResidentCreate(name="Resident B", room_number="202")
        )

    def test_create_and_get_permission(self):
        perm_in = UserResidentPermissionCreate(
            user_id=self.user1.id, resident_id=self.resident1.id
        )
        perm = create_user_resident_permission(self.db, perm_in)
        self.assertEqual(perm.user_id, self.user1.id)
        self.assertEqual(perm.resident_id, self.resident1.id)

        # Lookup by composite key
        fetched = get_user_resident_permission(
            self.db, self.user1.id, self.resident1.id
        )
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.user_id, self.user1.id)
        self.assertEqual(fetched.resident_id, self.resident1.id)

    def test_permission_response_serialization(self):
        perm_in = UserResidentPermissionCreate(
            user_id=self.user1.id, resident_id=self.resident1.id
        )
        perm = create_user_resident_permission(self.db, perm_in)
        resp = UserResidentPermissionResponse.model_validate(perm)
        self.assertEqual(resp.user_id, self.user1.id)
        self.assertEqual(resp.resident_id, self.resident1.id)

    def test_get_permissions_by_user_and_resident(self):
        create_user_resident_permission(
            self.db,
            UserResidentPermissionCreate(
                user_id=self.user1.id, resident_id=self.resident1.id
            ),
        )
        create_user_resident_permission(
            self.db,
            UserResidentPermissionCreate(
                user_id=self.user1.id, resident_id=self.resident2.id
            ),
        )
        create_user_resident_permission(
            self.db,
            UserResidentPermissionCreate(
                user_id=self.user2.id, resident_id=self.resident1.id
            ),
        )

        # Check by user
        user1_perms = get_permissions_by_user(self.db, self.user1.id)
        self.assertEqual(len(user1_perms), 2)

        # Check by resident
        res1_perms = get_permissions_by_resident(self.db, self.resident1.id)
        self.assertEqual(len(res1_perms), 2)

        # Check all
        all_perms = get_all_user_resident_permissions(self.db)
        self.assertEqual(len(all_perms), 3)

    def test_delete_permission(self):
        create_user_resident_permission(
            self.db,
            UserResidentPermissionCreate(
                user_id=self.user1.id, resident_id=self.resident1.id
            ),
        )
        deleted = delete_user_resident_permission(
            self.db, self.user1.id, self.resident1.id
        )
        self.assertTrue(deleted)
        self.assertIsNone(
            get_user_resident_permission(
                self.db, self.user1.id, self.resident1.id
            )
        )
