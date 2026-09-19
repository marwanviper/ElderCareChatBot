from src.crud.incident import (
    create_incident,
    delete_incident,
    get_all_incidents,
    get_incident_by_id,
    get_incidents_by_resident,
    update_incident,
)
from src.crud.resident import create_resident
from src.schemas.incident import (
    IncidentCreate,
    IncidentResponse,
    IncidentUpdate,
)
from src.schemas.resident import ResidentCreate
from tests.test_base import BaseTestCase


class TestIncidentCRUD(BaseTestCase):
    """Test suite for Incident model and CRUD operations."""

    def setUp(self):
        super().setUp()
        self.resident = create_resident(
            self.db, ResidentCreate(name="Clara Oswald", room_number="107")
        )

    def test_create_and_get_incident(self):
        inc_in = IncidentCreate(
            resident_id=self.resident.id,
            type="Fall",
            description="Resident slipped while getting out of bed. No visible injuries.",
        )
        incident = create_incident(self.db, inc_in)
        self.assertIsNotNone(incident.id)
        self.assertEqual(incident.type, "Fall")
        self.assertEqual(incident.resident_id, self.resident.id)

        fetched = get_incident_by_id(self.db, incident.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.description, inc_in.description)

    def test_incident_response_serialization(self):
        incident = create_incident(
            self.db,
            IncidentCreate(
                resident_id=self.resident.id,
                type="Medication",
                description="Late administration of morning insulin by 30 mins.",
            ),
        )
        resp = IncidentResponse.model_validate(incident)
        self.assertEqual(resp.id, incident.id)
        self.assertEqual(resp.type, "Medication")

    def test_get_incidents_by_resident(self):
        create_incident(
            self.db,
            IncidentCreate(
                resident_id=self.resident.id,
                type="Fall",
                description="Incident 1",
            ),
        )
        create_incident(
            self.db,
            IncidentCreate(
                resident_id=self.resident.id,
                type="Behavioral",
                description="Incident 2",
            ),
        )
        incidents = get_incidents_by_resident(self.db, self.resident.id)
        self.assertEqual(len(incidents), 2)

    def test_update_and_delete_incident(self):
        incident = create_incident(
            self.db,
            IncidentCreate(
                resident_id=self.resident.id,
                type="Minor Cut",
                description="Cut on left finger during crafts activity.",
            ),
        )
        # Update
        updated = update_incident(
            self.db,
            incident.id,
            IncidentUpdate(description="First aid applied, bandage replaced."),
        )
        self.assertEqual(
            updated.description, "First aid applied, bandage replaced."
        )

        # Delete
        deleted = delete_incident(self.db, incident.id)
        self.assertTrue(deleted)
        self.assertIsNone(get_incident_by_id(self.db, incident.id))
