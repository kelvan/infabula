"""password/TOTP/passkey auth

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-25

Adds login credentials to users (username, password hash, optional TOTP),
a table for registered passkeys, and a table for login sessions. The
existing placeholder user (id=1) predates login and is left without
credentials — it stays around only as the author of pre-auth entries;
real accounts are created fresh via registration.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(sa.Column("username", sa.String(length=64), nullable=True))
        batch.add_column(
            sa.Column("password_hash", sa.String(length=255), nullable=True)
        )
        batch.add_column(sa.Column("totp_secret", sa.String(length=64), nullable=True))
        batch.add_column(
            sa.Column(
                "totp_enabled", sa.Boolean(), nullable=False, server_default=sa.false()
            )
        )

    users = sa.table("users", sa.column("id"), sa.column("username"))
    op.get_bind().execute(
        users.update().where(users.c.id == 1).values(username="legacy")
    )

    with op.batch_alter_table("users") as batch:
        batch.create_unique_constraint("uq_users_username", ["username"])

    op.create_table(
        "webauthn_credentials",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("credential_id", sa.String(length=255), nullable=False),
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column("sign_count", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("credential_id"),
    )
    op.create_index(
        "ix_webauthn_credentials_user_id", "webauthn_credentials", ["user_id"]
    )

    op.create_table(
        "sessions",
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.String(length=32), nullable=True),
        sa.Column("expires_at", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("token"),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_sessions_user_id", table_name="sessions")
    op.drop_table("sessions")
    op.drop_index("ix_webauthn_credentials_user_id", table_name="webauthn_credentials")
    op.drop_table("webauthn_credentials")
    with op.batch_alter_table("users") as batch:
        batch.drop_constraint("uq_users_username", type_="unique")
        batch.drop_column("totp_enabled")
        batch.drop_column("totp_secret")
        batch.drop_column("password_hash")
        batch.drop_column("username")
