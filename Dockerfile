# Imagen base de Python
From python:3.9-slim

# Directorio de trabajo
WORKDIR /app

# Copia el archivo de requisitos e instala las dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del codigo de la aplicacion
COPY . .

# Exponer el puerto 8000 para gunicorn 
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["gunicorn", "myproject.asgi:application", "-c", "gunicorn.conf.py"]
