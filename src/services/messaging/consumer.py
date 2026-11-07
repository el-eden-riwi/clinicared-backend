import json
import logging
from src.services.messaging.connection import get_rabbitmq_connection
from src.services.messaging.topology import setup_topology

# <-- 1. AQUÍ AGREGAMOS LA IMPORTACIÓN NUEVA -->
from src.services.idempotency_manager import is_idempotent 

logger = logging.getLogger(__name__)

def handle_message(payload: dict) -> None:
    print(f"[x] Procesando recordatorio: {payload}")
    if payload.get("error_simulado"):
        raise ValueError("Error forzado para desvío a Dead Letter Queue (DLQ)")

def start_consumer(queue_name: str = "queue.reminders.sms") -> None:
    connection = get_rabbitmq_connection()
    channel = connection.channel()
    
    setup_topology(channel)
    channel.basic_qos(prefetch_count=1)

    # Esta es la función que se ejecuta cada vez que llega un mensaje
    def callback(ch, method, properties, body):
        try:
            data = json.loads(body.decode("utf-8"))
            
            # <-- 2. AQUÍ AGREGAMOS LA PROTECCIÓN DE IDEMPOTENCIA -->
            # Buscamos un identificador único en el mensaje
            message_id = data.get("message_id")
            
            # Preguntamos a nuestro gestor si ya procesó este ID
            if not is_idempotent(message_id):
                # Si ya existe (es duplicado), le decimos a RabbitMQ que lo borre (ACK) 
                # y usamos 'return' para frenar la ejecución y no enviar nada.
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return 
            # <------------------------------------------------------->

            handle_message(data)
            
            # Confirmación manual exitosa
            ch.basic_ack(delivery_tag=method.delivery_tag)
            print("[√] Mensaje procesado y confirmado (ACK).")
            
        except Exception as exc:
            logger.error(f"[!] Falló al procesar: {exc}")
            # Envío automático a la DLQ mediante NACK sin reencolar
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            print("[x] Mensaje redirigido a DLQ (NACK).")

    channel.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=False)
    print(f"[*] Consumidor activo en '{queue_name}'. Presiona Ctrl+C para salir.")
    
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
        connection.close()

if __name__ == "__main__":
    start_consumer()