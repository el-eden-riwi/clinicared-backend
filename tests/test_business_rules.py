from src.services.risk_calculator import calculate_no_show_risk
from src.services.overbooking_manager import check_overbooking_availability

# --- TESTS PARA EL MOTOR DE RIESGO ---

def test_calculate_no_show_risk_high():
    """Escenario: Paciente con alta tasa de inasistencia previa."""
    patient_data = {
        "total_appointments": 10,
        "historical_no_shows": 4, # 40% de inasistencia
        "days_since_last_visit": 200,
        "age": 25
    }
    result = calculate_no_show_risk(patient_data)
    assert result["classification"] == "HIGH"
    assert result["risk_score_percentage"] >= 50

def test_calculate_no_show_risk_low():
    """Escenario: Paciente cumplido y adulto mayor."""
    patient_data = {
        "total_appointments": 5,
        "historical_no_shows": 0,
        "days_since_last_visit": 10,
        "age": 70
    }
    result = calculate_no_show_risk(patient_data)
    assert result["classification"] == "LOW"

# --- TESTS PARA EL CONTROL DE SOBREVENTA (OVERBOOKING) ---

def test_overbooking_allows_extra_capacity():
    """Escenario: Agenda llena, pero el % de inasistencia permite sobreventa."""
    # Capacidad 20, tasa de inasistencia 20%. Permite 4 extras (hasta 24).
    # Actual: 21 (1 extra). Debería permitirlo.
    result = check_overbooking_availability(
        current_bookings=21, 
        max_capacity=20, 
        provider_no_show_rate=0.2
    )
    assert result["can_book"] is True
    assert result["is_overbooked"] is True

def test_overbooking_rejects_when_full():
    """Escenario: Se alcanzó el límite máximo de sobreventa permitida."""
    # Capacidad 20, inasistencia 20% = máximo 24 citas.
    # Intentamos meter la cita 25, debería rechazarla.
    result = check_overbooking_availability(
        current_bookings=24, 
        max_capacity=20, 
        provider_no_show_rate=0.2
    )
    assert result["can_book"] is False