from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class CreateOrderRequest(BaseModel):
    user_id: str
    quantity: int = Field(gt=0)
    item_id: UUID
    idempotency_key: str


class OrderResponse(BaseModel):
    id: UUID
    user_id: str
    quantity: int
    item_id: UUID
    status: str
    created_at: datetime
    updated_at: datetime


class PaymentCallbackRequest(BaseModel):
    payment_id: UUID
    order_id: UUID
    status: str
    amount: Decimal
    error_message: str | None = None
