# jui/tasks.py
from celery import shared_task
from .etl.evaluaciones import run_etl


@shared_task
def cargar_evaluaciones_task(file_path):
    """
    Task Celery que corre el ETL en background
    """
    run_etl(file_path)
    return f"ETL completado para {file_path}"
