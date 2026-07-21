"""Add spoken_language column to interviews and interview_configurations.

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-18 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "interviews",
        sa.Column("spoken_language", sa.String(10), nullable=True, server_default="en"),
    )
    op.add_column(
        "interview_configurations",
        sa.Column("spoken_language", sa.String(10), nullable=True, server_default="en"),
    )


def downgrade() -> None:
    op.drop_column("interview_configurations", "spoken_language")
    op.drop_column("interviews", "spoken_language")
