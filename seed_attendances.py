import random
from sqlalchemy import text
from src.core.database import engine

def seed_attendances():
    with engine.begin() as conn:
        # Verificar cuántas citas existen
        appts = conn.execute(text("SELECT id FROM appointments ORDER BY id ASC;")).fetchall()
        if not appts:
            print("[!] No hay citas registradas en appointments.")
            return

        # Limpiar asistencias previas
        conn.execute(text("DELETE FROM attendances;"))

        # Poblar asistencias con distribución realista: ~70% asistió, ~30% faltó (no-show)
        random.seed(42)  # Semilla fija para reproducibilidad
        values = []
        for appt in appts:
            attended = random.choices([True, False], weights=[0.70, 0.30])[0]
            values.append(f"({appt.id}, {attended})")

        insert_sql = text(f"""
            INSERT INTO attendances (appointment_id, attended)
            VALUES {', '.join(values)};
        """)
        conn.execute(insert_sql)
        print(f"[v] Se registraron exitosamente {len(appts)} registros de asistencia histórica en PostgreSQL.")

if __name__ == "__main__":
    seed_attendances()
