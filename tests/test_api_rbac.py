import unittest
from datetime import date

from tests.test_api_base import ApiTestCase
from src.crud.resident import create_resident
from src.schemas.resident import ResidentCreate


class TestApiRBAC(ApiTestCase):
    """Test suite for Role-Based Access Control (Admin vs Caregiver)."""

    def setUp(self):
        super().setUp()
        self.admin = self.create_test_user(
            name="Admin User",
            email="admin@eldercare.test",
            password="AdminPassword123!",
            role="admin",
        )
        self.caregiver1 = self.create_test_user(
            name="Caregiver One",
            email="cg1@eldercare.test",
            password="CaregiverPassword123!",
            role="caregiver",
        )
        self.caregiver2 = self.create_test_user(
            name="Caregiver Two",
            email="cg2@eldercare.test",
            password="CaregiverPassword123!",
            role="caregiver",
        )

        self.admin_headers = self.get_auth_headers(self.admin)
        self.cg1_headers = self.get_auth_headers(self.caregiver1)
        self.cg2_headers = self.get_auth_headers(self.caregiver2)

    def test_list_users_admin_allowed(self):
        """Admin can list all users."""
        response = self.client.get("/api/v1/users", headers=self.admin_headers)
        self.assertEqual(response.status_code, 200)
        users = response.json()
        self.assertGreaterEqual(len(users), 3)

    def test_list_users_caregiver_forbidden(self):
        """Caregiver cannot list all users (HTTP 403)."""
        response = self.client.get("/api/v1/users", headers=self.cg1_headers)
        self.assertEqual(response.status_code, 403)
        self.assertIn("Operation not permitted for your role", response.json()["detail"])

    def test_create_user_admin_allowed(self):
        """Admin can create a new user account."""
        payload = {
            "name": "New Staff",
            "email": "new.staff@eldercare.test",
            "password": "Password123!",
            "role": "caregiver",
        }
        response = self.client.post("/api/v1/users", json=payload, headers=self.admin_headers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["email"], "new.staff@eldercare.test")

    def test_create_user_caregiver_forbidden(self):
        """Caregiver cannot create a new user (HTTP 403)."""
        payload = {
            "name": "New Staff",
            "email": "new.staff2@eldercare.test",
            "password": "Password123!",
            "role": "caregiver",
        }
        response = self.client.post("/api/v1/users", json=payload, headers=self.cg1_headers)
        self.assertEqual(response.status_code, 403)

    def test_get_user_self_allowed_for_caregiver(self):
        """Caregiver can view their own profile."""
        response = self.client.get(
            f"/api/v1/users/{self.caregiver1.id}", headers=self.cg1_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], self.caregiver1.id)

    def test_get_user_other_forbidden_for_caregiver(self):
        """Caregiver cannot view another user's profile (HTTP 403)."""
        response = self.client.get(
            f"/api/v1/users/{self.caregiver2.id}", headers=self.cg1_headers
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("not authorized to view another user's profile", response.json()["detail"])

    def test_get_user_other_allowed_for_admin(self):
        """Admin can view any user's profile."""
        response = self.client.get(
            f"/api/v1/users/{self.caregiver1.id}", headers=self.admin_headers
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], self.caregiver1.id)

    def test_caregiver_cannot_change_own_role(self):
        """Caregiver cannot escalate privilege by updating their own role."""
        payload = {"role": "admin"}
        response = self.client.patch(
            f"/api/v1/users/{self.caregiver1.id}", json=payload, headers=self.cg1_headers
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("cannot change your own role", response.json()["detail"])

    def test_caregiver_cannot_delete_user(self):
        """Caregiver cannot delete user accounts (HTTP 403)."""
        response = self.client.delete(
            f"/api/v1/users/{self.caregiver2.id}", headers=self.cg1_headers
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_can_delete_user(self):
        """Admin can soft delete a user account."""
        user_to_delete = self.create_test_user(email="delete_me@eldercare.test")
        response = self.client.delete(
            f"/api/v1/users/{user_to_delete.id}", headers=self.admin_headers
        )
        self.assertEqual(response.status_code, 204)

    def test_resident_creation_rbac(self):
        """Only Admin can create residents."""
        payload = {
            "name": "Jane Resident",
            "date_of_birth": "1940-05-15",
            "room_number": "101A",
        }
        # Caregiver fails
        cg_res = self.client.post("/api/v1/residents", json=payload, headers=self.cg1_headers)
        self.assertEqual(cg_res.status_code, 403)

        # Admin succeeds
        admin_res = self.client.post("/api/v1/residents", json=payload, headers=self.admin_headers)
        self.assertEqual(admin_res.status_code, 201)
        self.assertEqual(admin_res.json()["name"], "Jane Resident")

    def test_resident_deletion_rbac(self):
        """Only Admin can delete residents."""
        resident = create_resident(
            self.db,
            ResidentCreate(
                name="Temp Resident",
                date_of_birth=date(1935, 1, 1),
                room_number="999",
            ),
        )
        # Caregiver fails
        cg_res = self.client.delete(
            f"/api/v1/residents/{resident.id}", headers=self.cg1_headers
        )
        self.assertEqual(cg_res.status_code, 403)

        # Admin succeeds
        admin_res = self.client.delete(
            f"/api/v1/residents/{resident.id}", headers=self.admin_headers
        )
        self.assertEqual(admin_res.status_code, 204)

    def test_permission_management_rbac(self):
        """Only Admin can manage user-resident permissions."""
        resident = create_resident(
            self.db,
            ResidentCreate(
                name="Perm Resident",
                date_of_birth=date(1938, 2, 2),
                room_number="202B",
            ),
        )
        payload = {
            "user_id": self.caregiver1.id,
            "resident_id": resident.id,
        }
        # Caregiver fails to assign
        cg_res = self.client.post("/api/v1/permissions", json=payload, headers=self.cg1_headers)
        self.assertEqual(cg_res.status_code, 403)

        # Caregiver fails to list all permissions
        cg_list = self.client.get("/api/v1/permissions", headers=self.cg1_headers)
        self.assertEqual(cg_list.status_code, 403)

        # Admin succeeds to assign
        admin_res = self.client.post("/api/v1/permissions", json=payload, headers=self.admin_headers)
        self.assertEqual(admin_res.status_code, 201)

        # Admin can list all permissions
        admin_list = self.client.get("/api/v1/permissions", headers=self.admin_headers)
        self.assertEqual(admin_list.status_code, 200)
        self.assertEqual(len(admin_list.json()), 1)

        # Caregiver can view their own permissions
        cg_own = self.client.get(
            f"/api/v1/permissions/user/{self.caregiver1.id}", headers=self.cg1_headers
        )
        self.assertEqual(cg_own.status_code, 200)
        self.assertEqual(len(cg_own.json()), 1)

        # Caregiver cannot view other user's permissions
        cg_other = self.client.get(
            f"/api/v1/permissions/user/{self.caregiver2.id}", headers=self.cg1_headers
        )
        self.assertEqual(cg_other.status_code, 403)

        # Admin can revoke permission
        admin_del = self.client.delete(
            f"/api/v1/permissions/{self.caregiver1.id}/{resident.id}",
            headers=self.admin_headers,
        )
        self.assertEqual(admin_del.status_code, 204)


if __name__ == "__main__":
    unittest.main()
