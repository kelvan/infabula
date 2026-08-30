"""track who invited whom

Revision ID: 0013
Revises: 0012
Create Date: 2026-08-31

Kept on the account itself, not just derived from the Invite row (which
can be pruned/revoked later), so "who brought this person in" survives
independently of invite housekeeping.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("invited_by", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_users_invited_by_users",
            "users",
            ["invited_by"],
            ["id"],
            ondelete="SET NULL",
        )

    conn = op.get_bind()
    users = sa.table("users", sa.column("id"), sa.column("invited_by"))
    invites = sa.table(
        "invites",
        sa.column("used_by"),
        sa.column("created_by"),
    )
    for used_by, created_by in conn.execute(
        sa.select(invites.c.used_by, invites.c.created_by).where(
            invites.c.used_by.isnot(None)
        )
    ):
        conn.execute(
            users.update().where(users.c.id == used_by).values(invited_by=created_by)
        )


def downgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.drop_constraint("fk_users_invited_by_users", type_="foreignkey")
        batch.drop_column("invited_by")
