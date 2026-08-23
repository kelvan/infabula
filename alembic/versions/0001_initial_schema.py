"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-23

Mirrors the schema the pre-ORM SQLite app created by hand, so an existing
database can be stamped at this revision instead of re-created.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "entries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("ts_start", sa.String(length=32), nullable=False),
        sa.Column("ts_end", sa.String(length=32), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column("ip", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.String(length=32), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_entries_ts_start", "entries", ["ts_start"])
    op.create_table(
        "ip_names",
        sa.Column("ip", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint("ip"),
    )
    op.create_table(
        "settings",
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    op.drop_table("settings")
    op.drop_table("ip_names")
    op.drop_index("ix_entries_ts_start", table_name="entries")
    op.drop_table("entries")
