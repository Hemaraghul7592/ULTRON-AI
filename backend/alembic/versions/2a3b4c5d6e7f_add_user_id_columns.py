"""add_user_id_columns

Revision ID: 7496ccf83cb6
Revises: 1ba6700f8cd2
Create Date: 2026-07-20 20:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '7496ccf83cb6'
down_revision: Union[str, None] = '1ba6700f8cd2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    _add_user_id_to_table('conversations')
    _add_user_id_to_table('memories')
    _add_user_id_to_table('tasks')
    _add_user_id_to_table('entities')


def downgrade() -> None:
    _drop_user_id_from_table('conversations')
    _drop_user_id_from_table('memories')
    _drop_user_id_from_table('tasks')
    _drop_user_id_from_table('entities')


def _add_user_id_to_table(table_name: str) -> None:
    with op.batch_alter_table(table_name) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.String(length=36), nullable=True))
    op.execute(
        f"UPDATE {table_name} SET user_id = (SELECT id FROM users LIMIT 1) WHERE user_id IS NULL"
    )
    with op.batch_alter_table(table_name) as batch_op:
        batch_op.alter_column('user_id', nullable=False)


def _drop_user_id_from_table(table_name: str) -> None:
    with op.batch_alter_table(table_name) as batch_op:
        batch_op.drop_column('user_id')