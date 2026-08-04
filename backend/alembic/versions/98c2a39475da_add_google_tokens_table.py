"""add_google_tokens_table

Revision ID: 98c2a39475da
Revises: 3c4d5e6f7g8h
Create Date: 2026-07-21 10:01:59.313415
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "98c2a39475da"
down_revision: Union[str, None] = "3c4d5e6f7g8h"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "google_tokens",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("encrypted_refresh_token", sa.Text(), nullable=False),
        sa.Column("scopes", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_google_tokens_user_id"), "google_tokens", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_google_tokens_user_id"), table_name="google_tokens")
    op.drop_table("google_tokens")
