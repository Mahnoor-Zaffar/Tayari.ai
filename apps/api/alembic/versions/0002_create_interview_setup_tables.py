"""Create interview setup tables.

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-14 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── interview_templates ──────────────────────────────────────────────
    op.create_table(
        "interview_templates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("interview_type", sa.String(20), nullable=False),
        sa.Column("default_company", sa.String(100), nullable=True),
        sa.Column("default_role", sa.String(100), nullable=True),
        sa.Column("default_experience_level", sa.String(20), nullable=True),
        sa.Column("default_language", sa.String(20), nullable=True),
        sa.Column("default_framework", sa.String(50), nullable=True),
        sa.Column("default_difficulty", sa.String(10), nullable=False, server_default="medium"),
        sa.Column("default_duration_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("default_instructions", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_interview_templates")),
        sa.UniqueConstraint("name", name=op.f("uq_interview_templates_name")),
    )

    # ── resumes ──────────────────────────────────────────────────────────
    op.create_table(
        "resumes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("storage_path", sa.String(512), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=False),
        sa.Column("parsed_content", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_resumes_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_resumes")),
    )
    op.create_index(op.f("ix_resumes_user_id"), "resumes", ["user_id"])
    op.create_index(op.f("ix_resumes_file_hash"), "resumes", ["file_hash"])

    # ── job_descriptions ─────────────────────────────────────────────────
    op.create_table(
        "job_descriptions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False, server_default=""),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("storage_path", sa.String(512), nullable=True),
        sa.Column("file_hash", sa.String(64), nullable=False, server_default=""),
        sa.Column("raw_content", sa.Text(), nullable=False, server_default=""),
        sa.Column("parsed_content", sa.Text(), nullable=True),
        sa.Column("source", sa.String(20), nullable=False, server_default="text"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_job_descriptions_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_job_descriptions")),
    )
    op.create_index(op.f("ix_job_descriptions_user_id"), "job_descriptions", ["user_id"])
    op.create_index(op.f("ix_job_descriptions_file_hash"), "job_descriptions", ["file_hash"])

    # ── interview_configurations ─────────────────────────────────────────
    op.create_table(
        "interview_configurations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("interview_type", sa.String(20), nullable=False),
        sa.Column("company", sa.String(100), nullable=False),
        sa.Column("role", sa.String(100), nullable=False, server_default=""),
        sa.Column("experience_level", sa.String(20), nullable=False),
        sa.Column("language", sa.String(20), nullable=True),
        sa.Column("framework", sa.String(50), nullable=True),
        sa.Column("difficulty", sa.String(10), nullable=False, server_default="medium"),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("custom_instructions", sa.Text(), nullable=True),
        sa.Column("device_checks", JSONB(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_interview_configurations_user_id_users")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_interview_configurations")),
    )
    op.create_index(op.f("ix_interview_configurations_user_id"), "interview_configurations", ["user_id"])

    # ── interviews (created fresh with all columns) ──────────────────────
    op.create_table(
        "interviews",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("company", sa.String(100), nullable=False),
        sa.Column("role", sa.String(100), nullable=False, server_default=""),
        sa.Column("experience_level", sa.String(20), nullable=False),
        sa.Column("language", sa.String(20), nullable=True),
        sa.Column("difficulty", sa.String(10), nullable=False, server_default="medium"),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("framework", sa.String(50), nullable=True),
        sa.Column("custom_instructions", sa.Text(), nullable=True),
        sa.Column("resume_id", sa.Uuid(), nullable=True),
        sa.Column("job_description_id", sa.Uuid(), nullable=True),
        sa.Column("template_id", sa.Uuid(), nullable=True),
        sa.Column("configuration_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("timer_remaining", sa.Integer(), nullable=False, server_default="1800"),
        sa.Column("transcript", JSONB(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("ai_messages", JSONB(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_interviews_user_id_users")),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], name=op.f("fk_interviews_resume_id_resumes")),
        sa.ForeignKeyConstraint(
            ["job_description_id"],
            ["job_descriptions.id"],
            name=op.f("fk_interviews_job_description_id_job_descriptions"),
        ),
        sa.ForeignKeyConstraint(
            ["template_id"],
            ["interview_templates.id"],
            name=op.f("fk_interviews_template_id_interview_templates"),
        ),
        sa.ForeignKeyConstraint(
            ["configuration_id"],
            ["interview_configurations.id"],
            name=op.f("fk_interviews_configuration_id_interview_configurations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_interviews")),
    )
    op.create_index(op.f("ix_interviews_user_id"), "interviews", ["user_id"])
    op.create_index(op.f("ix_interviews_status"), "interviews", ["status"])


def downgrade() -> None:
    op.drop_index(op.f("ix_interviews_status"), table_name="interviews")
    op.drop_index(op.f("ix_interviews_user_id"), table_name="interviews")
    op.drop_table("interviews")

    op.drop_index(op.f("ix_interview_configurations_user_id"), table_name="interview_configurations")
    op.drop_table("interview_configurations")

    op.drop_index(op.f("ix_job_descriptions_file_hash"), table_name="job_descriptions")
    op.drop_index(op.f("ix_job_descriptions_user_id"), table_name="job_descriptions")
    op.drop_table("job_descriptions")

    op.drop_index(op.f("ix_resumes_file_hash"), table_name="resumes")
    op.drop_index(op.f("ix_resumes_user_id"), table_name="resumes")
    op.drop_table("resumes")

    op.drop_table("interview_templates")
