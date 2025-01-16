"""Add proxy hourly limit setting

Revision ID: 002
Revises: 001
Create Date: 2024-01-16

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # Add proxy_hourly_limit column with default value of 150
    op.add_column('system_settings', 
        sa.Column('proxy_hourly_limit', 
            sa.Integer(), 
            nullable=False,
            server_default='150'
        )
    )

def downgrade():
    op.drop_column('system_settings', 'proxy_hourly_limit')
