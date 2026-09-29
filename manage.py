"""CLI for creating and managing user accounts.

Run inside the deployed container so it shares the real DB_URL/DB_PATH:

    podman exec -it systemd-infabula uv run python manage.py create a@example.com
    podman exec -it systemd-infabula uv run python manage.py list
"""

import argparse
import asyncio
import getpass
import sys

from sqlalchemy import delete, select, update

import auth
from db import (
    ROLE_OWNER,
    Baby,
    BabyAccess,
    Entry,
    Session,
    User,
)


def prompt_password() -> str:
    while True:
        password = getpass.getpass("Password: ")
        if len(password) < 8:
            print("Password must be at least 8 characters.", file=sys.stderr)
            continue
        if getpass.getpass("Confirm password: ") != password:
            print("Passwords did not match.", file=sys.stderr)
            continue
        return password


async def cmd_create(args: argparse.Namespace) -> None:
    email = args.email.strip().lower()
    password = args.password or prompt_password()
    async with Session() as session:
        existing = await session.scalar(select(User).where(User.username == email))
        if existing is not None:
            print(f"Account already exists: {email}", file=sys.stderr)
            raise SystemExit(1)
    async with Session.begin() as session:
        user = User(
            name=args.name or email,
            username=email,
            email=email,
            password_hash=auth.hash_password(password),
            email_verified=True,
            is_admin=args.admin,
        )
        session.add(user)
        await session.flush()
        print(f"Created user {user.id} ({email}){' [admin]' if args.admin else ''}")


async def cmd_list(_args: argparse.Namespace) -> None:
    async with Session() as session:
        rows = (await session.scalars(select(User).order_by(User.id))).all()
    if not rows:
        print("No users.")
        return
    print(
        f"{'ID':<4} {'EMAIL':<30} {'NAME':<20} {'ADMIN':<6} "
        f"{'DISABLED':<9} {'VERIFIED':<9} CREATED"
    )
    for u in rows:
        print(
            f"{u.id:<4} {(u.email or ''):<30} {(u.name or ''):<20} "
            f"{'yes' if u.is_admin else '':<6} {'yes' if u.disabled else '':<9} "
            f"{'yes' if u.email_verified else '':<9} {u.created_at or ''}"
        )


async def _get_user_by_email(email: str) -> User | None:
    async with Session() as session:
        return await session.scalar(
            select(User).where(User.username == email.strip().lower())
        )


async def cmd_disable(args: argparse.Namespace) -> None:
    user = await _get_user_by_email(args.email)
    if user is None:
        print(f"No such user: {args.email}", file=sys.stderr)
        raise SystemExit(1)
    async with Session.begin() as session:
        row = await session.get(User, user.id)
        assert row is not None
        row.disabled = True
    await auth.kill_sessions_for_user(user.id)
    print(f"Disabled {args.email} (sessions and API tokens revoked)")


async def cmd_enable(args: argparse.Namespace) -> None:
    user = await _get_user_by_email(args.email)
    if user is None:
        print(f"No such user: {args.email}", file=sys.stderr)
        raise SystemExit(1)
    async with Session.begin() as session:
        row = await session.get(User, user.id)
        assert row is not None
        row.disabled = False
    print(f"Enabled {args.email}")


async def cmd_set_admin(args: argparse.Namespace) -> None:
    user = await _get_user_by_email(args.email)
    if user is None:
        print(f"No such user: {args.email}", file=sys.stderr)
        raise SystemExit(1)
    async with Session.begin() as session:
        row = await session.get(User, user.id)
        assert row is not None
        row.is_admin = not args.off
    print(f"{'Revoked' if args.off else 'Granted'} admin for {args.email}")


async def cmd_set_password(args: argparse.Namespace) -> None:
    user = await _get_user_by_email(args.email)
    if user is None:
        print(f"No such user: {args.email}", file=sys.stderr)
        raise SystemExit(1)
    password = args.password or prompt_password()
    async with Session.begin() as session:
        row = await session.get(User, user.id)
        assert row is not None
        row.password_hash = auth.hash_password(password)
    await auth.kill_sessions_for_user(user.id)
    print(f"Password changed for {args.email} (existing sessions revoked)")


async def cmd_delete(args: argparse.Namespace) -> None:
    user = await _get_user_by_email(args.email)
    if user is None:
        print(f"No such user: {args.email}", file=sys.stderr)
        raise SystemExit(1)
    async with Session() as session:
        owned = (
            await session.scalars(
                select(BabyAccess.baby_id).where(
                    BabyAccess.user_id == user.id, BabyAccess.role == ROLE_OWNER
                )
            )
        ).all()
        solely_owned = []
        for baby_id in owned:
            other_owner = await session.scalar(
                select(BabyAccess).where(
                    BabyAccess.baby_id == baby_id,
                    BabyAccess.role == ROLE_OWNER,
                    BabyAccess.user_id != user.id,
                )
            )
            if other_owner is None:
                baby = await session.get(Baby, baby_id)
                solely_owned.append(baby.name if baby else str(baby_id))
    if solely_owned:
        print(
            "Refusing to delete: sole owner of "
            + ", ".join(solely_owned)
            + " — transfer or delete these babies first.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    if not args.yes:
        confirm = input(f"Type the email to confirm deleting {args.email}: ")
        if confirm.strip().lower() != args.email.strip().lower():
            print("Aborted.", file=sys.stderr)
            raise SystemExit(1)

    async with Session.begin() as session:
        await auth.delete_auth_records_for_user(session, user.id)
        await session.execute(delete(BabyAccess).where(BabyAccess.user_id == user.id))
        await session.execute(
            update(Entry).where(Entry.user_id == user.id).values(user_id=None)
        )
        await session.execute(delete(User).where(User.id == user.id))
    print(f"Deleted {args.email}")


async def cmd_vapid(_args: argparse.Namespace) -> None:
    import base64

    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import ec

    key = ec.generate_private_key(ec.SECP256R1())
    raw = key.private_numbers().private_value.to_bytes(32, "big")
    priv = base64.urlsafe_b64encode(raw).rstrip(b"=").decode()
    pub = base64.urlsafe_b64encode(
        key.public_key().public_bytes(
            serialization.Encoding.X962,
            serialization.PublicFormat.UncompressedPoint,
        )
    ).rstrip(b"=").decode()
    print("# rhythm-reminder push keys — set these in the container environment")
    print(f"VAPID_PRIVATE_KEY={priv}")
    print(f"VAPID_PUBLIC_KEY={pub}")
    print("VAPID_CLAIM_EMAIL=mailto:you@example.com")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage infabula user accounts")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("create", help="Create a new account")
    p.add_argument("email")
    p.add_argument("--name", help="Display name (defaults to the email)")
    p.add_argument(
        "--password", help="Skip the interactive prompt (visible in shell history)"
    )
    p.add_argument("--admin", action="store_true", help="Grant admin from the start")
    p.set_defaults(func=cmd_create)

    p = sub.add_parser("list", help="List all accounts")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser(
        "disable", help="Disable an account and revoke its sessions/tokens"
    )
    p.add_argument("email")
    p.set_defaults(func=cmd_disable)

    p = sub.add_parser("enable", help="Re-enable a disabled account")
    p.add_argument("email")
    p.set_defaults(func=cmd_enable)

    p = sub.add_parser("set-admin", help="Grant or revoke admin")
    p.add_argument("email")
    p.add_argument(
        "--off", action="store_true", help="Revoke admin instead of granting it"
    )
    p.set_defaults(func=cmd_set_admin)

    p = sub.add_parser("set-password", help="Reset an account's password")
    p.add_argument("email")
    p.add_argument(
        "--password", help="Skip the interactive prompt (visible in shell history)"
    )
    p.set_defaults(func=cmd_set_password)

    p = sub.add_parser("delete", help="Permanently delete an account")
    p.add_argument("email")
    p.add_argument("--yes", action="store_true", help="Skip the confirmation prompt")
    p.set_defaults(func=cmd_delete)

    p = sub.add_parser("vapid", help="Generate Web Push (rhythm reminder) keys")
    p.set_defaults(func=cmd_vapid)

    args = parser.parse_args()
    asyncio.run(args.func(args))


if __name__ == "__main__":
    main()
