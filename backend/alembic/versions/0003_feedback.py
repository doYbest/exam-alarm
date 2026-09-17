"""Anonymous feedback events.

Revision ID: 0003_feedback
Revises: 0002_content
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "0003_feedback"
down_revision: str | None = "0002_content"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_feedback",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("client_event_id", UUID(as_uuid=True), unique=True, nullable=False),
        sa.Column(
            "hotspot_id", UUID(as_uuid=True), sa.ForeignKey("hotspot_events.id"), nullable=False
        ),
        sa.Column("event_type", sa.String(20), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("install_id_hash", sa.String(64)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_table("user_feedback")
