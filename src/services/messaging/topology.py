import pika

EXCHANGE_NAME = "clinicared.reminders.exchange"
DLX_NAME = "clinicared.reminders.dlx"
DLQ_QUEUE = "clinicared.reminders.dlq"

QUEUES_CONFIG = {
    "queue.reminders.sms": {
        "routing_key": "reminder.sms.*",
        "dlx": DLX_NAME,
    },
    "queue.reminders.email": {
        "routing_key": "reminder.email.*",
        "dlx": DLX_NAME,
    },
}

def setup_topology(channel: pika.adapters.blocking_connection.BlockingChannel) -> None:
    # 1. Exchange principal (topic) y Dead Letter Exchange (direct)
    channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="topic", durable=True)
    channel.exchange_declare(exchange=DLX_NAME, exchange_type="direct", durable=True)

    # 2. Cola Dead Letter (DLQ) vinculada al DLX
    channel.queue_declare(queue=DLQ_QUEUE, durable=True)
    channel.queue_bind(exchange=DLX_NAME, queue=DLQ_QUEUE, routing_key="dead_letter")

    # 3. Colas de recordatorios con política de desvío al DLX ante rechazo
    for queue_name, config in QUEUES_CONFIG.items():
        arguments = {
            "x-dead-letter-exchange": config["dlx"],
            "x-dead-letter-routing-key": "dead_letter",
        }
        channel.queue_declare(queue=queue_name, durable=True, arguments=arguments)
        channel.queue_bind(
            exchange=EXCHANGE_NAME,
            queue=queue_name,
            routing_key=config["routing_key"],
        )