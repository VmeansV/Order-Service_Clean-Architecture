from abc import ABC, abstractmethod
from uuid import UUID

from app.core.models import Item, Order, OrderStatus, OutboxEvent


class AbstractOrderRepository(ABC):
    @abstractmethod
    async def create(self, dto) -> Order:
        pass

    @abstractmethod
    async def get_by_id(self, order_id: UUID) -> Order | None:
        pass

    @abstractmethod
    async def get_by_idempotency_key(self, idempotency_key: str) -> Order | None:
        pass

    @abstractmethod
    async def update_status(self, order_id: UUID, status: OrderStatus) -> Order:
        pass


class AbstractOutboxRepository(ABC):
    @abstractmethod
    async def create(self, event_type: str, payload: dict) -> OutboxEvent:
        pass

    @abstractmethod
    async def get_pending(self, limit: int = 10) -> list[OutboxEvent]:
        pass

    @abstractmethod
    async def mark_as_sent(self, event_id: UUID) -> None:
        pass

    @abstractmethod
    async def mark_as_failed(self, event_id: UUID) -> None:
        pass


class AbstractInboxRepository(ABC):
    @abstractmethod
    async def exists(self, event_id: UUID) -> bool:
        pass

    @abstractmethod
    async def create(self, event_id: UUID, event_type: str, payload: dict) -> None:
        pass


class AbstractUnitOfWork(ABC):
    orders: AbstractOrderRepository
    outbox: AbstractOutboxRepository
    inbox: AbstractInboxRepository

    @abstractmethod
    async def commit(self) -> None:
        pass

    @abstractmethod
    async def __call__(self):
        pass


class AbstractCatalogClient(ABC):
    @abstractmethod
    async def get_item(self, item_id: UUID) -> Item:
        pass


class AbstractPaymentClient(ABC):
    @abstractmethod
    async def create_payment(
        self, order_id: str, amount: str, idempotency_key: str
    ) -> dict:
        pass


class AbstractNotificationClient(ABC):
    @abstractmethod
    async def send_notification(
        self, message: str, reference_id: str, idempotency_key: str
    ) -> dict:
        pass


class AbstractKafkaProducer(ABC):
    @abstractmethod
    def send(self, message: dict, key: str | None = None) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass
