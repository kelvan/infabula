"""per-baby default bottle content

Revision ID: 0014
Revises: 0013
Create Date: 2026-09-02

Preselects pumped milk vs formula on the bottle entry so a household
that only ever gives one doesn't pick it every time. Null keeps the
picker on its first option, which is what every existing baby gets.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("babies") as batch:
        batch.add_column(
            sa.Column("bottle_default_content", sa.String(length=16), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("babies") as batch:
        batch.drop_column("bottle_default_content")
