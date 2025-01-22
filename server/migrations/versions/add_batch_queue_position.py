"""add batch queue position

Revision ID: 2023_12_add_batch_queue
Revises: 
Create Date: 2023-12-21 10:00:00.000000
"""
from flask import current_app

# revision identifiers
revision = '2023_12_add_batch_queue'
down_revision = None
branch_labels = None
depends_on = None
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Add queue_position column
    op.add_column('batches', sa.Column('queue_position', sa.Integer, nullable=True))

def downgrade():
    # Remove queue_position column
    op.drop_column('batches', 'queue_position')
