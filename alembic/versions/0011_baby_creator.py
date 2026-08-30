"""track each baby's creator

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-31

Only "at least one owner remains" was enforced before, so one owner
could revoke every other owner including whoever actually created the
baby. Backfills existing babies from their earliest owner grant, since
the real creator was never recorded before this.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("babies") as batch:
        batch.add_column(sa.Column("created_by", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_babies_created_by_users",
            "users",
            ["created_by"],
            ["id"],
            ondelete="SET NULL",
        )

    conn = op.get_bind()
    babies = sa.table("babies", sa.column("id"), sa.column("created_by"))
    access = sa.table(
        "baby_access",
        sa.column("baby_id"),
        sa.column("user_id"),
        sa.column("role"),
    )
    for baby_id in conn.execute(sa.select(babies.c.id)).scalars():
        owner_id = conn.execute(
            sa.select(access.c.user_id)
            .where(access.c.baby_id == baby_id, access.c.role == "owner")
            .order_by(access.c.user_id)
            .limit(1)
        ).scalar()
        if owner_id is not None:
            conn.execute(
                babies.update()
                .where(babies.c.id == baby_id)
                .values(created_by=owner_id)
            )


def downgrade() -> None:
    with op.batch_alter_table("babies") as batch:
        batch.drop_constraint("fk_babies_created_by_users", type_="foreignkey")
        batch.drop_column("created_by")
