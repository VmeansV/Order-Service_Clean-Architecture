import json

from confluent_kafka import Consumer, KafkaError

from app.config import settings


class KafkaConsumerClient:
    TOPIC = "student_system-shipment.events"
    GROUP_ID = "order-service-group"

    def __init__(self) -> None:
        self._consumer = Consumer(
            {
                "bootstrap.servers": settings.kafka_bootstrap_servers,
                "group.id": self.GROUP_ID,
                "auto.offset.reset": "earliest",
                "enable.auto.commit": True,
            }
        )
        self._consumer.subscribe([self.TOPIC])

    def poll(self, timeout: float = 1.0) -> dict | None:
        msg = self._consumer.poll(timeout)

        if msg is None:
            return None

        if msg.error():
            if msg.error().code() == KafkaError._PARTITION_EOF:
                return None
            raise Exception(f"Kafka consumer error: {msg.error()}")

        value = msg.value().decode("utf-8")
        return json.loads(value)

    def close(self) -> None:
        self._consumer.close()
