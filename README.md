# 🏥 ClínicaRed - Backend & Data Platform

Plataforma backend y de ingeniería de datos para la gestión transaccional y analítica de citas médicas, sedes, profesionales, pacientes, control de asistencia y notificaciones.

## 🚀 Prerrequisitos

- **Docker & Docker Compose** (Requerido para la base de datos contenedorizada `postgres:15-alpine`)
- **Python 3.10+** (Entorno virtual en Ubuntu WSL2 / Linux)
- **Git**

## 📁 Estructura del Proyecto

```text
clinicared-backend/
├── docs/
│   ├── adr/                              # Architecture Decision Records (Decisiones de diseño)
│   │   ├── 001-motor-base-datos-y-docker.md
│   │   ├── 002-estrategia-seeding-idempotente-calidad.md
│   │   └── 003-extraccion-incremental-watermark.md
│   ├── architecture/                     # Arquitectura End-to-End del sistema
│   │   └── architecture_v1.md
│   └── database/                         # Esquema DDL y documentación del modelo relacional
│       ├── 01_init_schema.sql
│       └── data_model.md
├── src/
│   └── seeders/                          # Scripts de generación e inyección de datos sintéticos
│       └── generate_seed.py
├── tests/                                # Pruebas unitarias y de integración
├── .env                                  # Variables de entorno (no versionado en Git)
├── docker-compose.yml                    # Orquestación del contenedor PostgreSQL 15
└── README.md
```

## ⚙️ Configuración y Puesta en Marcha (Quickstart)

### 1. Variables de Entorno
Crea un archivo `.env` en la raíz del proyecto con las credenciales de conexión a la base de datos:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=clinicared_db
DB_USER=postgres
DB_PASSWORD=tu_password_seguro
```

### 2. Levantar la Base de Datos (Docker)
El contenedor aprovisiona y ejecuta automáticamente el esquema inicial (`docs/database/01_init_schema.sql`) al crearse por primera vez:

```bash
docker compose up -d
```

### 3. Activar Entorno Virtual y Poblar Datos (Seeder Idempotente)
Desde tu terminal de Ubuntu (WSL), activa tu entorno virtual y ejecuta el generador de datos sintéticos:

```bash
source venv/bin/activate
python src/seeders/generate_seed.py
```
> **Nota:** El script es 100% idempotente (limpia y reinicia las identidades antes de poblar) e incluye un parámetro configurable de inyección de defectos para pruebas de calidad de datos.

### 4. Verificar los Datos en el Contenedor
Puedes consultar el estado de las tablas directamente desde la terminal sin depender de clientes externos:

```bash
docker exec -it clinicared_postgres psql -U postgres -d clinicared_db -c "SELECT COUNT(*) FROM appointments;"
```

## 📐 Documentación de Arquitectura y ADRs

- **Arquitectura General:** [Arquitectura End-to-End v1](docs/architecture/architecture_v1.md)
- **Modelo de Datos Relacional:** [Documentación del Modelo de Datos](docs/database/data_model.md)
- **Registro de Decisiones de Arquitectura (ADRs):**
  - [ADR 001: Uso de PostgreSQL Contenerizado en Docker](docs/adr/001-motor-base-datos-y-docker.md)
  - [ADR 002: Estrategia de Poblado de Datos Idempotente e Inyección de Defectos](docs/adr/002-estrategia-seeding-idempotente-calidad.md)
  - [ADR 003: Estrategia de Extracción Incremental Basada en Watermark](docs/adr/003-extraccion-incremental-watermark.md)

## 🛠️ Estándares de Desarrollo y Flujo Git

Utilizamos **GitHub Flow**:
1. La rama `main` siempre es estable y refleja producción.
2. Todo desarrollo se integra primero en la rama `develop`.
3. Las ramas de trabajo deben seguir el formato: `feat/US01-nombre-tarea`, `fix/bug-name`, `docs/update-readme`.

### Convenciones de Commits (Conventional Commits)
- `feat:` Nuevas características.
- `fix:` Corrección de errores.
- `docs:` Cambios en la documentación.
- `chore:` Tareas de mantenimiento y configuración (ej. `chore: setup docker compose`).