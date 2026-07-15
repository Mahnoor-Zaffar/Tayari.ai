"""Create submissions and code_reviews tables for the coding engine.

Revision ID: 0005
Revises: 0004
Create Date: 2026-07-16 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── submissions ──────────────────────────────────────────────────────
    op.create_table(
        "submissions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("interview_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("language", sa.String(20), nullable=False),
        sa.Column("source_code", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),
        sa.Column("test_results", JSONB(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("passed_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("total_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("execution_ms", sa.Integer(), nullable=True),
        sa.Column("stdout", sa.Text(), nullable=True),
        sa.Column("stderr", sa.Text(), nullable=True),
        sa.Column("compiler_output", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], name=op.f("fk_submissions_interview_id_interviews")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_submissions_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_submissions")),
    )
    op.create_index(op.f("ix_submissions_interview_id"), "submissions", ["interview_id"])
    op.create_index(op.f("ix_submissions_user_id"), "submissions", ["user_id"])
    op.create_index(op.f("ix_submissions_status"), "submissions", ["status"])

    # ── code_reviews ─────────────────────────────────────────────────────
    op.create_table(
        "code_reviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("submission_id", sa.Uuid(), nullable=False),
        sa.Column("interview_id", sa.Uuid(), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=True),
        sa.Column("dimensions", JSONB(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("strengths", JSONB(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("improvements", JSONB(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("line_comments", JSONB(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("raw_review", sa.Text(), nullable=True),
        sa.Column("model_used", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["submission_id"], ["submissions.id"], name=op.f("fk_code_reviews_submission_id_submissions")),
        sa.ForeignKeyConstraint(["interview_id"], ["interviews.id"], name=op.f("fk_code_reviews_interview_id_interviews")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_code_reviews")),
        sa.UniqueConstraint("submission_id", name=op.f("uq_code_reviews_submission_id")),
    )
    op.create_index(op.f("ix_code_reviews_submission_id"), "code_reviews", ["submission_id"])
    op.create_index(op.f("ix_code_reviews_interview_id"), "code_reviews", ["interview_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_code_reviews_interview_id"), table_name="code_reviews")
    op.drop_index(op.f("ix_code_reviews_submission_id"), table_name="code_reviews")
    op.drop_table("code_reviews")
    op.drop_index(op.f("ix_submissions_status"), table_name="submissions")
    op.drop_index(op.f("ix_submissions_user_id"), table_name="submissions")
    op.drop_index(op.f("ix_submissions_interview_id"), table_name="submissions")
    op.drop_table("submissions")
