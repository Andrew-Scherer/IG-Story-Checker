"""add batch logs table

Revision ID: add_batch_logs_table
Revises: add_proxy_and_session_columns
Create Date: 2023-05-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_batch_logs_table'
down_revision = 'add_proxy_and_session_columns'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('batch_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('batch_id', sa.String(36), sa.ForeignKey('batches.id'), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('message', sa.String(500), nullable=False),
        sa.Column('profile_id', sa.String(36), sa.ForeignKey('profiles.id'), nullable=True),
        sa.Column('proxy_id', sa.String(36), sa.ForeignKey('proxies.id'), nullable=True),
    )

def downgrade():
    op.drop_table('batch_logs')
