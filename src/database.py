import sqlalchemy
from src.config import Settings
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# Load settings from the .env file
settings = Settings()

# Create a SQLAlchemy engine using the DATABASE_URL from settings echo=True enables logging of SQL statements for debugging purposes.
engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(declarative_base):
    """Base class for all SQLAlchemy models."""

    pass


def get_db():
    """Dependency to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
