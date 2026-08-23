"""drop the duplicated birthday setting

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-23

0002 copied the global 'birthday' setting onto the baby row. Keeping both
would let them drift apart, so the setting is dropped and the baby record
becomes the only place a birthday lives.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# "key" is reserved in MySQL, so go through the expression language to get
# per-dialect quoting instead of hand-written SQL.
settings = sa.table("settings", sa.column("key"), sa.column("value"))
babies = sa.table("babies", sa.column("id"), sa.column("birthday"))


def upgrade() -> None:
    op.get_bind().execute(settings.delete().where(settings.c.key == "birthday"))


def downgrade() -> None:
    conn = op.get_bind()
    birthday = conn.execute(
        sa.select(babies.c.birthday).order_by(babies.c.id).limit(1)
    ).scalar()
    if birthday:
        conn.execute(settings.insert().values(key="birthday", value=birthday))
