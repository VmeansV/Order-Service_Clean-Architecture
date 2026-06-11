from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import Row, insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models import Order, OrderStatus
from app.infrastructure.db_schema import orders_tbl


class OrderRepository:
    class CreateDTO(BaseModel):
        user_id: str
        item_id: UUID
        quantity: int
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
                status=OrderStatus.NEW.value,
                idempotency_key=order.idempotency_key,
            )
            .returning(*orders_tbl.c)
        )

        result = await self._session.execute(stmt_order)
        row = result.fetchone()

        return self._construct(row)

    async def get_by_id(self, order_id: UUID) -> Order:
        stmt = select(*orders_tbl.c).where(orders_tbl.c.id == order_id)
        result = await self._session.execute(stmt)
        row = result.fetchone()

        if row is None:
            raise ValueError(f"Order with id {order_id} not found")

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
