"""Lock down backend-owned tables from Supabase Data API roles.

Revision ID: 0002_lock_down_public_tables
Revises: 0001_create_users
Create Date: 2026-07-15
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_lock_down_public_tables"
down_revision: str | Sequence[str] | None = "0001_create_users"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Prevent Supabase API roles from accessing backend-owned tables."""
    op.execute("ALTER TABLE public.users ENABLE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL PRIVILEGES ON TABLE public.users FROM anon, authenticated")

    op.execute("ALTER TABLE public.alembic_version ENABLE ROW LEVEL SECURITY")
    op.execute("REVOKE ALL PRIVILEGES ON TABLE public.alembic_version FROM anon, authenticated")


def downgrade() -> None:
    """Restore the original Supabase public-schema access configuration."""
    op.execute("GRANT ALL PRIVILEGES ON TABLE public.alembic_version TO anon, authenticated")
    op.execute("ALTER TABLE public.alembic_version DISABLE ROW LEVEL SECURITY")

    op.execute("GRANT ALL PRIVILEGES ON TABLE public.users TO anon, authenticated")
    op.execute("ALTER TABLE public.users DISABLE ROW LEVEL SECURITY")
