import logging
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.core.models import Order, OrderStatus
from app.infrastructure.http_clients import (
    NotificationServiceClient,
    NotificationServiceError,
)
from app.infrastructure.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class PaymentCallbackDTO(BaseModel):
    payment_id: UUID
    order_id: UUID
    status: str
    amount: Decimal
    error_message: str | None = None


class OrderNotFoundError(Exception):
    pass


class ProcessPaymentCallbackUseCase:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        notifications_client: NotificationServiceClient,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._notifications_client = notifications_client

    async def execute(self, data: PaymentCallbackDTO) -> Order:
        async with self._unit_of_work() as uow:
            order = await uow.orders.get_by_id(data.order_id)

            if order is None:
                raise OrderNotFoundError(f"Order with id {data.order_id} not found")

            if order.status != OrderStatus.NEW:
                return order

            if data.status == "succeeded":
                order = await uow.orders.update_status(data.order_id, OrderStatus.PAID)

                await uow.outbox.create(
                    event_type="order.paid",
                    payload={
                        "event_type": "order.paid",
                        "order_id": str(order.id),
                        "item_id": str(order.item_id),
                        "quantity": order.quantity,
                        "idempotency_key": order.idempotency_key,
                    },
                )

            else:
                order = await uow.orders.update_status(
                    data.order_id, OrderStatus.CANCELLED
                )

            await uow.commit()

        try:
            if data.status == "succeeded":
                await self._notifications_client.send_notification(
                    message="Ваш заказ успешно оплачен и готов к отправке",
                    reference_id=str(order.id),
                    idempotency_key=f"{order.id}:PAID",
                )
            else:
                reason = data.error_message or "Payment failed"
                await self._notifications_client.send_notification(
                    message=f"Ваше заказ отменен. Причина: {reason}",
                    reference_id=str(order.id),
                    idempotency_key=f"{order.id}:CANCELLED:payment",
                )
        except NotificationServiceError as exc:
            logger.error(f"Failed to send notification: {exc}")

        return order
