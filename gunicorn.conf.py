import os

env = os.getenv('DJANGO_ENV', 'dev').lower()

if env in ['pre', 'prod']:
    workers = 4
    timeout = 120
else:
    workers = 1
    timeout = 60

worker_class = "uvicorn.workers.UvicornWorker"
bind = "0.0.0.0:8000"
loglevel = "info"
