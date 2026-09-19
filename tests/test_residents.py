from datetime import date
from pydantic import ValidationError

from src.crud.resident import (
    create_resident,
    delete_resident,
    get_all_residents,
    get_resident_by_id,
    update_resident,
)
from src.schemas.resident import ResidentCreate, ResidentResponse, ResidentUpdate
from tests.test_base import BaseTestCase


class TestResidentCRUD(BaseTestCase):
    """Test suite for Resident model, validation, and CRUD operations."""

    def test_create_resident_success(self):
        res_in = ResidentCreate(
            name="Anna Müller",
            date_of_birth=date(1942, 3, 14),
            room_number="101",
        )
        resident = create_resident(self.db, res_in)
        self.assertIsNotNone(resident.id)
        self.assertEqual(resident.name, "Anna Müller")
        self.assertEqual(resident.date_of_birth, date(1942, 3, 14))
        self.assertEqual(resident.room_number, "101")

    def test_resident_validation_empty_name(self):
        with self.assertRaises(ValidationError):
            ResidentCreate(name="", room_number="102")

    def test_resident_response_serialization(self):
        res_in = ResidentCreate(
            name="Peter Schneider",
            date_of_birth=date(1938, 11, 2),
            room_number="102",
        )
        resident = create_resident(self.db, res_in)
        resp = ResidentResponse.model_validate(resident)
        self.assertEqual(resp.id, resident.id)
        self.assertEqual(resp.name, "Peter Schneider")
        self.assertEqual(resp.room_number, "102")

    def test_get_and_update_resident(self):
        res_in = ResidentCreate(name="Maria Rossi", room_number="103")
        resident = create_resident(self.db, res_in)

        # Get by id
        fetched = get_resident_by_id(self.db, resident.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.name, "Maria Rossi")

        # Update room number
        update_in = ResidentUpdate(room_number="205")
        updated = update_resident(self.db, resident.id, update_in)
        self.assertEqual(updated.room_number, "205")
        self.assertEqual(updated.name, "Maria Rossi")

    def test_get_all_residents(self):
        for i in range(3):
            create_resident(
                self.db, ResidentCreate(name=f"Resident {i}", room_number=f"Room-{i}")
            )
        all_res = get_all_residents(self.db, skip=0, limit=10)
        self.assertEqual(len(all_res), 3)

    def test_delete_resident(self):
        res_in = ResidentCreate(name="Hans Weber", room_number="104")
        resident = create_resident(self.db, res_in)
        deleted = delete_resident(self.db, resident.id)
        self.assertTrue(deleted)
        self.assertIsNone(get_resident_by_id(self.db, resident.id))
