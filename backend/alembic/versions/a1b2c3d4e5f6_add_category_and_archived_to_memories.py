"""add_category_and_archived_to_memories

Revision ID: a1b2c3d4e5f6
Revises: 98c2a39475da
Create Date: 2026-07-21 16:45:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '98c2a39475da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('memories', sa.Column('category', sa.String(length=50), nullable=False, server_default='general'))
    op.add_column('memories', sa.Column('is_archived', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    op.create_index('ix_memories_category', 'memories', ['category'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_memories_category', table_name='memories')
    op.drop_column('memories', 'is_archived')
    op.drop_column('memories', 'category')
