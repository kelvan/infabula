"""users, babies and per-baby access

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-23

Introduces the data model for multiple users sharing a baby's log. Nothing
authenticates yet: a placeholder user and baby are created and every existing
entry is attached to them, so the app keeps behaving as a single-baby journal.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_USER_ID = 1
DEFAULT_BABY_ID = 1


def upgrade() -> None:
    users = op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.String(length=32), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    babies = op.create_table(
        "babies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("birthday", sa.String(length=10), nullable=True),
        sa.Column("created_at", sa.String(length=32), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    access = op.create_table(
        "baby_access",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("baby_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["baby_id"], ["babies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "baby_id"),
    )

    conn = op.get_bind()

    # Carry the birthday the app already stored globally over to the baby.
    # Built via the expression language so "key" — reserved in MySQL — gets
    # quoted the way each backend expects.
    settings = sa.table("settings", sa.column("key"), sa.column("value"))
    birthday = conn.execute(
        sa.select(settings.c.value).where(settings.c.key == "birthday")
    ).scalar()

    op.bulk_insert(
        users,
        [{"id": DEFAULT_USER_ID, "name": "Default user", "email": None}],
    )
    op.bulk_insert(
        babies,
        [{"id": DEFAULT_BABY_ID, "name": "Baby", "birthday": birthday}],
    )
    op.bulk_insert(
        access,
        [{"user_id": DEFAULT_USER_ID, "baby_id": DEFAULT_BABY_ID, "role": "owner"}],
    )

    # Add the entry columns nullable first so existing rows can be backfilled,
    # then tighten baby_id to NOT NULL.
    with op.batch_alter_table("entries") as batch:
        batch.add_column(sa.Column("baby_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("user_id", sa.Integer(), nullable=True))

    entries = sa.table("entries", sa.column("baby_id"))
    conn.execute(entries.update().values(baby_id=DEFAULT_BABY_ID))

    with op.batch_alter_table("entries") as batch:
        batch.alter_column("baby_id", existing_type=sa.Integer(), nullable=False)
        batch.create_foreign_key(
            "fk_entries_baby", "babies", ["baby_id"], ["id"], ondelete="CASCADE"
        )
        batch.create_foreign_key("fk_entries_user", "users", ["user_id"], ["id"])
        batch.create_index("ix_entries_baby_id", ["baby_id"])
        batch.create_index("ix_entries_user_id", ["user_id"])


def downgrade() -> None:
    with op.batch_alter_table("entries") as batch:
        batch.drop_index("ix_entries_user_id")
        batch.drop_index("ix_entries_baby_id")
        batch.drop_constraint("fk_entries_user", type_="foreignkey")
        batch.drop_constraint("fk_entries_baby", type_="foreignkey")
        batch.drop_column("user_id")
        batch.drop_column("baby_id")
    op.drop_table("baby_access")
    op.drop_table("babies")
    op.drop_table("users")
