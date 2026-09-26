import unittest
from datetime import date

from tests.test_api_base import ApiTestCase
from src.crud.resident import create_resident
from src.crud.user_resident_permission import create_user_resident_permission
from src.schemas.resident import ResidentCreate
from src.schemas.user_resident_permission import UserResidentPermissionCreate


class TestApiResources(ApiTestCase):
    """Test suite for resource-level authorization (Caregiver access to assigned vs unassigned residents)."""

    def setUp(self):
        super().setUp()
        # Create users
        self.admin = self.create_test_user(
            name="Admin Staff",
            email="admin.res@eldercare.test",
            role="admin",
        )
        self.cg1 = self.create_test_user(
            name="Caregiver Alpha",
            email="cg.alpha@eldercare.test",
            role="caregiver",
        )
        self.cg2 = self.create_test_user(
            name="Caregiver Beta",
            email="cg.beta@eldercare.test",
            role="caregiver",
        )

        self.admin_headers = self.get_auth_headers(self.admin)
        self.cg1_headers = self.get_auth_headers(self.cg1)
        self.cg2_headers = self.get_auth_headers(self.cg2)

        # Create residents
        self.res1 = create_resident(
            self.db,
            ResidentCreate(
                name="Resident Alpha",
                date_of_birth=date(1942, 3, 10),
                room_number="101",
            ),
        )
        self.res2 = create_resident(
            self.db,
            ResidentCreate(
                name="Resident Beta",
                date_of_birth=date(1938, 7, 22),
                room_number="102",
            ),
        )
        self.res3 = create_resident(
            self.db,
            ResidentCreate(
                name="Resident Gamma",
                date_of_birth=date(1945, 11, 5),
                room_number="103",
            ),
        )

        # Assign res1 to cg1, res2 to cg2 (res3 unassigned)
        create_user_resident_permission(
            self.db,
            UserResidentPermissionCreate(
                user_id=self.cg1.id, resident_id=self.res1.id
            ),
        )
        create_user_resident_permission(
            self.db,
            UserResidentPermissionCreate(
                user_id=self.cg2.id, resident_id=self.res2.id
            ),
        )

    def test_list_residents_scoping(self):
        """Admin sees all residents, caregivers see only assigned residents."""
        # Admin gets all 3
        admin_res = self.client.get("/api/v1/residents", headers=self.admin_headers)
        self.assertEqual(admin_res.status_code, 200)
        self.assertEqual(len(admin_res.json()), 3)

        # CG1 gets only res1
        cg1_res = self.client.get("/api/v1/residents", headers=self.cg1_headers)
        self.assertEqual(cg1_res.status_code, 200)
        cg1_list = cg1_res.json()
        self.assertEqual(len(cg1_list), 1)
        self.assertEqual(cg1_list[0]["id"], self.res1.id)

        # CG2 gets only res2
        cg2_res = self.client.get("/api/v1/residents", headers=self.cg2_headers)
        self.assertEqual(cg2_res.status_code, 200)
        cg2_list = cg2_res.json()
        self.assertEqual(len(cg2_list), 1)
        self.assertEqual(cg2_list[0]["id"], self.res2.id)

    def test_get_resident_by_id_access(self):
        """Caregiver can view assigned resident, denied for unassigned."""
        # CG1 views assigned res1 -> OK
        res = self.client.get(f"/api/v1/residents/{self.res1.id}", headers=self.cg1_headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["name"], "Resident Alpha")

        # CG1 views unassigned res2 -> 403 Forbidden
        res = self.client.get(f"/api/v1/residents/{self.res2.id}", headers=self.cg1_headers)
        self.assertEqual(res.status_code, 403)
        self.assertIn("not authorized to access this resident", res.json()["detail"])

        # Non-existent resident -> 404
        res = self.client.get("/api/v1/residents/9999", headers=self.cg1_headers)
        self.assertEqual(res.status_code, 404)

        # Admin views any resident -> OK
        res = self.client.get(f"/api/v1/residents/{self.res2.id}", headers=self.admin_headers)
        self.assertEqual(res.status_code, 200)

    def test_care_reports_resource_access(self):
        """Caregiver can create/view/update reports only for assigned residents."""
        # CG1 creates report for assigned res1 -> OK
        report_payload = {
            "resident_id": self.res1.id,
            "content": "Resident had breakfast and completed morning exercises.",
        }
        create_res = self.client.post(
            "/api/v1/care-reports", json=report_payload, headers=self.cg1_headers
        )
        self.assertEqual(create_res.status_code, 201)
        report_id = create_res.json()["id"]
        self.assertEqual(create_res.json()["created_by"], self.cg1.id)

        # CG1 attempts to create report for unassigned res2 -> 403 Forbidden
        bad_payload = {
            "resident_id": self.res2.id,
            "content": "Attempting unauthorized note.",
        }
        bad_res = self.client.post(
            "/api/v1/care-reports", json=bad_payload, headers=self.cg1_headers
        )
        self.assertEqual(bad_res.status_code, 403)

        # CG1 gets reports for res1 -> OK
        list_res = self.client.get(
            f"/api/v1/care-reports/resident/{self.res1.id}", headers=self.cg1_headers
        )
        self.assertEqual(list_res.status_code, 200)
        self.assertEqual(len(list_res.json()), 1)

        # CG2 tries to get reports for res1 -> 403 Forbidden
        cg2_list = self.client.get(
            f"/api/v1/care-reports/resident/{self.res1.id}", headers=self.cg2_headers
        )
        self.assertEqual(cg2_list.status_code, 403)

        # CG1 updates their own report -> OK
        patch_res = self.client.patch(
            f"/api/v1/care-reports/{report_id}",
            json={"content": "Updated: Resident completed morning walk."},
            headers=self.cg1_headers,
        )
        self.assertEqual(patch_res.status_code, 200)
        self.assertEqual(patch_res.json()["content"], "Updated: Resident completed morning walk.")

        # CG1 deletes their own report -> OK
        del_res = self.client.delete(
            f"/api/v1/care-reports/{report_id}", headers=self.cg1_headers
        )
        self.assertEqual(del_res.status_code, 204)

    def test_care_goals_resource_access(self):
        """Caregiver can manage goals for assigned residents."""
        # CG1 creates goal for res1 -> OK
        goal_payload = {
            "resident_id": self.res1.id,
            "goal": "Walk 50 meters independently daily",
            "status": "active",
        }
        res = self.client.post(
            "/api/v1/care-goals", json=goal_payload, headers=self.cg1_headers
        )
        self.assertEqual(res.status_code, 201)
        goal_id = res.json()["id"]

        # CG1 attempts to create goal for res2 -> 403 Forbidden
        res = self.client.post(
            "/api/v1/care-goals",
            json={"resident_id": self.res2.id, "goal": "Unauthorized goal"},
            headers=self.cg1_headers,
        )
        self.assertEqual(res.status_code, 403)

        # CG1 gets goals for res1 with status filter -> OK
        res = self.client.get(
            f"/api/v1/care-goals/resident/{self.res1.id}?status=active",
            headers=self.cg1_headers,
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 1)

        # CG1 modifies goal status -> OK
        res = self.client.patch(
            f"/api/v1/care-goals/{goal_id}",
            json={"status": "achieved"},
            headers=self.cg1_headers,
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "achieved")

    def test_incidents_resource_access(self):
        """Caregiver can report and view incidents for assigned residents."""
        # CG1 reports incident for res1 -> OK
        incident_payload = {
            "resident_id": self.res1.id,
            "type": "Fall",
            "description": "Resident slipped near bathroom, no fractures detected.",
        }
        res = self.client.post(
            "/api/v1/incidents", json=incident_payload, headers=self.cg1_headers
        )
        self.assertEqual(res.status_code, 201)
        incident_id = res.json()["id"]

        # CG1 attempts incident for res2 -> 403 Forbidden
        res = self.client.post(
            "/api/v1/incidents",
            json={"resident_id": self.res2.id, "type": "Fall", "description": "Forbidden"},
            headers=self.cg1_headers,
        )
        self.assertEqual(res.status_code, 403)

        # CG1 views incident list for res1 -> OK
        res = self.client.get(
            f"/api/v1/incidents/resident/{self.res1.id}", headers=self.cg1_headers
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 1)

        # CG1 updates incident notes -> OK
        res = self.client.patch(
            f"/api/v1/incidents/{incident_id}",
            json={"description": "Follow-up: Resident checked by physician, vital signs stable."},
            headers=self.cg1_headers,
        )
        self.assertEqual(res.status_code, 200)
        self.assertIn("vital signs stable", res.json()["description"])


if __name__ == "__main__":
    unittest.main()
