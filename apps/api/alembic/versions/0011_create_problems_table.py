"""Create problems table, link submissions, and seed coding problems.

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-06 12:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── problems ────────────────────────────────────────────────────────
    op.create_table(
        "problems",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("difficulty", sa.String(20), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("examples", JSONB(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("constraints", JSONB(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("test_cases", JSONB(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_problems")),
        sa.UniqueConstraint("slug", name=op.f("uq_problems_slug")),
    )
    op.create_index(op.f("ix_problems_slug"), "problems", ["slug"])

    # ── submissions.problem_id ──────────────────────────────────────────
    op.add_column("submissions", sa.Column("problem_id", sa.Uuid(), nullable=True))
    op.create_index(op.f("ix_submissions_problem_id"), "submissions", ["problem_id"])
    op.create_foreign_key(
        op.f("fk_submissions_problem_id_problems"),
        "submissions",
        "problems",
        ["problem_id"],
        ["id"],
    )

    # ── seed coding problems ────────────────────────────────────────────
    from features.code.seed_data import SEED_PROBLEMS

    problems_table = sa.table(
        "problems",
        sa.column("id", sa.Uuid()),
        sa.column("slug", sa.String(80)),
        sa.column("title", sa.String(200)),
        sa.column("difficulty", sa.String(20)),
        sa.column("description", sa.Text()),
        sa.column("examples", JSONB()),
        sa.column("constraints", JSONB()),
        sa.column("test_cases", JSONB()),
    )
    op.bulk_insert(problems_table, [dict(p) for p in SEED_PROBLEMS])


def downgrade() -> None:
    op.drop_constraint(op.f("fk_submissions_problem_id_problems"), "submissions", type_="foreignkey")
    op.drop_index(op.f("ix_submissions_problem_id"), table_name="submissions")
    op.drop_column("submissions", "problem_id")
    op.drop_index(op.f("ix_problems_slug"), table_name="problems")
    op.drop_table("problems")
