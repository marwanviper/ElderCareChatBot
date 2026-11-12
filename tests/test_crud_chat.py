import unittest
from datetime import date

from src.crud.chat import (
    create_conversation,
    create_message,
    delete_conversation,
    delete_message,
    get_conversation_by_id,
    get_conversations_by_resident,
    get_messages_by_conversation,
    update_conversation,
)
from src.models import MessageRole, Resident, Role, User
from src.schemas.chat import (
    ConversationCreate,
    ConversationUpdate,
    MessageCreate,
)
from tests.test_base import BaseTestCase


class TestChatCrud(BaseTestCase):
    """Unit tests for Chat and Message CRUD functions."""

    def setUp(self):
        super().setUp()
        self.resident = Resident(
            name="Harold Finch",
            date_of_birth=date(1945, 8, 20),
            room_number="101",
        )
        self.user = User(
            name="Caregiver Sam",
            email="sam@eldercare.test",
            password_hash="secret",
            role=Role.CAREGIVER,
        )
        self.db.add_all([self.resident, self.user])
        self.db.commit()
        self.db.refresh(self.resident)
        self.db.refresh(self.user)

    def test_create_and_get_conversation(self):
        """Test creating a conversation via CRUD and retrieving it."""
        conv_in = ConversationCreate(
            resident_id=self.resident.id,
            user_id=self.user.id,
            title="Blood Pressure Discussion",
            status="active",
            extra_metadata={"device_type": "mobile"},
        )
        conv = create_conversation(self.db, conv_in)
        self.assertIsNotNone(conv.id)
        self.assertEqual(conv.title, "Blood Pressure Discussion")

        fetched = get_conversation_by_id(self.db, conv.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.resident_id, self.resident.id)
        self.assertEqual(fetched.user_id, self.user.id)
        self.assertEqual(fetched.extra_metadata["device_type"], "mobile")

    def test_get_conversations_by_resident_and_filter(self):
        """Test listing conversations for a resident with status filtering and pagination."""
        c1 = create_conversation(
            self.db,
            ConversationCreate(
                resident_id=self.resident.id,
                title="Active Session 1",
                status="active",
            ),
        )
        c2 = create_conversation(
            self.db,
            ConversationCreate(
                resident_id=self.resident.id,
                title="Archived Session",
                status="archived",
            ),
        )
        c3 = create_conversation(
            self.db,
            ConversationCreate(
                resident_id=self.resident.id,
                title="Active Session 2",
                status="active",
            ),
        )

        # Get all
        all_convs = get_conversations_by_resident(self.db, self.resident.id)
        self.assertEqual(len(all_convs), 3)

        # Filter by active
        active_convs = get_conversations_by_resident(
            self.db, self.resident.id, status="active"
        )
        self.assertEqual(len(active_convs), 2)
        for ac in active_convs:
            self.assertEqual(ac.status, "active")

        # Test pagination limit
        paged = get_conversations_by_resident(self.db, self.resident.id, limit=1)
        self.assertEqual(len(paged), 1)

    def test_update_conversation(self):
        """Test updating title, status, and metadata on a conversation."""
        conv = create_conversation(
            self.db,
            ConversationCreate(
                resident_id=self.resident.id,
                title="Initial Title",
                status="active",
            ),
        )

        update_data = ConversationUpdate(
            title="Updated Title",
            status="closed",
            extra_metadata={"summary": "Patient felt well."},
        )
        updated = update_conversation(self.db, conv.id, update_data)
        self.assertIsNotNone(updated)
        self.assertEqual(updated.title, "Updated Title")
        self.assertEqual(updated.status, "closed")
        self.assertEqual(updated.extra_metadata["summary"], "Patient felt well.")

    def test_delete_conversation(self):
        """Test deleting a conversation."""
        conv = create_conversation(
            self.db,
            ConversationCreate(
                resident_id=self.resident.id,
                title="Temporary",
            ),
        )
        conv_id = conv.id

        success = delete_conversation(self.db, conv_id)
        self.assertTrue(success)
        self.assertIsNone(get_conversation_by_id(self.db, conv_id))

        # Deleting nonexistent should return False
        self.assertFalse(delete_conversation(self.db, conv_id))

    def test_create_and_get_messages(self):
        """Test appending messages and retrieving history in chronological order."""
        conv = create_conversation(
            self.db,
            ConversationCreate(
                resident_id=self.resident.id,
                title="Q&A Session",
            ),
        )

        msg1 = create_message(
            self.db,
            conv.id,
            MessageCreate(
                role=MessageRole.USER,
                content="Did I take my morning pills?",
                token_count=7,
            ),
        )
        msg2 = create_message(
            self.db,
            conv.id,
            MessageCreate(
                role=MessageRole.ASSISTANT,
                content="Yes Harold, Nurse Sam confirmed your medication at 8:15 AM.",
                token_count=13,
                extra_metadata={"confidence": 0.99},
            ),
        )

        history = get_messages_by_conversation(self.db, conv.id)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0].id, msg1.id)
        self.assertEqual(history[1].id, msg2.id)
        self.assertEqual(history[0].content, "Did I take my morning pills?")
        self.assertEqual(history[1].role, MessageRole.ASSISTANT)

    def test_delete_message(self):
        """Test deleting an individual message."""
        conv = create_conversation(
            self.db,
            ConversationCreate(
                resident_id=self.resident.id,
                title="Msg Delete Test",
            ),
        )
        msg = create_message(
            self.db,
            conv.id,
            MessageCreate(
                role=MessageRole.USER,
                content="Draft message",
            ),
        )
        msg_id = msg.id

        deleted = delete_message(self.db, msg_id)
        self.assertTrue(deleted)
        self.assertEqual(len(get_messages_by_conversation(self.db, conv.id)), 0)

        # Deleting already deleted should return False
        self.assertFalse(delete_message(self.db, msg_id))


if __name__ == "__main__":
    unittest.main()

