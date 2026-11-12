import uuid
from datetime import datetime, date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.models.patient import Patient
from src.models.appointment import Location, Specialty, Professional, Appointment, Attendance, MessageRecord
from src.services.risk_calculator import calculate_no_show_risk
from src.services.idempotency_manager import is_idempotent

router = APIRouter(prefix="/appointments", tags=["Appointments"])

class AppointmentCreate(BaseModel):
    patientName: str
    national_id: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    specialty: str = "Medicina General"
    doctor: str = "Dra. Elena Gómez"
    date: str = "2026-11-15"
    time: str = "09:00 AM"

class StatusUpdate(BaseModel):
    status: str  # SCHEDULED, ATTENDED, NO_SHOW

def _parse_datetime(date_str: str, time_str: str) -> datetime:
    for fmt in ("%Y-%m-%d %I:%M %p", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(f"{date_str.strip()} {time_str.strip()}", fmt)
        except ValueError:
            continue
    return datetime.utcnow() + timedelta(days=1)

def _serialize_appointment(appt: Appointment, db: Session) -> dict:
    patient = appt.patient
    history = db.query(Appointment).filter(Appointment.patient_id == patient.id).all()
    total_appts = len(history)
    no_shows = sum(1 for a in history if a.status == "NO_SHOW")
    past_dates = [a.scheduled_datetime.date() for a in history if a.scheduled_datetime.date() <= date.today()]
    days_since = (date.today() - max(past_dates)).days if past_dates else 30
    age = (date.today().year - patient.date_of_birth.year) if patient.date_of_birth else 35

    risk_data = calculate_no_show_risk({
        "total_appointments": total_appts,
        "historical_no_shows": no_shows,
        "days_since_last_visit": max(0, days_since),
        "age": age
    })

    return {
        "id": appt.id,
        "patient_id": patient.id,
        "name": f"{patient.first_name} {patient.last_name}".strip(),
        "national_id": patient.national_id,
        "specialty": appt.specialty.name if appt.specialty else "Medicina General",
        "doctor": f"{appt.professional.first_name} {appt.professional.last_name}".strip() if appt.professional else "Dra. Elena Gómez",
        "date": appt.scheduled_datetime.strftime("%Y-%m-%d"),
        "time": appt.scheduled_datetime.strftime("%I:%M %p"),
        "status": appt.status,
        "total_appointments": total_appts,
        "historical_no_shows": no_shows,
        "days_since_last_visit": max(0, days_since),
        "age": age,
        "risk": risk_data["classification"],
        "score": f"{risk_data['risk_score_percentage']}%"
    }

@router.get("/")
def list_appointments(db: Session = Depends(get_db)):
    appts = db.query(Appointment).order_by(Appointment.scheduled_datetime.desc()).limit(50).all()
    return [_serialize_appointment(a, db) for a in appts]

@router.post("/", status_code=status.HTTP_201_CREATED)
def create_appointment(
    payload: AppointmentCreate,
    x_idempotency_key: Optional[str] = Header(default=None),
    db: Session = Depends(get_db)
):
    if x_idempotency_key:
        existing_msg = db.query(MessageRecord).filter(MessageRecord.message_id == x_idempotency_key).first()
        if existing_msg or not is_idempotent(x_idempotency_key):
            raise HTTPException(status_code=409, detail="Solicitud duplicada bloqueada por idempotencia.")

    parts = payload.patientName.strip().split(" ", 1)
    first_name = parts[0]
    last_name = parts[1] if len(parts) > 1 else "Paciente"

    patient = None
    if payload.national_id:
        patient = db.query(Patient).filter(Patient.national_id == payload.national_id).first()
    if not patient:
        patient = db.query(Patient).filter(
            Patient.first_name == first_name,
            Patient.last_name == last_name
        ).first()
    if not patient:
        doc_id = payload.national_id or f"CC-{uuid.uuid4().hex[:8].upper()}"
        patient = Patient(
            national_id=doc_id,
            first_name=first_name,
            last_name=last_name,
            email=payload.email,
            phone=payload.phone,
            date_of_birth=date(1990, 5, 15)
        )
        db.add(patient)
        db.flush()

    location = db.query(Location).first()
    if not location:
        location = Location(name="Sede Principal Barranquilla", address="Cra 54 # 72-10", city="Barranquilla")
        db.add(location)
        db.flush()

    specialty = db.query(Specialty).filter(Specialty.name == payload.specialty).first()
    if not specialty:
        specialty = Specialty(name=payload.specialty, description=f"Servicio de {payload.specialty}")
        db.add(specialty)
        db.flush()

    doc_parts = payload.doctor.strip().split(" ", 1)
    professional = db.query(Professional).filter(Professional.first_name == doc_parts[0]).first()
    if not professional:
        professional = Professional(
            first_name=doc_parts[0],
            last_name=doc_parts[1] if len(doc_parts) > 1 else "Médico",
            email=f"med.{uuid.uuid4().hex[:6]}@clinicared.com",
            medical_license=f"RM-{uuid.uuid4().hex[:6].upper()}"
        )
        db.add(professional)
        db.flush()

    scheduled_dt = _parse_datetime(payload.date, payload.time)
    new_appt = Appointment(
        patient_id=patient.id,
        professional_id=professional.id,
        location_id=location.id,
        specialty_id=specialty.id,
        scheduled_datetime=scheduled_dt,
        status="SCHEDULED"
    )
    db.add(new_appt)

    msg = MessageRecord(
        message_id=x_idempotency_key or f"msg_{uuid.uuid4().hex[:12]}",
        recipient=payload.patientName,
        channel="SMS",
        content=f"Cita confirmada con {payload.doctor} ({payload.specialty}) el {payload.date} a las {payload.time}",
        status="PERSISTED_RDS"
    )
    db.add(msg)
    db.commit()
    db.refresh(new_appt)

    return {
        "status": "PERSISTED_RDS",
        "message": "Cita registrada en PostgreSQL RDS",
        "appointment": _serialize_appointment(new_appt, db)
    }

@router.patch("/{appointment_id}/status")
def update_appointment_status(appointment_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Cita no encontrada")

    new_status = payload.status.upper()
    if new_status not in ("SCHEDULED", "ATTENDED", "NO_SHOW"):
        raise HTTPException(status_code=400, detail="Estado inválido")

    appt.status = new_status
    attendance = db.query(Attendance).filter(Attendance.appointment_id == appt.id).first()
    if not attendance:
        attendance = Attendance(appointment_id=appt.id)
        db.add(attendance)
    attendance.attended = (new_status == "ATTENDED")
    attendance.check_in_time = datetime.utcnow()

    db.commit()
    db.refresh(appt)
    return _serialize_appointment(appt, db)

@router.delete("/reset")
def reset_transactional_data(db: Session = Depends(get_db)):
    from sqlalchemy import text
    db.execute(text("TRUNCATE TABLE messages, attendances, appointments, patients RESTART IDENTITY CASCADE;"))
    db.commit()
    return {"status": "ok", "message": "Tablas transaccionales de AWS RDS reiniciadas a 0."}
