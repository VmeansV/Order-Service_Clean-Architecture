import uuid

from sqlalchemy import UUID, Column, DateTime, Integer, MetaData, String, Table, func

metadata = MetaData()

orders_tbl = Table(
    "orders",
    metadata,
    Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column("user_id", String(255), nullable=False),
    Column("item_id", UUID(as_uuid=True), nullable=False),
    Column("quantity", Integer, nullable=False),
    Column("status", String(20), nullable=False, server_default="NEW"),
    Column("idempotency_key", UUID(as_uuid=True), unique=True, nullable=False),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    Column("updated_at", DateTime, server_default=func.now(), nullable=False),
)
