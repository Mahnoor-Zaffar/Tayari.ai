"""Create user_templates table.

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-15 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_templates",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("interview_type", sa.String(20), nullable=False),
        sa.Column("company", sa.String(100), nullable=False),
        sa.Column("role", sa.String(100), nullable=False),
        sa.Column("experience_level", sa.String(20), nullable=False),
        sa.Column("language", sa.String(20), nullable=True),
        sa.Column("framework", sa.String(50), nullable=True),
        sa.Column("difficulty", sa.String(10), nullable=False, server_default="medium"),
        sa.Column("duration_minutes", sa.Integer(), nullable=False, server_default="30"),
        sa.Column("custom_instructions", sa.Text(), nullable=True),
        sa.Column("resume_id", sa.Uuid(), nullable=True),
        sa.Column("job_description_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_user_templates_user_id_users")),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"], name=op.f("fk_user_templates_resume_id_resumes")),
        sa.ForeignKeyConstraint(
            ["job_description_id"],
            ["job_descriptions.id"],
            name=op.f("fk_user_templates_job_description_id_job_descriptions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_templates")),
    )
    op.create_index(op.f("ix_user_templates_user_id"), "user_templates", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_user_templates_user_id"), table_name="user_templates")
    op.drop_table("user_templates")
