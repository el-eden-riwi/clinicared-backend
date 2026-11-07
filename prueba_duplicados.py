from src.services.messaging.producer import publish_reminder_event

# Simulamos un evento de recordatorio con un ID único
mensaje = {
    "message_id": "EVT-999", 
    "paciente": "Jeas Ayala", 
    "tipo": "recordatorio_sms"
}

print("-> Enviando mensaje ORIGINAL...")
publish_reminder_event(routing_key="reminder.sms.test", payload=mensaje)

print("-> Enviando mensaje DUPLICADO por error de red...")
publish_reminder_event(routing_key="reminder.sms.test", payload=mensaje)