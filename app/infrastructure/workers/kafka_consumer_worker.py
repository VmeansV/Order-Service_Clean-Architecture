import asyncio
import json
import logging
from uuid import NAMESPACE_URL, uuid5

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
                message = await asyncio.to_thread(self._consumer.poll, 1.0)

                if message is None:
                    continue

                logger.info("Received event: %s", message.get("event_type"))

                event_id = message.get("event_id")

                if not event_id:
                    event_id = str(
                        uuid5(
                            NAMESPACE_URL,
                            json.dumps(message, sort_keys=True, ensure_ascii=False),
                        )
                    )

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
                    "Processed event: %s for order %s",
                    dto.event_type,
                    dto.order_id,
                )

            except Exception as e:
                logger.error("Kafka consumer worker error: %s", e)

            await asyncio.sleep(0.1)

        logger.info("Kafka consumer worker stopped")

    def stop(self) -> None:
        self._running = False
        self._consumer.close()
