from src.crud.care_report import (
    create_care_report,
    delete_care_report,
    get_all_care_reports,
    get_care_report_by_id,
    get_care_reports_by_resident,
    update_care_report,
)
from src.crud.resident import create_resident
from src.crud.user import create_user
from src.schemas.care_report import (
    CareReportCreate,
    CareReportResponse,
    CareReportUpdate,
)
from src.schemas.resident import ResidentCreate
from src.schemas.user import UserCreate
from tests.test_base import BaseTestCase


class TestCareReportCRUD(BaseTestCase):
    """Test suite for CareReport model and CRUD operations."""

    def setUp(self):
        super().setUp()
        self.user = create_user(
            self.db,
            UserCreate(
                name="Nurse Jack",
                email="jack@eldercare.test",
                password="password123",
            ),
        )
        self.resident = create_resident(
            self.db, ResidentCreate(name="Elena Fischer", room_number="105")
        )

    def test_create_and_get_care_report(self):
        report_in = CareReportCreate(
            resident_id=self.resident.id,
            created_by=self.user.id,
            content="Resident showed high engagement in morning activities.",
        )
        report = create_care_report(self.db, report_in)
        self.assertIsNotNone(report.id)
        self.assertEqual(report.resident_id, self.resident.id)
        self.assertEqual(report.created_by, self.user.id)
        self.assertIsNotNone(report.report_date)

        fetched = get_care_report_by_id(self.db, report.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.content, report_in.content)

    def test_care_report_response_serialization(self):
        report_in = CareReportCreate(
            resident_id=self.resident.id,
            created_by=self.user.id,
            content="Blood pressure measured: 120/80 mmHg.",
        )
        report = create_care_report(self.db, report_in)
        resp = CareReportResponse.model_validate(report)
        self.assertEqual(resp.id, report.id)
        self.assertEqual(resp.resident_id, self.resident.id)
        self.assertEqual(resp.created_by, self.user.id)

    def test_get_care_reports_by_resident(self):
        create_care_report(
            self.db,
            CareReportCreate(
                resident_id=self.resident.id,
                created_by=self.user.id,
                content="Report 1",
            ),
        )
        create_care_report(
            self.db,
            CareReportCreate(
                resident_id=self.resident.id,
                created_by=self.user.id,
                content="Report 2",
            ),
        )
        reports = get_care_reports_by_resident(self.db, self.resident.id)
        self.assertEqual(len(reports), 2)

    def test_update_and_delete_care_report(self):
        report = create_care_report(
            self.db,
            CareReportCreate(
                resident_id=self.resident.id,
                created_by=self.user.id,
                content="Initial report content",
            ),
        )
        # Update
        updated = update_care_report(
            self.db, report.id, CareReportUpdate(content="Corrected report content")
        )
        self.assertEqual(updated.content, "Corrected report content")

        # Delete
        deleted = delete_care_report(self.db, report.id)
        self.assertTrue(deleted)
        self.assertIsNone(get_care_report_by_id(self.db, report.id))
