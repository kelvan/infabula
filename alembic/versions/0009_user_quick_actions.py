"""per-user quick-log button choices

Revision ID: 0009
Revises: 0008
Create Date: 2026-08-30

Was stored in the browser's localStorage, so switching devices or
browsers silently reset it. Moves it onto the account so it follows
the user everywhere.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("quick_actions", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.drop_column("quick_actions")
