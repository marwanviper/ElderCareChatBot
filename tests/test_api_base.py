import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.deps import get_db
from src.core.security import create_access_token, hash_password
from src.crud.user import create_user
from src.database import Base
from src.main import app
from src.models import (
    CareGoal,
    CareReport,
    Incident,
    Resident,
    User,
    UserResidentPermission,
)
from src.schemas.user import UserCreate


class ApiTestCase(unittest.TestCase):
    """Base class for FastAPI TestClient integration testing with in-memory DB."""

    def setUp(self):
        self.engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(bind=self.engine)
        self.TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )
        self.db = self.TestingSessionLocal()

        def override_get_db():
            db = self.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()
        self.db.close()
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()

    def create_test_user(
        self,
        name: str = "Test User",
        email: str = "test@eldercare.test",
        password: str = "Password123!",
        role: str = "caregiver",
    ) -> User:
        """Helper to create a user with a valid bcrypt password hash."""
        hashed_pwd = hash_password(password)
        user_in = UserCreate(
            name=name, email=email, password=password, role=role
        )
        return create_user(self.db, user_data=user_in, password_hash=hashed_pwd)

    def get_auth_headers(self, user: User) -> dict[str, str]:
        """Helper to generate Authorization Bearer headers for a user."""
        token = create_access_token(
            data={"sub": user.email, "user_id": user.id, "role": user.role}
        )
        return {"Authorization": f"Bearer {token}"}
