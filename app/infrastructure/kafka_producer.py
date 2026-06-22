import json

from confluent_kafka import Producer

from app.application.interfaces import AbstractKafkaProducer
from app.config import settings


class KafkaProducer(AbstractKafkaProducer):
    TOPIC = "student_system-order.events"

    def __init__(self) -> None:
        self._producer = Producer(
            {"bootstrap.servers": settings.kafka_bootstrap_servers}
        )

    def send(self, message: dict, key: str | None = None) -> None:
        self._producer.produce(
            topic=self.TOPIC,
            value=json.dumps(message).encode("utf-8"),
            key=key.encode("utf-8") if key else None,
        )
        self._producer.flush()

    def close(self) -> None:
        self._producer.flush()
