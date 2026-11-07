import logging

logger = logging.getLogger(__name__)

# En un entorno de producción, esto sería una tabla en PostgreSQL o Redis.
# Para la arquitectura actual, este set en memoria cumple con el criterio de aceptación.
_processed_messages = set()

def is_idempotent(message_id: str) -> bool:
    """
    Verifica si un mensaje ya fue procesado. 
    Retorna True si es un mensaje nuevo (seguro para procesar), 
    o False si es un duplicado (debe ser ignorado).
    """
    if not message_id:
        logger.warning("Mensaje sin ID recibido. Se procesará por defecto.")
        return True

    if message_id in _processed_messages:
        logger.info(f"Mensaje duplicado detectado y bloqueado (Idempotencia): {message_id}")
        return False

    # Si es nuevo, lo registramos como procesado
    _processed_messages.add(message_id)
    return True
    
def clear_idempotency_cache():
    """Limpia el registro (útil para pruebas unitarias)."""
    _processed_messages.clear()