import json
import logging
import pika
from src.services.messaging.connection import get_rabbitmq_connection
from src.services.messaging.topology import EXCHANGE_NAME, setup_topology

logger = logging.getLogger(__name__)

def publish_reminder_event(routing_key: str, payload: dict) -> bool:
    connection = get_rabbitmq_connection()
    channel = connection.channel()

    try:
        setup_topology(channel)
        channel.confirm_delivery()

        body = json.dumps(payload, ensure_ascii=False)

        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=routing_key,
            body=body,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Mensaje persistente en disco
                content_type="application/json",
            ),
            mandatory=True,
        )
        logger.info(f"Mensaje publicado en {routing_key}")
        return True
    except pika.exceptions.AMQPError as err:
        logger.error(f"Error publicando en RabbitMQ: {err}")
        return False
    finally:
        connection.close()