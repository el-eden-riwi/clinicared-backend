# ==========================================
# ETAPA 1: Builder (Compilación de dependencias)
# ==========================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Instalar herramientas para compilar psycopg2 y extensiones C
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Compilar dependencias directamente en formato wheel
RUN pip install --no-cache-dir --user -r requirements.txt


# ==========================================
# ETAPA 2: Runtime (Imagen limpia y segura)
# ==========================================
FROM python:3.11-slim AS runner

WORKDIR /app

# Instalar únicamente la librería de enlace en tiempo de ejecución (sin gcc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Crear un usuario no privilegiado para ejecutar la aplicación
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -s /bin/bash -m appuser

# Copiar las librerías instaladas desde la etapa builder
COPY --from=builder /root/.local /home/appuser/.local

# Asegurar que los binarios copiados estén en el PATH del nuevo usuario
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copiar el código fuente y asignar propiedad al usuario no privilegiado
COPY --chown=appuser:appgroup ./src ./src

# Cambiar al usuario seguro
USER appuser

EXPOSE 8000

# Healthcheck para que AWS ECS/Fargate monitoree la salud del contenedor
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/docs || exit 1

# Ejecutar Uvicorn con 2 workers para producción
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]