from uuid import UUID

from pydantic import BaseModel, Field

from app.core.models import Order
from app.infrastructure.http_clients import (
    CatalogItemNotFoundError,
    CatalogServiceClient,
    CatalogServiceError,
)
from app.infrastructure.unit_of_work import UnitOfWork


class ItemNotFoundError(Exception):
    pass


class InsufficientStockError(Exception):
    pass


class CatalogUnavailableError(Exception):
    pass


class CreateOrderUseCase:
    class InputDTO(BaseModel):
        user_id: str
        quantity: int = Field(gt=0)
        item_id: UUID
        idempotency_key: UUID

    def __init__(
        self, unit_of_work: UnitOfWork, catalog_client: CatalogServiceClient
    ) -> None:
        self._unit_of_work = unit_of_work
        self._catalog_client = catalog_client

    async def execute(self, data: InputDTO) -> Order:
        async with self._unit_of_work() as uow:
            existing_order = await uow.orders.get_by_idempotency_key(
                data.idempotency_key
            )
            if existing_order is not None:
                return existing_order

            try:
                item = await self._catalog_client.get_item(data.item_id)
            except CatalogItemNotFoundError as exc:
                raise ItemNotFoundError(
                    f"Item with id {data.item_id} not found"
                ) from exc
            except CatalogServiceError as exc:
                raise CatalogUnavailableError("Catalog service is unavailable") from exc

            if item.available_qty < data.quantity:
                raise InsufficientStockError(
                    f"Insufficient stock for item {data.item_id}. "
                    f"Available: {item.available_qty}, requested: {data.quantity}"
                )

            order = await uow.orders.create(
                uow.orders.CreateDTO(
                    user_id=data.user_id,
                    item_id=data.item_id,
                    quantity=data.quantity,
                    idempotency_key=data.idempotency_key,
                )
            )

            await uow.commit()
            return order
