"""Create session_events table for event sourcing and reconnection replay.

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-15 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "session_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("interview_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("payload", JSONB(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("sequence", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_session_events")),
    )
    op.create_index(op.f("ix_session_events_session_id"), "session_events", ["session_id"])
    op.create_index(op.f("ix_session_events_interview_id"), "session_events", ["interview_id"])
    op.create_index(op.f("ix_session_events_event_type"), "session_events", ["event_type"])


def downgrade() -> None:
    op.drop_index(op.f("ix_session_events_event_type"), table_name="session_events")
    op.drop_index(op.f("ix_session_events_interview_id"), table_name="session_events")
    op.drop_index(op.f("ix_session_events_session_id"), table_name="session_events")
    op.drop_table("session_events")
