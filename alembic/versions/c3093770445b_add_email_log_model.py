"""add email_log model

Revision ID: c3093770445b
Revises: 3b8895d72792
Create Date: 2026-08-12 18:59:53.134477

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3093770445b'
down_revision: Union[str, Sequence[str], None] = '3b8895d72792'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'email_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email_to', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_logs_email_to'), 'email_logs', ['email_to'], unique=False)
    op.create_index(op.f('ix_email_logs_id'), 'email_logs', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_email_logs_id'), table_name='email_logs')
    op.drop_index(op.f('ix_email_logs_email_to'), table_name='email_logs')
    op.drop_table('email_logs')
