"""Add proxy and session columns

Revision ID: add_proxy_and_session_columns
Revises: 011_add_profiles_to_check
Create Date: 2025-01-19 23:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_proxy_and_session_columns'
down_revision = '011_add_profiles_to_check'
branch_labels = None
depends_on = None

def upgrade():
    # Add proxy_id and session_id to batch_profiles
    op.add_column('batch_profiles', sa.Column('proxy_id', sa.String(36), sa.ForeignKey('proxies.id'), nullable=True))
    op.add_column('batch_profiles', sa.Column('session_id', sa.Integer, sa.ForeignKey('sessions.id'), nullable=True))

    # Add missing columns to proxies
    op.add_column('proxies', sa.Column('total_requests', sa.Integer, nullable=False, server_default='0'))
    op.add_column('proxies', sa.Column('failed_requests', sa.Integer, nullable=False, server_default='0'))
    op.add_column('proxies', sa.Column('requests_this_hour', sa.Integer, nullable=False, server_default='0'))
    op.add_column('proxies', sa.Column('error_count', sa.Integer, nullable=False, server_default='0'))

def downgrade():
    # Remove proxy_id and session_id from batch_profiles
    op.drop_column('batch_profiles', 'proxy_id')
    op.drop_column('batch_profiles', 'session_id')

    # Remove columns from proxies
    op.drop_column('proxies', 'total_requests')
    op.drop_column('proxies', 'failed_requests')
    op.drop_column('proxies', 'requests_this_hour')
    op.drop_column('proxies', 'error_count')
