# ClínicaRed - Backend Platform

Plataforma backend para la gestión de citas médicas, pacientes y especialidades.

## 🚀 Prerrequisitos
- PostgreSQL 14+
- Python 3.10+ (o Node.js, según el stack que elijas)
- Docker & Docker Compose (Recomendado)

## 📁 Estructura del Proyecto
- `/docs`: Documentación técnica, ADRs y diagramas de base de datos (`data_model.md`).
- `/src`: Código fuente principal de la API.
- `/tests`: Pruebas unitarias y de integración.

## 🛠️ Estándares de Desarrollo y Flujo Git

Utilizamos **GitHub Flow**.
1. La rama `main` siempre es estable y refleja producción.
2. Todo desarrollo se integra primero en la rama `develop`.
3. Ramas de trabajo deben seguir el formato: `feat/US01-nombre-tarea`, `fix/bug-name`, `docs/update-readme`.

### Convenciones de Commits (Conventional Commits)
- `feat:` Nuevas características.
- `fix:` Corrección de errores.
- `docs:` Cambios en la documentación.
- `chore:` Tareas de mantenimiento (ej. `chore: setup initial structure`).