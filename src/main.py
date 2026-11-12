from datetime import datetime, date, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from src.core.database import engine, Base, SessionLocal
from src.models import patient, appointment
from src.models.patient import Patient
from src.models.appointment import Location, Specialty, Professional, Appointment
from src.api.routes import patients, simulators, risk, appointments

Base.metadata.create_all(bind=engine)

def seed_initial_data():
    db = SessionLocal()
    try:
        if db.query(Specialty).count() > 0:
            return
        loc = Location(name="Sede Norte Barranquilla", address="Cra 53 # 80-45", city="Barranquilla")
        db.add(loc)
        db.flush()

        specs = {
            name: Specialty(name=name, description=f"Consulta especializada en {name}")
            for name in ["Medicina General", "Cardiología", "Dermatología", "Pediatría"]
        }
        db.add_all(specs.values())
        db.flush()

        docs = [
            Professional(first_name="Dra. Elena", last_name="Gómez", email="elena.gomez@clinicared.com", medical_license="RM-10421"),
            Professional(first_name="Dr. Roberto", last_name="Suárez", email="roberto.suarez@clinicared.com", medical_license="RM-10422"),
            Professional(first_name="Dra. Patricia", last_name="Ortiz", email="patricia.ortiz@clinicared.com", medical_license="RM-10423"),
        ]
        db.add_all(docs)
        db.flush()

        demo_patients = [
            ("1045231001", "Carlos", "Mendoza", date(1968, 4, 10), "Cardiología", ["NO_SHOW", "NO_SHOW", "ATTENDED"]),
            ("1045231002", "Beatriz", "Castro", date(1984, 7, 22), "Medicina General", ["NO_SHOW", "ATTENDED", "ATTENDED"]),
            ("1045231003", "Andrés", "Morales", date(1998, 2, 14), "Dermatología", ["ATTENDED", "ATTENDED", "ATTENDED"]),
            ("1045231004", "Diana", "Quintero", date(1992, 11, 3), "Pediatría", ["NO_SHOW", "NO_SHOW", "NO_SHOW"]),
        ]
        for idx, (nid, fname, lname, dob, spec_name, past_statuses) in enumerate(demo_patients):
            p = Patient(national_id=nid, first_name=fname, last_name=lname, date_of_birth=dob, phone="300555010" + str(idx))
            db.add(p)
            db.flush()
            for d_idx, st in enumerate(past_statuses):
                db.add(Appointment(
                    patient_id=p.id, professional_id=docs[idx % len(docs)].id,
                    location_id=loc.id, specialty_id=specs[spec_name].id,
                    scheduled_datetime=datetime.now() - timedelta(days=(d_idx + 1) * 20),
                    status=st
                ))
            db.add(Appointment(
                patient_id=p.id, professional_id=docs[idx % len(docs)].id,
                location_id=loc.id, specialty_id=specs[spec_name].id,
                scheduled_datetime=datetime.now() + timedelta(days=1, hours=idx),
                status="SCHEDULED"
            ))
        db.commit()
    except Exception as exc:
        db.rollback()
        print("Aviso seeder inicial:", exc)
    finally:
        db.close()

seed_initial_data()

app = FastAPI(
    title="ClínicaRed Backend API",
    description="API central para la gestión de citas, pacientes y admisiones.",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patients.router)
app.include_router(appointments.router)
app.include_router(simulators.router)
app.include_router(risk.router)

@app.get("/", include_in_schema=False)
def read_root():
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "ClínicaRed API running smoothly"}
