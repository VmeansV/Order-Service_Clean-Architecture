import json
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Row, insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import (
    Order,
    OrderStatus,
    OutboxEvent,
    OutboxEventStatus,
)
from app.infrastructure.db_schema import inbox_tbl, orders_tbl, outbox_tbl


class OrderRepository:
    class CreateDTO(BaseModel):
        user_id: str
        item_id: UUID
        quantity: int
        amount: Decimal
        idempotency_key: str

    def __init__(self, session: AsyncSession):
        self._session = session

    @staticmethod
    def _construct(row: Row) -> Order:
        data = row._mapping

        return Order(
            id=data["id"],
            user_id=data["user_id"],
            item_id=data["item_id"],
            quantity=data["quantity"],
            amount=data["amount"],
            status=OrderStatus(data["status"]),
            idempotency_key=data["idempotency_key"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
        )

    async def create(self, order: CreateDTO) -> Order:
        stmt_order = (
            insert(orders_tbl)
            .values(
                user_id=order.user_id,
                item_id=order.item_id,
                quantity=order.quantity,
                amount=order.amount,
                status=OrderStatus.NEW.value,
                idempotency_key=order.idempotency_key,
            )
            .returning(*orders_tbl.c)
        )

        result = await self._session.execute(stmt_order)
        row = result.fetchone()

        return self._construct(row)

    async def get_by_id(self, order_id: UUID) -> Order | None:
        stmt = select(*orders_tbl.c).where(orders_tbl.c.id == order_id)
        result = await self._session.execute(stmt)
        row = result.fetchone()

        if row is None:
            return None

        return self._construct(row)

    async def get_by_idempotency_key(self, idempotency_key: str) -> Order | None:
        stmt = select(*orders_tbl.c).where(
            orders_tbl.c.idempotency_key == idempotency_key
        )
        result = await self._session.execute(stmt)
        row = result.fetchone()

        if row is None:
            return None

        return self._construct(row)

    async def update_status(self, order_id: UUID, status: OrderStatus) -> Order:
        stmt = (
            update(orders_tbl)
            .where(orders_tbl.c.id == order_id)
            .values(status=status.value)
            .returning(*orders_tbl.c)
        )

        result = await self._session.execute(stmt)
        row = result.fetchone()

        if row is None:
            raise ValueError(f"Order with id {order_id} not found")

        return self._construct(row)


class OutboxRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    @staticmethod
    def _construct(row: Row) -> OutboxEvent:
        data = row._mapping

        return OutboxEvent(
            id=data["id"],
            event_type=data["event_type"],
            payload=json.loads(data["payload"]),
            status=OutboxEventStatus(data["status"]),
            created_at=data["created_at"],
        )

    async def create(
        self,
        event_type: str,
        payload: dict,
    ) -> OutboxEvent:
        stmt = (
            insert(outbox_tbl)
            .values(
                event_type=event_type,
                payload=json.dumps(payload),
                status=OutboxEventStatus.PENDING.value,
            )
            .returning(*outbox_tbl.c)
        )

        result = await self._session.execute(stmt)
        row = result.fetchone()

        return self._construct(row)

    async def get_pending(self, limit: int = 10) -> list[OutboxEvent]:
        stmt = (
            select(*outbox_tbl.c)
            .where(outbox_tbl.c.status == OutboxEventStatus.PENDING.value)
            .order_by(outbox_tbl.c.created_at)
            .limit(limit)
        )

        result = await self._session.execute(stmt)

        rows = result.fetchall()

        return [self._construct(row) for row in rows]

    async def mark_as_sent(self, event_id: UUID) -> None:
        stmt = (
            update(outbox_tbl)
            .where(outbox_tbl.c.id == event_id)
            .values(status=OutboxEventStatus.SENT.value)
        )

        await self._session.execute(stmt)

    async def mark_as_failed(self, event_id: UUID) -> None:
        stmt = (
            update(outbox_tbl)
            .where(outbox_tbl.c.id == event_id)
            .values(status=OutboxEventStatus.FAILED.value)
        )

        await self._session.execute(stmt)


class InboxRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def exists(self, event_id: UUID) -> bool:
        stmt = select(*inbox_tbl.c).where(inbox_tbl.c.id == event_id)
        result = await self._session.execute(stmt)
        row = result.fetchone()

        return row is not None

    async def create(self, event_id: UUID, event_type: str, payload: dict) -> None:
        stmt = insert(inbox_tbl).values(
            id=event_id,
            event_type=event_type,
            payload=json.dumps(payload),
        )

        await self._session.execute(stmt)
