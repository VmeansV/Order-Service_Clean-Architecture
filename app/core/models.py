from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class OrderStatus(StrEnum):
    NEW = "NEW"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


class Order(BaseModel):
    id: UUID
    user_id: str
    item_id: UUID
    quantity: int
    amount: Decimal
    status: OrderStatus
    idempotency_key: str
    created_at: datetime
    updated_at: datetime


class Item(BaseModel):
    id: UUID
    name: str
    price: Decimal
    available_qty: int
    created_at: datetime


class PaymentStatus(StrEnum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Payment(BaseModel):
    id: UUID
    order_id: UUID
    amount: Decimal
    status: str
    idempotency_key: str
    created_at: datetime
