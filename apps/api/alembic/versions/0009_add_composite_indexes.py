"""Add composite indexes for common dashboard/session queries.

The following indexes are added:

======================= ===================================================
Table                   Index
======================= ===================================================
``interviews``          ``ix_interviews_user_created``
                        ON (user_id, created_at DESC)
                        — Dashboard listing: "my interviews, newest first"
``evaluations``         ``ix_evaluations_interview_created``
                        ON (interview_id, created_at DESC)
                        — Report retrieval ordered by date
``session_events``      ``ix_session_events_session_sequence``
                        ON (session_id, sequence DESC)
                        — Reconnection replay in chronological order
======================= ===================================================

These are pure index additions — zero schema or data changes.  They can be
created concurrently in production once the table is not under heavy write
load.
"""

from __future__ import annotations

from typing import ClassVar

import sqlalchemy as sa

from alembic import op

revision: str = "0009"
down_revision: ClassVar[str | None] = "0008"
branch_labels: ClassVar[str | None] = None
depends_on: ClassVar[str | None] = None


def upgrade() -> None:
    op.create_index(
        "ix_interviews_user_created",
        "interviews",
        ["user_id", sa.text("created_at DESC")],
        postgresql_concurrently=False,
    )
    op.create_index(
        "ix_evaluations_interview_created",
        "evaluations",
        ["interview_id", sa.text("created_at DESC")],
        postgresql_concurrently=False,
    )
    op.create_index(
        "ix_session_events_session_sequence",
        "session_events",
        ["session_id", sa.text("sequence DESC")],
        postgresql_concurrently=False,
    )


def downgrade() -> None:
    op.drop_index("ix_interviews_user_created", table_name="interviews")
    op.drop_index("ix_evaluations_interview_created", table_name="evaluations")
    op.drop_index("ix_session_events_session_sequence", table_name="session_events")
