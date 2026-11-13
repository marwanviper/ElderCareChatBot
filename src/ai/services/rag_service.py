"""Clinical RAG Service: Document Vectorization and Semantic Similarity Search."""

import math
from typing import Any
from sqlalchemy.orm import Session

from src.ai.embeddings.base import BaseEmbeddingProvider
from src.ai.embeddings.factory import EmbeddingProviderFactory
from src.core.logging import logger
from src.models.clinical_embedding import ClinicalEmbedding
from src.models.care_report import CareReport
from src.models.care_goal import CareGoal
from src.models.incident import Incident
from src.models.resident import Resident


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


class RAGService:
    """Orchestrates embedding generation, vector persistence, and resident-scoped semantic retrieval."""

    @staticmethod
    def _get_provider(provider_name: str | None = None) -> BaseEmbeddingProvider:
        return EmbeddingProviderFactory.get_provider(provider_name)

    # -------------------------------------------------------------------------
    # Indexing Clinical Records
    # -------------------------------------------------------------------------

    @classmethod
    def index_care_report(
        cls,
        db: Session,
        report: CareReport,
        resident_name: str | None = None,
        provider_name: str | None = None,
    ) -> list[ClinicalEmbedding]:
        """Embed and upsert a CareReport."""
        cls.delete_by_source(db, resident_id=report.resident_id, source_type="care_report", source_id=report.id)

        res_name = resident_name
        if not res_name:
            res = db.query(Resident).filter(Resident.id == report.resident_id).first()
            res_name = res.name if res else "Unknown Resident"

        date_str = str(report.report_date or "")
        chunk_text = (
            f"[Care Report - Date: {date_str}] Resident: {res_name}. "
            f"Observation Notes: {report.content}"
        )

        provider = cls._get_provider(provider_name)
        embedding_vec = provider.embed_text(chunk_text)

        rec = ClinicalEmbedding(
            resident_id=report.resident_id,
            source_type="care_report",
            source_id=report.id,
            chunk_index=0,
            chunk_text=chunk_text,
            embedding=embedding_vec,
            extra_metadata={
                "report_date": date_str,
                "created_by": report.created_by,
            },
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        logger.info("Indexed CareReport #%s for resident %s", report.id, report.resident_id)
        return [rec]

    @classmethod
    def index_care_goal(
        cls,
        db: Session,
        goal: CareGoal,
        resident_name: str | None = None,
        provider_name: str | None = None,
    ) -> list[ClinicalEmbedding]:
        """Embed and upsert a CareGoal."""
        cls.delete_by_source(db, resident_id=goal.resident_id, source_type="care_goal", source_id=goal.id)

        res_name = resident_name
        if not res_name:
            res = db.query(Resident).filter(Resident.id == goal.resident_id).first()
            res_name = res.name if res else "Unknown Resident"

        chunk_text = (
            f"[Care Goal - Status: {goal.status.upper()}] Resident: {res_name}. "
            f"Target Objective: {goal.goal}"
        )

        provider = cls._get_provider(provider_name)
        embedding_vec = provider.embed_text(chunk_text)

        rec = ClinicalEmbedding(
            resident_id=goal.resident_id,
            source_type="care_goal",
            source_id=goal.id,
            chunk_index=0,
            chunk_text=chunk_text,
            embedding=embedding_vec,
            extra_metadata={"status": goal.status},
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        logger.info("Indexed CareGoal #%s for resident %s", goal.id, goal.resident_id)
        return [rec]

    @classmethod
    def index_incident(
        cls,
        db: Session,
        incident: Incident,
        resident_name: str | None = None,
        provider_name: str | None = None,
    ) -> list[ClinicalEmbedding]:
        """Embed and upsert an Adverse Incident."""
        cls.delete_by_source(db, resident_id=incident.resident_id, source_type="incident", source_id=incident.id)

        res_name = resident_name
        if not res_name:
            res = db.query(Resident).filter(Resident.id == incident.resident_id).first()
            res_name = res.name if res else "Unknown Resident"

        date_str = str(incident.incident_date or "")
        chunk_text = (
            f"[Adverse Incident - Type: {incident.type}, Date: {date_str}] Resident: {res_name}. "
            f"Details & Actions: {incident.description}"
        )

        provider = cls._get_provider(provider_name)
        embedding_vec = provider.embed_text(chunk_text)

        rec = ClinicalEmbedding(
            resident_id=incident.resident_id,
            source_type="incident",
            source_id=incident.id,
            chunk_index=0,
            chunk_text=chunk_text,
            embedding=embedding_vec,
            extra_metadata={"type": incident.type, "incident_date": date_str},
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        logger.info("Indexed Incident #%s for resident %s", incident.id, incident.resident_id)
        return [rec]

    @classmethod
    def index_resident_profile(
        cls,
        db: Session,
        resident: Resident,
        provider_name: str | None = None,
    ) -> list[ClinicalEmbedding]:
        """Embed baseline resident demographic and room profile."""
        cls.delete_by_source(db, resident_id=resident.id, source_type="resident_profile", source_id=resident.id)

        chunk_text = (
            f"[Resident Profile] Full Name: {resident.name}. "
            f"Assigned Room: {resident.room_number or 'Unassigned'}. "
            f"Date of Birth: {resident.date_of_birth or 'Not specified'}."
        )

        provider = cls._get_provider(provider_name)
        embedding_vec = provider.embed_text(chunk_text)

        rec = ClinicalEmbedding(
            resident_id=resident.id,
            source_type="resident_profile",
            source_id=resident.id,
            chunk_index=0,
            chunk_text=chunk_text,
            embedding=embedding_vec,
            extra_metadata={"name": resident.name, "room": resident.room_number},
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        logger.info("Indexed Resident Profile for resident %s", resident.id)
        return [rec]

    # -------------------------------------------------------------------------
    # Deletion & Cleanup
    # -------------------------------------------------------------------------

    @classmethod
    def delete_by_source(
        cls, db: Session, resident_id: int, source_type: str, source_id: int
    ) -> int:
        """Purge existing embeddings for a specific source record."""
        count = (
            db.query(ClinicalEmbedding)
            .filter(
                ClinicalEmbedding.resident_id == resident_id,
                ClinicalEmbedding.source_type == source_type,
                ClinicalEmbedding.source_id == source_id,
            )
            .delete(synchronize_session=False)
        )
        db.commit()
        return count

    # -------------------------------------------------------------------------
    # Semantic Search & Retrieval
    # -------------------------------------------------------------------------

    @classmethod
    def search_relevant_context(
        cls,
        db: Session,
        resident_id: int,
        query_text: str,
        top_k: int = 4,
        threshold: float = 0.35,
        provider_name: str | None = None,
    ) -> list[str]:
        """Embed the query and retrieve top-K most similar clinical chunks for the resident."""
        if not query_text or not query_text.strip():
            return []

        provider = cls._get_provider(provider_name)
        query_vec = provider.embed_text(query_text.strip())

        # Load all embeddings scoped strictly to this resident
        records = (
            db.query(ClinicalEmbedding)
            .filter(ClinicalEmbedding.resident_id == resident_id)
            .all()
        )

        if not records:
            return []

        scored: list[tuple[float, ClinicalEmbedding]] = []
        for r in records:
            emb = r.embedding
            if isinstance(emb, list):
                score = cosine_similarity(query_vec, emb)
                if score >= threshold:
                    scored.append((score, r))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1].chunk_text for item in scored[:top_k]]

    # -------------------------------------------------------------------------
    # Non-blocking Safe Indexing Wrappers (for route handlers)
    # -------------------------------------------------------------------------

    @classmethod
    def safe_index_care_report(cls, db: Session, report: CareReport) -> None:
        """Safely index a care report without letting failures interrupt caller."""
        try:
            cls.index_care_report(db=db, report=report)
        except Exception as exc:
            logger.warning("Safe RAG indexing skipped for CareReport #%s: %s", getattr(report, "id", None), exc)

    @classmethod
    def safe_index_care_goal(cls, db: Session, goal: CareGoal) -> None:
        """Safely index a care goal without letting failures interrupt caller."""
        try:
            cls.index_care_goal(db=db, goal=goal)
        except Exception as exc:
            logger.warning("Safe RAG indexing skipped for CareGoal #%s: %s", getattr(goal, "id", None), exc)

    @classmethod
    def safe_index_incident(cls, db: Session, incident: Incident) -> None:
        """Safely index an incident without letting failures interrupt caller."""
        try:
            cls.index_incident(db=db, incident=incident)
        except Exception as exc:
            logger.warning("Safe RAG indexing skipped for Incident #%s: %s", getattr(incident, "id", None), exc)

    @classmethod
    def safe_index_resident(cls, db: Session, resident: Resident) -> None:
        """Safely index a resident profile without letting failures interrupt caller."""
        try:
            cls.index_resident_profile(db=db, resident=resident)
        except Exception as exc:
            logger.warning("Safe RAG indexing skipped for Resident #%s: %s", getattr(resident, "id", None), exc)

    @classmethod
    def safe_delete_by_source(cls, db: Session, resident_id: int, source_type: str, source_id: int) -> None:
        """Safely delete clinical embeddings for a source record."""
        try:
            cls.delete_by_source(db=db, resident_id=resident_id, source_type=source_type, source_id=source_id)
        except Exception as exc:
            logger.warning("Safe RAG deletion skipped for %s #%s: %s", source_type, source_id, exc)
