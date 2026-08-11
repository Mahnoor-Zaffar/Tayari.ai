"""Create ai_usage table for model gateway telemetry.

Revision ID: 0012
Revises: 0011
Create Date: 2026-08-11 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ai_usage",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("task", sa.String(30), nullable=False),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("model", sa.String(80), nullable=False),
        sa.Column("prompt_version", sa.String(30), nullable=True),
        sa.Column("interview_id", sa.Uuid(), nullable=True),
        sa.Column("session_id", sa.Uuid(), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("estimated_cost_cents", sa.Float(), nullable=True),
        sa.Column("is_error", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_ai_usage")),
    )
    op.create_index(op.f("ix_ai_usage_created_at"), "ai_usage", ["created_at"])
    op.create_index(op.f("ix_ai_usage_task"), "ai_usage", ["task"])
    op.create_index(op.f("ix_ai_usage_model"), "ai_usage", ["model"])


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_usage_model"), table_name="ai_usage")
    op.drop_index(op.f("ix_ai_usage_task"), table_name="ai_usage")
    op.drop_index(op.f("ix_ai_usage_created_at"), table_name="ai_usage")
    op.drop_table("ai_usage")
