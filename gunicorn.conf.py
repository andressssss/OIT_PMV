# gunicorn.conf.py

import multiprocessing

workers = multiprocessing.cpu_count() * 2 + 1

worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8000"

# Timeouts
timeout = 900
graceful_timeout = 60
keepalive = 5

# Recycling de workers para evitar fugas de memoria
max_requests = 50000
max_requests_jitter = 50

# Logs (stdout para que Docker los capture)
accesslog = "-"
errorlog = "-"
loglevel = "info"