from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.core.models import Order, OrderStatus
from app.infrastructure.unit_of_work import UnitOfWork


class PaymentCallbackDTO(BaseModel):
    payment_id: UUID
    order_id: UUID
    status: str
    amount: Decimal
    error_message: str | None = None


class OrderNotFoundError(Exception):
    pass


class ProcessPaymentCallbackUseCase:
    def __init__(self, unit_of_work: UnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    async def execute(self, data: PaymentCallbackDTO) -> Order:
        async with self._unit_of_work() as uow:
            order = await uow.orders.get_by_id(data.order_id)

            if order is None:
                raise OrderNotFoundError(f"Order with id {data.order_id} not found")

            if order.status != OrderStatus.NEW:
                return order

            if data.status == "succeeded":
                order = await uow.orders.update_status(data.order_id, OrderStatus.PAID)

            else:
                order = await uow.orders.update_status(
                    data.order_id, OrderStatus.CANCELLED
                )

            await uow.commit()
            return order
