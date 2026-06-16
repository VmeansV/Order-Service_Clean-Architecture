import asyncio
import logging

import sentry_sdk
import uvicorn
from fastapi import FastAPI

from app.application.process_outbox_events import ProcessOutboxEventsUseCase
from app.application.process_shipment_event import ProcessShipmentEventUseCase
from app.config import settings
from app.infrastructure.kafka_consumer import KafkaConsumerClient
from app.infrastructure.kafka_producer import KafkaProducer
from app.infrastructure.unit_of_work import UnitOfWork
from app.presentation.api import router
from app.presentation.dependencies import (
    catalog_client,
    engine,
    payments_client,
    session_factory,
)
from app.presentation.kafka_consumer_worker import KafkaConsumerWorker
from app.presentation.outbox_worker import OutboxWorker

logging.basicConfig(level=logging.INFO)

if settings.sentry_dsn:
    sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=1.0)


def build_app() -> FastAPI:
    app = FastAPI(title="Order service")
    app.include_router(router)
    return app


async def main():
    app = build_app()

    uow = UnitOfWork(session_factory)
    kafka_producer = KafkaProducer()
    kafka_consumer = KafkaConsumerClient()

    outbox_use_case = ProcessOutboxEventsUseCase(
        unit_of_work=uow, kafka_producer=kafka_producer
    )

    shipment_use_case = ProcessShipmentEventUseCase(unit_of_work=uow)

    outbox_worker = OutboxWorker(use_case=outbox_use_case)

    consumer_worker = KafkaConsumerWorker(
        consumer=kafka_consumer, use_case=shipment_use_case
    )

    api_task = asyncio.create_task(
        uvicorn.Server(
            uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
        ).serve()
    )

    outbox_task = asyncio.create_task(outbox_worker.run())
    consumer_task = asyncio.create_task(consumer_worker.run())

    try:
        await asyncio.gather(api_task, outbox_task, consumer_task)
    finally:
        outbox_worker.stop()
        consumer_worker.stop()
        kafka_producer.close()
        await catalog_client.close()
        await payments_client.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
