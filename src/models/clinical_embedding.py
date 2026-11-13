"""SQLAlchemy model for clinical vector embeddings and RAG retrieval."""

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from src.database import Base
from utils.utils import _utcnow

# Cross-dialect JSON/JSONB type compatible with SQLite (tests) and PostgreSQL (production)
JSONType = JSON().with_variant(JSONB, "postgresql")


class ClinicalEmbedding(Base):
    """Stores high-dimensional vector embeddings of clinical documents (reports, goals, incidents, profiles)."""

    __tablename__ = "clinical_embeddings"

    id = Column(Integer, primary_key=True, index=True)
    resident_id = Column(
        Integer,
        ForeignKey("residents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_type = Column(
        String(50),
        nullable=False,
        index=True,
        doc="Category: 'care_report', 'care_goal', 'incident', or 'resident_profile'",
    )
    source_id = Column(
        Integer,
        nullable=False,
        index=True,
        doc="Foreign ID of the source record in its respective table",
    )
    chunk_index = Column(
        Integer,
        default=0,
        nullable=False,
        doc="Sequential chunk index for partitioned documents",
    )
    chunk_text = Column(
        Text,
        nullable=False,
        doc="The exact textual chunk embedded into the vector space",
    )
    embedding = Column(
        JSONType,
        nullable=False,
        doc="Vector representation (float list stored as JSONB / native Vector)",
    )
    extra_metadata = Column(
        JSONType,
        nullable=True,
        doc="Auxiliary clinical metadata, tags, and timestamps",
    )
    created_at = Column(
        DateTime,
        default=_utcnow,
        nullable=False,
        doc="Timestamp when this embedding was generated",
    )

    # Relationships
    resident = relationship("Resident", back_populates="clinical_embeddings")

    __table_args__ = (
        Index(
            "idx_clinical_embeddings_lookup",
            "resident_id",
            "source_type",
            "source_id",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ClinicalEmbedding(id={self.id}, resident_id={self.resident_id}, "
            f"source_type='{self.source_type}', source_id={self.source_id})>"
        )
