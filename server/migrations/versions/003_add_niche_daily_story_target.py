"""Add daily story target to niches

Revision ID: 003
Revises: 002
Create Date: 2024-03-19

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None

def upgrade():
    # Add daily_story_target column with default value of 10
    op.add_column('niches', 
        sa.Column('daily_story_target', sa.Integer(), nullable=False, server_default='10')
    )

def downgrade():
    # Remove daily_story_target column
    op.drop_column('niches', 'daily_story_target')
