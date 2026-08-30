"""per-baby nap threshold

Revision ID: 0010
Revises: 0009
Create Date: 2026-08-30

The nap/night-sleep split in stats was a fixed 240-minute constant for
every baby. Moves it onto each baby, since newborns sleep in short
bursts around the clock and the right cutoff rises as they mature.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("babies") as batch:
        batch.add_column(
            sa.Column(
                "nap_threshold_min",
                sa.Integer(),
                nullable=False,
                server_default="240",
            )
        )


def downgrade() -> None:
    with op.batch_alter_table("babies") as batch:
        batch.drop_column("nap_threshold_min")
