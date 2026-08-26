"""admin flag, disabled flag, email verification

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-26

Hardens open registration: new accounts must click a link sent to their
address before they can log in. Existing accounts are grandfathered in
as already verified — they were already trusted household members, not
strangers registration is meant to slow down. The earliest account that
can actually log in (has a password set) becomes the first admin, since
nothing else can grant that role once this migration is the only way
in — id 1 is not necessarily it: a database predating real accounts
seeds a placeholder row at id 1 with no password, which would otherwise
become an unusable "admin" while the real account stays a regular user.

``disabled`` lets an admin lock an account out without deleting its
journal history.
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch:
        batch.add_column(
            sa.Column(
                "email_verified",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch.add_column(
            sa.Column(
                "disabled", sa.Boolean(), nullable=False, server_default=sa.false()
            )
        )
        batch.add_column(
            sa.Column(
                "is_admin", sa.Boolean(), nullable=False, server_default=sa.false()
            )
        )

    users = sa.table(
        "users",
        sa.column("id"),
        sa.column("password_hash"),
        sa.column("email_verified"),
        sa.column("is_admin"),
    )
    conn = op.get_bind()
    conn.execute(users.update().values(email_verified=True))
    first_real_user = conn.execute(
        sa.select(users.c.id)
        .where(users.c.password_hash.is_not(None))
        .order_by(users.c.id)
        .limit(1)
    ).scalar()
    if first_real_user is not None:
        conn.execute(
            users.update().where(users.c.id == first_real_user).values(is_admin=True)
        )

    op.create_table(
        "email_verifications",
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.String(length=32), nullable=True),
        sa.Column("expires_at", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("token"),
    )
    op.create_index(
        "ix_email_verifications_user_id", "email_verifications", ["user_id"]
    )


def downgrade() -> None:
    op.drop_index(
        "ix_email_verifications_user_id", table_name="email_verifications"
    )
    op.drop_table("email_verifications")
    with op.batch_alter_table("users") as batch:
        batch.drop_column("is_admin")
        batch.drop_column("disabled")
        batch.drop_column("email_verified")
