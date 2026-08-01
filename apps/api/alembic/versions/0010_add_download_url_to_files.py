"""Add download_url column to resumes and job_descriptions.

Enables pre-signed download URLs for uploaded files without exposing
the underlying storage path to the client.
"""

from __future__ import annotations

from typing import ClassVar

import sqlalchemy as sa

from alembic import op

revision: str = "0010"
down_revision: ClassVar[str | None] = "0009"
branch_labels: ClassVar[str | None] = None
depends_on: ClassVar[str | None] = None


def upgrade() -> None:
    op.add_column("resumes", sa.Column("download_url", sa.String(2048), nullable=True))
    op.add_column("job_descriptions", sa.Column("download_url", sa.String(2048), nullable=True))


def downgrade() -> None:
    op.drop_column("resumes", "download_url")
    op.drop_column("job_descriptions", "download_url")
