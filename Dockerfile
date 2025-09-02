# Usar una imagen base oficial de Python
FROM python:3.11-slim

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema para Cairo y otras necesarias
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    libcairo2-dev \
    meson \
    && rm -rf /var/lib/apt/lists/*

# Copiar solo el archivo de requisitos e instalar las dependencias
COPY requirements.txt .

# Instalar las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código de la aplicación, evitando archivos innecesarios (si los hay)
COPY . .

# Exponer el puerto 8000 para gunicorn
EXPOSE 8000

# Comando para ejecutar la aplicación con gunicorn
CMD ["gunicorn", "IOTPMV.asgi:application", "-k", "uvicorn.workers.UvicornWorker", "-c", "gunicorn.conf.py"]
