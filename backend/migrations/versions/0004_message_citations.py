"""Add messages.citations (snapshot of RAG sources shown with an answer).

Revision ID: 0004_message_citations
Revises: 0003_chat
Create Date: 2026-10-11
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_message_citations"
down_revision: str | Sequence[str] | None = "0003_chat"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("messages", sa.Column("citations", sa.JSON(none_as_null=True), nullable=True))


def downgrade() -> None:
    op.drop_column("messages", "citations")
