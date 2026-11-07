from fastapi import APIRouter
from pydantic import BaseModel
from src.services.risk_calculator import calculate_no_show_risk
from src.services.overbooking_manager import check_overbooking_availability # Nueva importación

router = APIRouter(prefix="/risk", tags=["Risk Engine"])

class PatientHistoryParams(BaseModel):
    total_appointments: int = 0
    historical_no_shows: int = 0
    days_since_last_visit: int = 0
    age: int = 0

class OverbookingParams(BaseModel):
    current_bookings: int
    max_capacity: int
    provider_no_show_rate: float

@router.post("/calculate")
def evaluate_risk(patient_data: PatientHistoryParams):
    data_dict = patient_data.model_dump() 
    risk_result = calculate_no_show_risk(data_dict)
    return {"message": "Cálculo de riesgo completado", "data": risk_result}

@router.post("/overbooking")
def evaluate_overbooking(params: OverbookingParams):
    """
    Evalúa si es seguro agendar una cita extra cuando la agenda está llena.
    """
    result = check_overbooking_availability(
        params.current_bookings, 
        params.max_capacity, 
        params.provider_no_show_rate
    )
    return result