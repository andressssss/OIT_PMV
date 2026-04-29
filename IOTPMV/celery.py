import os
from celery import Celery

django_env = os.getenv("DJANGO_ENV", "dev")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"IOTPMV.settings.{django_env}")

app = Celery("IOTPMV")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
