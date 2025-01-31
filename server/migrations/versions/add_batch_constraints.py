"""Add batch state and position constraints

Revision ID: add_batch_constraints
Revises: add_batch_queue_columns
Create Date: 2025-01-30 19:28

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_batch_constraints'
down_revision = 'add_batch_queue_columns'
branch_labels = None
depends_on = None

def upgrade():
    # Create unique index for position (except null)
    op.create_index(
        'idx_unique_position',
        'batches',
        ['position'],
        unique=True,
        postgresql_where=sa.text('position IS NOT NULL')
    )

    # Add valid states check
    op.execute("""
        ALTER TABLE batches
        ADD CONSTRAINT valid_states
        CHECK (status IN ('queued', 'running', 'paused', 'done', 'error'))
    """)

    # Add position rules check
    op.execute("""
        ALTER TABLE batches
        ADD CONSTRAINT position_rules
        CHECK (
            (status IN ('paused', 'done', 'error') AND position IS NULL) OR
            (status = 'running' AND position = 0) OR
            (status = 'queued' AND position > 0)
        )
    """)

def downgrade():
    # Remove constraints
    op.execute('ALTER TABLE batches DROP CONSTRAINT IF EXISTS position_rules')
    op.execute('ALTER TABLE batches DROP CONSTRAINT IF EXISTS valid_states')
    op.drop_index('idx_unique_position', table_name='batches')