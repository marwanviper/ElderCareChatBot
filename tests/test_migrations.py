import os
import unittest
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


class TestAlembicMigrations(unittest.TestCase):
    """Integration test verifying Alembic migrations generation, upgrade, and downgrade cycles."""

    TEST_DB_FILE = "test_alembic_run.db"
    TEST_DB_URL = f"sqlite:///./{TEST_DB_FILE}"

    def setUp(self):
        # Remove any pre-existing test db file
        if os.path.exists(self.TEST_DB_FILE):
            try:
                os.remove(self.TEST_DB_FILE)
            except OSError:
                pass

        # Prepare Alembic config
        ini_path = Path(__file__).resolve().parent.parent / "alembic.ini"
        self.alembic_cfg = Config(str(ini_path))
        self.alembic_cfg.set_main_option("sqlalchemy.url", self.TEST_DB_URL)
        os.environ["DATABASE_URL"] = self.TEST_DB_URL

    def tearDown(self):
        if os.path.exists(self.TEST_DB_FILE):
            try:
                os.remove(self.TEST_DB_FILE)
            except OSError:
                pass

    def test_alembic_upgrade_and_downgrade_cycle(self):
        """Verify full upgrade to head, schema inspection, and downgrade to base."""
        # Step 1: Run upgrade to head
        command.upgrade(self.alembic_cfg, "head")

        engine = create_engine(self.TEST_DB_URL)
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # All 8 tables must exist
        expected_tables = {
            "users",
            "residents",
            "care_reports",
            "care_goals",
            "incidents",
            "user_resident_permissions",
            "conversations",
            "messages",
        }
        for table in expected_tables:
            self.assertIn(
                table,
                tables,
                f"Expected table '{table}' not found in migrated database",
            )

        # Verify conversations columns
        conv_cols = {col["name"] for col in inspector.get_columns("conversations")}
        self.assertTrue(
            {
                "id",
                "resident_id",
                "user_id",
                "title",
                "status",
                "created_at",
                "updated_at",
                "extra_metadata",
            }.issubset(conv_cols)
        )

        # Verify messages columns
        msg_cols = {col["name"] for col in inspector.get_columns("messages")}
        self.assertTrue(
            {
                "id",
                "conversation_id",
                "role",
                "content",
                "token_count",
                "created_at",
                "extra_metadata",
            }.issubset(msg_cols)
        )

        # Verify foreign keys on messages
        msg_fks = inspector.get_foreign_keys("messages")
        conv_fk_found = any(
            fk.get("referred_table") == "conversations" for fk in msg_fks
        )
        self.assertTrue(conv_fk_found, "Foreign key from messages to conversations not found")

        # Step 2: Downgrade back to base
        engine.dispose()
        command.downgrade(self.alembic_cfg, "base")

        engine = create_engine(self.TEST_DB_URL)
        inspector = inspect(engine)
        remaining_tables = inspector.get_table_names()
        engine.dispose()

        self.assertNotIn("conversations", remaining_tables)
        self.assertNotIn("messages", remaining_tables)
        self.assertNotIn("residents", remaining_tables)


if __name__ == "__main__":
    unittest.main()

