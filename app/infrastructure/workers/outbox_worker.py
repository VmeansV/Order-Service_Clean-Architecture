import asyncio
import logging

from app.application.process_outbox_events import ProcessOutboxEventsUseCase

logger = logging.getLogger(__name__)


class OutboxWorker:
    def __init__(self, use_case: ProcessOutboxEventsUseCase) -> None:
        self._use_case = use_case
        self._running = True

    async def run(self) -> None:
        logger.info("Outbox worker started")

        while self._running:
            try:
                sent_count = await self._use_case.execute()

                if sent_count > 0:
                    logger.info("Outbox worker sent %d events", sent_count)

            except Exception as e:
                logger.error("Outbox worker error: %s", e)

            await asyncio.sleep(1)

        logger.info("Outbox worker stopped")

    def stop(self) -> None:
        self._running = False
