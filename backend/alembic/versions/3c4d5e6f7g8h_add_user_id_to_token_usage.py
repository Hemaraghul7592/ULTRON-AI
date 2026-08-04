"""add_user_id_to_token_usage

Revision ID: 3c4d5e6f7g8h
Revises: 2a3b4c5d6e7f
Create Date: 2026-07-20 20:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3c4d5e6f7g8h"
down_revision: Union[str, None] = "7496ccf83cb6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("token_usage", sa.Column("user_id", sa.String(36), nullable=True))
    op.create_index("ix_token_usage_user", "token_usage", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_token_usage_user", table_name="token_usage")
    op.drop_column("token_usage", "user_id")
