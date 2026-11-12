import unittest
from datetime import date
from sqlalchemy.exc import IntegrityError

from src.models import (
    Conversation,
    Message,
    MessageRole,
    Resident,
    Role,
    User,
)
from tests.test_base import BaseTestCase


class TestChatModels(BaseTestCase):
    """Unit tests for Conversation and Message SQLAlchemy models and relationships."""

    def setUp(self):
        super().setUp()
        # Create a test resident
        self.resident = Resident(
            name="Eleanor Vance",
            date_of_birth=date(1938, 5, 12),
            room_number="204-B",
        )
        # Create a test caregiver user
        self.caregiver = User(
            name="Nurse Ratched",
            email="nurse@eldercare.test",
            password_hash="hashedpass",
            role=Role.CAREGIVER,
        )
        self.db.add_all([self.resident, self.caregiver])
        self.db.commit()
        self.db.refresh(self.resident)
        self.db.refresh(self.caregiver)

    def test_create_conversation_with_user(self):
        """Test creating a conversation with an associated staff user."""
        conv = Conversation(
            resident_id=self.resident.id,
            user_id=self.caregiver.id,
            title="Daily Wellness Check",
            status="active",
            extra_metadata={"device": "tablet", "floor": 2},
        )
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)

        self.assertIsNotNone(conv.id)
        self.assertEqual(conv.resident_id, self.resident.id)
        self.assertEqual(conv.user_id, self.caregiver.id)
        self.assertEqual(conv.title, "Daily Wellness Check")
        self.assertEqual(conv.status, "active")
        self.assertEqual(conv.extra_metadata["device"], "tablet")
        self.assertIsNotNone(conv.created_at)
        self.assertIsNotNone(conv.updated_at)

    def test_create_conversation_without_user(self):
        """Test creating a resident-initiated conversation (user_id is None)."""
        conv = Conversation(
            resident_id=self.resident.id,
            user_id=None,
            title="Resident Direct Chat",
            status="active",
        )
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)

        self.assertIsNotNone(conv.id)
        self.assertIsNone(conv.user_id)
        self.assertEqual(conv.resident_id, self.resident.id)

    def test_create_messages_with_roles(self):
        """Test creating messages with system, user, and assistant roles."""
        conv = Conversation(
            resident_id=self.resident.id,
            title="Morning Greeting",
        )
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)

        msg_system = Message(
            conversation_id=conv.id,
            role=MessageRole.SYSTEM,
            content="You are a compassionate geriatric care assistant.",
        )
        msg_user = Message(
            conversation_id=conv.id,
            role=MessageRole.USER,
            content="Good morning, what activities are scheduled today?",
            token_count=10,
        )
        msg_assistant = Message(
            conversation_id=conv.id,
            role=MessageRole.ASSISTANT,
            content="Good morning Eleanor! At 10:00 AM there is gentle chair yoga in the garden room.",
            token_count=22,
            extra_metadata={"model": "gemini-2.0-flash", "finish_reason": "stop"},
        )

        self.db.add_all([msg_system, msg_user, msg_assistant])
        self.db.commit()

        # Query messages back
        messages = (
            self.db.query(Message)
            .filter(Message.conversation_id == conv.id)
            .order_by(Message.created_at.asc())
            .all()
        )
        self.assertEqual(len(messages), 3)
        self.assertEqual(messages[0].role, MessageRole.SYSTEM)
        self.assertEqual(messages[1].role, MessageRole.USER)
        self.assertEqual(messages[2].role, MessageRole.ASSISTANT)
        self.assertEqual(messages[2].token_count, 22)
        self.assertEqual(messages[2].extra_metadata["model"], "gemini-2.0-flash")

    def test_resident_conversations_relationship(self):
        """Test bidirectional relationship between Resident and Conversation."""
        conv1 = Conversation(resident_id=self.resident.id, title="Session 1")
        conv2 = Conversation(resident_id=self.resident.id, title="Session 2")
        self.db.add_all([conv1, conv2])
        self.db.commit()

        # Refresh resident
        self.db.refresh(self.resident)
        self.assertEqual(len(self.resident.conversations), 2)
        self.assertIn(conv1, self.resident.conversations)
        self.assertIn(conv2, self.resident.conversations)

    def test_conversation_messages_relationship_ordering(self):
        """Test conversation.messages relationship and ordered cascade."""
        conv = Conversation(resident_id=self.resident.id, title="Ordered Check")
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)

        m1 = Message(conversation_id=conv.id, role=MessageRole.USER, content="First")
        m2 = Message(conversation_id=conv.id, role=MessageRole.ASSISTANT, content="Second")
        self.db.add_all([m1, m2])
        self.db.commit()

        self.db.refresh(conv)
        self.assertEqual(len(conv.messages), 2)
        self.assertEqual(conv.messages[0].content, "First")
        self.assertEqual(conv.messages[1].content, "Second")
        self.assertEqual(conv.messages[0].conversation, conv)

    def test_cascade_delete_conversation_removes_messages(self):
        """Deleting a conversation must cascade-delete all its child messages."""
        conv = Conversation(resident_id=self.resident.id, title="To Be Deleted")
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)

        m1 = Message(conversation_id=conv.id, role=MessageRole.USER, content="Hello")
        m2 = Message(conversation_id=conv.id, role=MessageRole.ASSISTANT, content="Hi")
        self.db.add_all([m1, m2])
        self.db.commit()

        conv_id = conv.id
        self.assertEqual(self.db.query(Message).filter(Message.conversation_id == conv_id).count(), 2)

        # Delete conversation
        self.db.delete(conv)
        self.db.commit()

        # Messages must be gone
        self.assertEqual(self.db.query(Message).filter(Message.conversation_id == conv_id).count(), 0)

    def test_cascade_delete_resident_removes_conversations(self):
        """Deleting a resident must cascade-delete all associated conversations and messages."""
        conv = Conversation(resident_id=self.resident.id, title="Resident Conv")
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)

        msg = Message(conversation_id=conv.id, role=MessageRole.USER, content="Resident Msg")
        self.db.add(msg)
        self.db.commit()

        res_id = self.resident.id
        conv_id = conv.id

        # Delete resident
        self.db.delete(self.resident)
        self.db.commit()

        # Conversation and message must be removed
        self.assertIsNone(self.db.query(Conversation).filter(Conversation.id == conv_id).first())
        self.assertIsNone(self.db.query(Message).filter(Message.id == msg.id).first())

    def test_user_set_null_on_delete(self):
        """Deleting a staff user should set conversation.user_id to NULL, not delete conversation."""
        conv = Conversation(
            resident_id=self.resident.id,
            user_id=self.caregiver.id,
            title="Preserve Conv On User Delete",
        )
        self.db.add(conv)
        self.db.commit()
        self.db.refresh(conv)

        conv_id = conv.id
        # Delete caregiver user
        self.db.delete(self.caregiver)
        self.db.commit()

        # Conversation should still exist, with user_id = None
        surviving_conv = self.db.query(Conversation).filter(Conversation.id == conv_id).first()
        self.assertIsNotNone(surviving_conv)
        self.assertIsNone(surviving_conv.user_id)


if __name__ == "__main__":
    unittest.main()

