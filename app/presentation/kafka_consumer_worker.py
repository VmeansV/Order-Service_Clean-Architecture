import asyncio
import logging
from uuid import uuid4

from app.application.process_shipment_event import (
    ProcessShipmentEventUseCase,
    ShipmentEventDTO,
)
from app.infrastructure.kafka_consumer import KafkaConsumerClient

logger = logging.getLogger(__name__)


class KafkaConsumerWorker:
    def __init__(
        self, consumer: KafkaConsumerClient, use_case: ProcessShipmentEventUseCase
    ) -> None:
        self._consumer = consumer
        self._use_case = use_case
        self._running = True

    async def run(self) -> None:
        logger.info("Kafka consumer worker started")

        while self._running:
            try:
                message = asyncio.to_thread(self._consumer.poll, 1.0)

                if message is None:
                    continue

                logger.info(f"Received event: {message.get('event_type')}")

                event_id = message.get("event_id") or str(uuid4())

                dto = ShipmentEventDTO(
                    event_id=event_id,
                    event_type=message["event_type"],
                    order_id=message["order_id"],
                    item_id=message["item_id"],
                    quantity=message["quantity"],
                    shipment_id=message.get("shipment_id"),
                    reason=message.get("reason"),
                )

                await self._use_case.execute(dto)

                logger.info(
                    f"Processed event: {dto.event_type} for order {dto.order_id}"
                )

            except Exception as e:
                logger.error(f"Kafka consumer worker error: {e}")

            await asyncio.sleep(0.1)

        logger.info("Kafka consumer worker stopped")

    def stop(self) -> None:
        self._running = False
        self._consumer.close()
