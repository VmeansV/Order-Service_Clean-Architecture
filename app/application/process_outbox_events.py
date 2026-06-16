from app.infrastructure.kafka_producer import KafkaProducer
from app.infrastructure.unit_of_work import UnitOfWork


class ProcessOutboxEventsUseCase:
    def __init__(self, unit_of_work: UnitOfWork, kafka_producer: KafkaProducer) -> None:
        self._unit_of_work = unit_of_work
        self._kafka_producer = kafka_producer

    async def execute(self) -> int:
        async with self._unit_of_work() as uow:
            events = await uow.outbox.get_pending()

            if not events:
                return 0

            sent_count = 0

            for event in events:
                try:
                    self._kafka_producer.send(
                        message=event.payload, key=event.payload.get("order_id")
                    )
                    await uow.outbox.mark_as_sent(event.id)
                    sent_count += 1

                except Exception:
                    await uow.outbox.mark_as_failed(event.id)

            await uow.commit()
            return sent_count
