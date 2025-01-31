"""Add queue position and priority columns to batches

Revision ID: add_batch_queue_columns
Revises: (previous revision ID)
Create Date: 2025-01-30 18:23

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = 'add_batch_queue_columns'
down_revision = None  # Update this to your previous migration
branch_labels = None
depends_on = None

def upgrade():
    # Add position column with unique constraint
    op.add_column('batches',
        sa.Column('position', sa.Integer, nullable=True, unique=True)
    )
    
    # Add priority column with default value
    op.add_column('batches',
        sa.Column('priority', sa.Integer, nullable=False, server_default='0')
    )
    
    # Create index on position for faster queue queries
    op.create_index(
        'ix_batches_position',
        'batches',
        ['position'],
        unique=True,
        postgresql_where=sa.text('position IS NOT NULL')  # Partial index excluding NULL values
    )

def downgrade():
    # Remove index
    op.drop_index('ix_batches_position')
    
    # Remove columns
    op.drop_column('batches', 'priority')
    op.drop_column('batches', 'position')