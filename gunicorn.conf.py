# gunicorn.conf.py

import multiprocessing

# Workers: 2 × cores + 1  → con 4 cores, 9 workers
workers = multiprocessing.cpu_count() * 2 + 1

worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8000"

# Timeouts
timeout = 120             # segundos antes de matar peticiones largas
graceful_timeout = 30     # segundos para apagado gracioso
keepalive = 5             # segundos de keep-alive por conexión

# Recycling de workers para evitar fugas de memoria
max_requests = 1000
max_requests_jitter = 50

# Logs (stdout para que Docker los capture)
accesslog = "-"           # stdout
errorlog = "-"            # stderr
loglevel = "info"