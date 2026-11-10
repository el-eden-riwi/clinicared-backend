-- 1. Sedes
CREATE TABLE IF NOT EXISTS locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(255),
    city VARCHAR(100)
);

-- 2. Especialidades
CREATE TABLE IF NOT EXISTS specialties (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- 3. Profesionales Médicos
CREATE TABLE IF NOT EXISTS professionals (
    id SERIAL PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    medical_license VARCHAR(50) UNIQUE NOT NULL
);

-- 4. Pacientes (coincide con src/models/patient.py)
CREATE TABLE IF NOT EXISTS patients (
    id SERIAL PRIMARY KEY,
    national_id VARCHAR(20) UNIQUE NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(30),
    date_of_birth DATE
);

-- 5. Relación Profesionales - Especialidades
CREATE TABLE IF NOT EXISTS professional_specialties (
    professional_id INT REFERENCES professionals(id) ON DELETE CASCADE,
    specialty_id INT REFERENCES specialties(id) ON DELETE CASCADE,
    PRIMARY KEY (professional_id, specialty_id)
);

-- 6. Citas Médicas
CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    patient_id INT REFERENCES patients(id) ON DELETE CASCADE,
    professional_id INT REFERENCES professionals(id) ON DELETE CASCADE,
    location_id INT REFERENCES locations(id) ON DELETE CASCADE,
    specialty_id INT REFERENCES specialties(id) ON DELETE CASCADE,
    scheduled_datetime TIMESTAMP NOT NULL,
    status VARCHAR(20) DEFAULT 'SCHEDULED'
);

-- 7. Asistencias (analítica No-Show)
CREATE TABLE IF NOT EXISTS attendances (
    id SERIAL PRIMARY KEY,
    appointment_id INT REFERENCES appointments(id) ON DELETE CASCADE,
    attended BOOLEAN DEFAULT FALSE,
    check_in_time TIMESTAMP
);

-- 8. Mensajería / Idempotencia
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(100) UNIQUE,
    recipient VARCHAR(100),
    channel VARCHAR(20),
    content TEXT,
    status VARCHAR(20) DEFAULT 'SENT',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
