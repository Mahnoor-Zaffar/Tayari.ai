from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SubscriptionResponse(BaseModel):
    id: UUID
    status: str
    plan: str | None = None
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    created_at: datetime


class CreateCheckoutRequest(BaseModel):
    price_id: str
    success_url: str
    cancel_url: str
