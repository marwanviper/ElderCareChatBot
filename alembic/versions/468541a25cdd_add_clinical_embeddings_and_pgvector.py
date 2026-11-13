"""add_clinical_embeddings_and_pgvector

Revision ID: 468541a25cdd
Revises: 319f8335a997
Create Date: 2026-11-12 23:26:39.804085

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = '468541a25cdd'
down_revision: Union[str, Sequence[str], None] = '319f8335a997'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: enable pgvector if available, create clinical_embeddings table."""
    conn = op.get_bind()
    is_postgres = conn.dialect.name == "postgresql"

    has_pgvector_ext = False
    if is_postgres:
        # Check if the C extension 'vector' is compiled/installed in pg_available_extensions
        res = conn.execute(
            sa.text("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'")
        ).scalar()
        if res:
            try:
                op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                has_pgvector_ext = True
            except Exception:
                has_pgvector_ext = False

    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "clinical_embeddings" not in existing_tables:
        # If pgvector extension is present, use native Vector(768); otherwise use sa.JSON()
        if has_pgvector_ext:
            from pgvector.sqlalchemy import Vector
            vector_col = Vector(768)
        else:
            vector_col = JSONB if is_postgres else sa.JSON()

        op.create_table(
            "clinical_embeddings",
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("resident_id", sa.Integer(), nullable=False),
            sa.Column("source_type", sa.String(length=50), nullable=False),
            sa.Column("source_id", sa.Integer(), nullable=False),
            sa.Column("chunk_index", sa.Integer(), server_default="0", nullable=False),
            sa.Column("chunk_text", sa.Text(), nullable=False),
            sa.Column("embedding", vector_col, nullable=False),
            sa.Column("extra_metadata", JSONB if is_postgres else sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["resident_id"], ["residents.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_clinical_embeddings_id", "clinical_embeddings", ["id"], unique=False)
        op.create_index("ix_clinical_embeddings_resident_id", "clinical_embeddings", ["resident_id"], unique=False)
        op.create_index("ix_clinical_embeddings_source_type", "clinical_embeddings", ["source_type"], unique=False)
        op.create_index("ix_clinical_embeddings_source_id", "clinical_embeddings", ["source_id"], unique=False)
        op.create_index(
            "idx_clinical_embeddings_lookup",
            "clinical_embeddings",
            ["resident_id", "source_type", "source_id"],
            unique=False,
        )

        if has_pgvector_ext:
            op.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_clinical_embeddings_hnsw
                ON clinical_embeddings
                USING hnsw (embedding vector_cosine_ops)
                WITH (m = 16, ef_construction = 64);
                """
            )


def downgrade() -> None:
    """Downgrade schema: drop clinical_embeddings table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "clinical_embeddings" in existing_tables:
        op.drop_table("clinical_embeddings")
