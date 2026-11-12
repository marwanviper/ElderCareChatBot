"""initial_baseline

Revision ID: ec9f5f8b6d16
Revises: 
Create Date: 2026-11-12 13:10:30.845641

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ec9f5f8b6d16'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema idempotently."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = set(inspector.get_table_names())

    if 'residents' not in tables:
        op.create_table(
            'residents',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('date_of_birth', sa.Date(), nullable=True),
            sa.Column('room_number', sa.String(length=20), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('residents', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_residents_id'), ['id'], unique=False)
            batch_op.create_index(batch_op.f('ix_residents_name'), ['name'], unique=False)

    if 'users' not in tables:
        op.create_table(
            'users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('password_hash', sa.Text(), nullable=False),
            sa.Column('role', sa.Enum('admin', 'caregiver', name='role', native_enum=False, length=20), nullable=False),
            sa.Column('deleted_date', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_users_email'), ['email'], unique=True)
            batch_op.create_index(batch_op.f('ix_users_id'), ['id'], unique=False)
            batch_op.create_index(batch_op.f('ix_users_name'), ['name'], unique=False)

    if 'care_goals' not in tables:
        op.create_table(
            'care_goals',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('resident_id', sa.Integer(), nullable=False),
            sa.Column('goal', sa.Text(), nullable=False),
            sa.Column('status', sa.String(length=30), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['resident_id'], ['residents.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('care_goals', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_care_goals_id'), ['id'], unique=False)

    if 'care_reports' not in tables:
        op.create_table(
            'care_reports',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('resident_id', sa.Integer(), nullable=False),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('report_date', sa.DateTime(), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
            sa.ForeignKeyConstraint(['resident_id'], ['residents.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('care_reports', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_care_reports_id'), ['id'], unique=False)

    if 'incidents' not in tables:
        op.create_table(
            'incidents',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('resident_id', sa.Integer(), nullable=False),
            sa.Column('incident_date', sa.DateTime(), nullable=False),
            sa.Column('type', sa.String(length=50), nullable=False),
            sa.Column('description', sa.Text(), nullable=False),
            sa.ForeignKeyConstraint(['resident_id'], ['residents.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('incidents', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_incidents_id'), ['id'], unique=False)

    if 'user_resident_permissions' not in tables:
        op.create_table(
            'user_resident_permissions',
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('resident_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['resident_id'], ['residents.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('user_id', 'resident_id')
        )


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = set(inspector.get_table_names())

    if 'user_resident_permissions' in tables:
        op.drop_table('user_resident_permissions')

    if 'incidents' in tables:
        with op.batch_alter_table('incidents', schema=None) as batch_op:
            batch_op.drop_index(batch_op.f('ix_incidents_id'))
        op.drop_table('incidents')

    if 'care_reports' in tables:
        with op.batch_alter_table('care_reports', schema=None) as batch_op:
            batch_op.drop_index(batch_op.f('ix_care_reports_id'))
        op.drop_table('care_reports')

    if 'care_goals' in tables:
        with op.batch_alter_table('care_goals', schema=None) as batch_op:
            batch_op.drop_index(batch_op.f('ix_care_goals_id'))
        op.drop_table('care_goals')

    if 'users' in tables:
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.drop_index(batch_op.f('ix_users_name'))
            batch_op.drop_index(batch_op.f('ix_users_id'))
            batch_op.drop_index(batch_op.f('ix_users_email'))
        op.drop_table('users')

    if 'residents' in tables:
        with op.batch_alter_table('residents', schema=None) as batch_op:
            batch_op.drop_index(batch_op.f('ix_residents_name'))
            batch_op.drop_index(batch_op.f('ix_residents_id'))
        op.drop_table('residents')
