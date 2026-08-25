"""track last login

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-25

Registration and TOTP setup already stamp created_at; this adds the other
half — when an account last actually logged in — updated on every
password, TOTP, and passkey login.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(
            sa.Column("last_login_at", sa.String(length=32), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.drop_column("last_login_at")
