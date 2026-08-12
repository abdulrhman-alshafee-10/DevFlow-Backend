"""Add notifications model

Revision ID: 3b8895d72792
Revises: 2a6694c61691
Create Date: 2026-08-12 13:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3b8895d72792'
down_revision: Union[str, None] = '2a6694c61691'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('notifications',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('organization_id', sa.UUID(), nullable=False),
    sa.Column('type', sa.String(length=50), nullable=False),
    sa.Column('title', sa.String(length=500), nullable=False),
    sa.Column('message', sa.Text(), nullable=True),
    sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('is_read', sa.Boolean(), server_default='false', nullable=False),
    sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notifications_created_at', 'notifications', ['created_at'], unique=False)
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'], unique=False)
    op.create_index('ix_notifications_user_id_is_read', 'notifications', ['user_id', 'is_read'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_notifications_user_id_is_read', table_name='notifications')
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    op.drop_index('ix_notifications_created_at', table_name='notifications')
    op.drop_table('notifications')
