"""Create evaluations, subscriptions, and billing_events tables.

These tables were previously only created implicitly via
``Base.metadata.create_all`` at app startup; no Alembic migration created
them, so a fresh ``alembic upgrade head`` failed when later migrations
(e.g. 0009) referenced ``evaluations``.

Revision ID: 0006b
Revises: 0006
Create Date: 2026-08-05 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision: str = "0006b"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "evaluations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("interview_id", sa.Uuid(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("dimension_scores", JSONB(), nullable=True),
        sa.Column("hire_verdict", sa.String(20), nullable=True),
        sa.Column("strengths", JSONB(), nullable=True),
        sa.Column("improvements", JSONB(), nullable=True),
        sa.Column("delta_vs_last", sa.Float(), nullable=True),
        sa.Column("raw_evaluation", sa.Text(), nullable=True),
        sa.Column("model_used", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["interview_id"], ["interviews.id"], name=op.f("fk_evaluations_interview_id_interviews")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evaluations")),
        sa.UniqueConstraint("interview_id", name=op.f("uq_evaluations_interview_id")),
    )
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("stripe_subscription_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="incomplete"),
        sa.Column("plan", sa.String(20), nullable=True),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_subscriptions_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_subscriptions")),
        sa.UniqueConstraint("user_id", name=op.f("uq_subscriptions_user_id")),
        sa.UniqueConstraint("stripe_subscription_id", name=op.f("uq_subscriptions_stripe_subscription_id")),
    )
    op.create_table(
        "billing_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("stripe_event_id", sa.String(255), nullable=False),
        sa.Column("data", JSONB(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_billing_events_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_billing_events")),
        sa.UniqueConstraint("stripe_event_id", name=op.f("uq_billing_events_stripe_event_id")),
    )
    op.create_index(op.f("ix_billing_events_user_id"), "billing_events", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_billing_events_user_id"), table_name="billing_events")
    op.drop_table("billing_events")
    op.drop_table("subscriptions")
    op.drop_table("evaluations")
