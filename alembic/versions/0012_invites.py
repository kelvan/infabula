"""invite-only registration

Revision ID: 0012
Revises: 0011
Create Date: 2026-08-31

Lets an admin invite someone who can then register even while open
signup is closed or they're off-LAN — the flow the README promised
back when REGISTRATION_ENABLED was added.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "invites",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("token_hash", sa.String(64), nullable=False, unique=True),
        sa.Column("prefix", sa.String(16), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column(
            "created_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.String(32), nullable=True),
        sa.Column("expires_at", sa.String(32), nullable=False),
        sa.Column("used_at", sa.String(32), nullable=True),
        sa.Column(
            "used_by",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("invites")
