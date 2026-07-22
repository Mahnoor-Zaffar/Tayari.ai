"""Add system_design_problem column to interviews and interview_configurations.

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-22 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "interviews",
        sa.Column("system_design_problem", sa.Text(), nullable=True),
    )
    op.add_column(
        "interview_configurations",
        sa.Column("system_design_problem", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("interview_configurations", "system_design_problem")
    op.drop_column("interviews", "system_design_problem")
