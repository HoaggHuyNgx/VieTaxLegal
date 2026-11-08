"""Add oauth_identities (Google sign-in) and let users.password_hash be null.

Revision ID: 0006_oauth_identities
Revises: 0005_roles_refresh_tokens
Create Date: 2026-11-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_oauth_identities"
down_revision: str | Sequence[str] | None = "0005_roles_refresh_tokens"
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
    with op.batch_alter_table("users") as batch:
        batch.alter_column("password_hash", existing_type=sa.String(255), nullable=True)

    op.create_table(
        "oauth_identities",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("provider", "subject", name="uq_oauth_identities_provider_subject"),
        sa.UniqueConstraint("user_id", "provider", name="uq_oauth_identities_user_provider"),
    )
    op.create_index("ix_oauth_identities_user_id", "oauth_identities", ["user_id"])

    if not _has_supabase_roles():
        return

    op.execute("ALTER TABLE public.oauth_identities ENABLE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL PRIVILEGES ON TABLE public.oauth_identities FROM anon, authenticated")


def downgrade() -> None:
    op.drop_index("ix_oauth_identities_user_id", table_name="oauth_identities")
    op.drop_table("oauth_identities")
    # Google-only accounts have no password, so they must go before the column is NOT NULL again.
    op.execute("DELETE FROM users WHERE password_hash IS NULL")
    with op.batch_alter_table("users") as batch:
        batch.alter_column("password_hash", existing_type=sa.String(255), nullable=False)
