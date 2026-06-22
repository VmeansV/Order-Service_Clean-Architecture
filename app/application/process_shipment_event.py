import logging
from uuid import UUID

from pydantic import BaseModel

from app.application.interfaces import (
    AbstractNotificationClient,
    AbstractUnitOfWork,
)
from app.core.models import Order, OrderStatus
from app.infrastructure.http_clients import (
    NotificationServiceError,
)

logger = logging.getLogger(__name__)


class ShipmentEventDTO(BaseModel):
    event_id: UUID
    event_type: str
    order_id: UUID
    item_id: UUID
    quantity: int
    shipment_id: UUID | None = None
    reason: str | None = None


class OrderNotFoundError(Exception):
    pass


class UnknownEventTypeError(Exception):
    pass


class ProcessShipmentEventUseCase:
    def __init__(
        self,
        unit_of_work: AbstractUnitOfWork,
        notifications_client: AbstractNotificationClient,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._notifications_client = notifications_client

    async def execute(self, data: ShipmentEventDTO) -> Order | None:
        async with self._unit_of_work() as uow:
            already_processed = await uow.inbox.exists(data.event_id)

            if already_processed:
                return None

            order = await uow.orders.get_by_id(data.order_id)

            if order is None:
                raise OrderNotFoundError(f"Order with id {data.order_id} not found")

            if data.event_type == "order.shipped":
                order = await uow.orders.update_status(
                    data.order_id, OrderStatus.SHIPPED
                )

            elif data.event_type == "order.cancelled":
                order = await uow.orders.update_status(
                    data.order_id, OrderStatus.CANCELLED
                )

            else:
                raise UnknownEventTypeError(f"Unknown event type: {data.event_type}")

            await uow.inbox.create(
                event_id=data.event_id,
                event_type=data.event_type,
                payload=data.model_dump(mode="json"),
            )

            await uow.commit()

        try:
            if data.event_type == "order.shipped":
                await self._notifications_client.send_notification(
                    message="SHIPPED: Ваш заказ отправлен в доставку",
                    reference_id=str(order.id),
                    idempotency_key=f"{order.id}:SHIPPED",
                )
            elif data.event_type == "order.cancelled":
                reason = data.reason or "Unknown reason"
                await self._notifications_client.send_notification(
                    message=f"CANCELLED: Ваш заказ отменен. Причина: {reason}",
                    reference_id=str(order.id),
                    idempotency_key=f"{order.id}:CANCELLED:shipment",
                )
        except NotificationServiceError as exc:
            logger.error("Failed to send notification: %s", exc)

        return order
