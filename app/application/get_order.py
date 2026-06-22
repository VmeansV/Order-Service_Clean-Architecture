from uuid import UUID

from app.application.interfaces import AbstractUnitOfWork
from app.core.models import Order


class OrderNotFoundError(Exception):
    pass


class GetOrderUseCase:
    def __init__(self, unit_of_work: AbstractUnitOfWork) -> None:
        self._unit_of_work = unit_of_work

    async def execute(self, order_id: UUID) -> Order:
        async with self._unit_of_work() as uow:
            order = await uow.orders.get_by_id(order_id)

            if order is None:
                raise OrderNotFoundError(f"Order with id {order_id} not found")

            return order
