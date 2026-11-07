def calculate_no_show_risk(patient_history: dict) -> dict:
    """
    Calcula el riesgo de inasistencia (no-show) de un paciente basándose en su historial.
    Retorna la clasificación del riesgo y el porcentaje calculado.
    """
    risk_score = 0
    total_appointments = patient_history.get("total_appointments", 0)
    no_shows = patient_history.get("historical_no_shows", 0)
    days_since_last_visit = patient_history.get("days_since_last_visit", 0)
    age = patient_history.get("age", 0)

    # Regla 1: Historial directo (peso alto)
    if total_appointments > 0:
        no_show_rate = no_shows / total_appointments
        if no_show_rate > 0.3:
            risk_score += 40  # Alta probabilidad de reincidir
        elif no_show_rate > 0.1:
            risk_score += 20
    else:
        risk_score += 15 # Riesgo leve por ser paciente nuevo (sin historial)

    # Regla 2: Tiempo sin asistir a la clínica
    if days_since_last_visit > 365:
        risk_score += 25
    elif days_since_last_visit > 180:
        risk_score += 10

    # Regla 3: Factor demográfico (ejemplo: jóvenes tienden a faltar más a consultas de rutina)
    if 18 <= age <= 30:
        risk_score += 10
    elif age > 65:
        risk_score -= 10 # Adultos mayores suelen ser más cumplidos

    # Limitar el score entre 0 y 100
    risk_score = max(0, min(100, risk_score))

    # Clasificación final
    if risk_score >= 60:
        classification = "HIGH"
    elif risk_score >= 30:
        classification = "MEDIUM"
    else:
        classification = "LOW"

    return {
        "risk_score_percentage": risk_score,
        "classification": classification
    }