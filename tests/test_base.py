import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base
# Ensure all models are imported so their tables exist in metadata
from src.models import (
    CareGoal,
    CareReport,
    Incident,
    Resident,
    User,
    UserResidentPermission,
)


class BaseTestCase(unittest.TestCase):
    """Base test case initializing an in-memory SQLite database for test isolation."""

    def setUp(self):
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.Session = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self.db = self.Session()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()
