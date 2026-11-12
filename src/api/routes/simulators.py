from fastapi import APIRouter
from pydantic import BaseModel
from src.services.messaging.producer import publish_reminder_event
import uuid

router = APIRouter(
    prefix="/simulate",
    tags=["External Simulators"]
)

class AdmissionCheckRequest(BaseModel):
    national_id: str

class MessageNotificationRequest(BaseModel):
    recipient: str
    message: str
    channel: str = "SMS"

@router.post("/admissions/verify")
def simulate_admission_check(payload: AdmissionCheckRequest):
    """Simula la validación de estado o afiliación de un paciente."""
    is_active = int(payload.national_id[-1]) % 2 == 0 if payload.national_id[-1].isdigit() else True
    return {
        "national_id": payload.national_id,
        "status": "ACTIVE" if is_active else "INACTIVE",
        "network": "ClínicaRed Preferred",
        "message": "Verificación de admisión completada."
    }

@router.post("/messaging/send")
def simulate_send_message(payload: MessageNotificationRequest):
    """
    Endpoint Gateway: Inyecta en RabbitMQ si está disponible,
    o responde en modo simulación cloud en AWS Fargate.
    """
    mensaje = {
        "message_id": f"API-{uuid.uuid4().hex[:8]}",
        "paciente": payload.recipient,
        "tipo": payload.channel.lower(),
        "contenido": payload.message
    }
    routing_key = f"reminder.{payload.channel.lower()}.gateway"

    try:
        success = publish_reminder_event(routing_key=routing_key, payload=mensaje)
    except Exception:
        success = False

    if success:
        return {
            "status": "QUEUED",
            "channel": payload.channel,
            "message_id": mensaje["message_id"],
            "message": "Mensaje inyectado exitosamente en RabbitMQ"
        }

    return {
        "status": "SIMULATED_SENT",
        "channel": payload.channel,
        "message_id": mensaje["message_id"],
        "message": f"Notificación {payload.channel} procesada correctamente"
    }
