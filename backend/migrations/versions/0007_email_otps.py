"""Add email_otps (one-time codes that verify an email before registration).

Revision ID: 0007_email_otps
Revises: 0006_oauth_identities
Create Date: 2026-11-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_email_otps"
down_revision: str | Sequence[str] | None = "0006_oauth_identities"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_supabase_roles() -> bool:
    """anon/authenticated exist only on Supabase; plain PostgreSQL has neither."""
    if op.get_context().as_sql:
        return True  # offline SQL generation cannot query the server
    found = op.get_bind().execute(
        sa.text("SELECT count(*) FROM pg_roles WHERE rolname IN ('anon', 'authenticated')")
    )
    return found.scalar() == 2


def upgrade() -> None:
    op.create_table(
        "email_otps",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_email_otps_email", "email_otps", ["email"])

    if not _has_supabase_roles():
        return

    op.execute("ALTER TABLE public.email_otps ENABLE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL PRIVILEGES ON TABLE public.email_otps FROM anon, authenticated")


def downgrade() -> None:
    op.drop_index("ix_email_otps_email", table_name="email_otps")
    op.drop_table("email_otps")
