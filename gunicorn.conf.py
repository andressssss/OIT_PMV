# gunicorn.conf.py
workers = 4  # Número de workers (ajusta según los recursos de tu máquina)
worker_class = "uvicorn.workers.UvicornWorker"  # Usa Uvicorn como worker
bind = "0.0.0.0:8000"  # Escucha en todas las interfaces, puerto 8000