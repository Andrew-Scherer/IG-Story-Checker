"""Add timezone to batch timestamps

Revision ID: 004
Revises: 003
Create Date: 2024-03-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TIMESTAMP

# revision identifiers, used by Alembic
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade():
    # Convert start_time and end_time columns to timezone-aware
    op.alter_column('batches', 'start_time',
        type_=TIMESTAMP(timezone=True),
        existing_type=sa.DateTime(),
        existing_nullable=True
    )
    op.alter_column('batches', 'end_time',
        type_=TIMESTAMP(timezone=True),
        existing_type=sa.DateTime(),
        existing_nullable=True
    )

def downgrade():
    # Convert start_time and end_time columns back to timezone-naive
    op.alter_column('batches', 'start_time',
        type_=sa.DateTime(),
        existing_type=TIMESTAMP(timezone=True),
        existing_nullable=True
    )
    op.alter_column('batches', 'end_time',
        type_=sa.DateTime(),
        existing_type=TIMESTAMP(timezone=True),
        existing_nullable=True
    )
