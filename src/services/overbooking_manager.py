def check_overbooking_availability(current_bookings: int, max_capacity: int, provider_no_show_rate: float) -> dict:
    """
    Determina si se puede programar una cita extra (overbooking) basado en la capacidad máxima
    y la tasa histórica de inasistencia del médico o la clínica.
    """
    # Si aún hay espacio normal, se acepta inmediatamente
    if current_bookings < max_capacity:
        return {
            "can_book": True,
            "is_overbooked": False,
            "message": "Capacidad normal disponible."
        }

    # Lógica de sobreventa controlada:
    # Permitimos citas extra equivalentes a la probabilidad de que la gente falte.
    # Ejemplo: Si la capacidad es 20 y el no_show_rate es 0.2 (20%), permitimos 4 citas extra.
    allowed_overbooking = int(max_capacity * provider_no_show_rate)
    max_allowed_bookings = max_capacity + allowed_overbooking

    if current_bookings < max_allowed_bookings:
        return {
            "can_book": True,
            "is_overbooked": True,
            "message": f"Cita aceptada bajo regla de sobreventa. Espacios extra usados: {current_bookings - max_capacity + 1}/{allowed_overbooking}"
        }
    
    return {
        "can_book": False,
        "is_overbooked": True,
        "message": "Capacidad máxima de sobreventa alcanzada. Debe ir a lista de espera."
    }