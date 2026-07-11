import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    interview_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("interviews.id"), nullable=False, unique=True
    )
    overall_score: Mapped[float] = mapped_column(nullable=True)
    dimension_scores: Mapped[dict] = mapped_column(JSONB, default=dict)
    hire_verdict: Mapped[str] = mapped_column(String(20), nullable=True)
    strengths: Mapped[dict] = mapped_column(JSONB, default=list)
    improvements: Mapped[dict] = mapped_column(JSONB, default=list)
    delta_vs_last: Mapped[float] = mapped_column(nullable=True)
    raw_evaluation: Mapped[str] = mapped_column(Text, nullable=True)
    model_used: Mapped[str] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    interview = relationship("Interview", back_populates="evaluation")
