"""Add timezone to story timestamps

Revision ID: 005
Revises: 004
Create Date: 2024-03-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TIMESTAMP

# revision identifiers, used by Alembic
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None

def upgrade():
    # Convert detected_at and expires_at columns to timezone-aware
    op.alter_column('story_results', 'detected_at',
        type_=TIMESTAMP(timezone=True),
        existing_type=sa.DateTime(),
        existing_nullable=False
    )
    op.alter_column('story_results', 'expires_at',
        type_=TIMESTAMP(timezone=True),
        existing_type=sa.DateTime(),
        existing_nullable=False
    )

def downgrade():
    # Convert detected_at and expires_at columns back to timezone-naive
    op.alter_column('story_results', 'detected_at',
        type_=sa.DateTime(),
        existing_type=TIMESTAMP(timezone=True),
        existing_nullable=False
    )
    op.alter_column('story_results', 'expires_at',
        type_=sa.DateTime(),
        existing_type=TIMESTAMP(timezone=True),
        existing_nullable=False
    )
