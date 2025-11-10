"""
Comando Django para ejecutar el proceso ETL de juicios evaluativos.
----------------------------
Este comando toma un archivo Excel con las evaluaciones y ejecuta
el proceso de extracción, transformación y carga (ETL) definido en
`commons.etl.evaluaciones`.

Uso:
    python manage.py cargar_juicios <file_path> [--chunksize 5000]

Ejemplo:
    python manage.py cargar_juicios data/evaluaciones.xlsx --chunksize 10000
    
Argumentos:
    file_path   Ruta del archivo Excel con las evaluaciones.
    
Opciones:
    --chunksize Tamaño del lote de lectura (por defecto: 5000 filas).

----------------------------------------------------------------------
CHANGELOG
----------------------------------------------------------------------
    v1.1.0 (2025-11-07) - Mejora estructural al archivo
      - Añadido tipado (PEP 484)
      - Incluidas variables __author__ y __version__
      - Implementado logging para trazabilidad
      - Manejo de errores más específico (FileNotFoundError, Exception)
      - Documentación completa (PEP 257)
      - Pasado `chunksize` al método run_etl

    v1.0.0 (2025-10-25) - Versión inicial del comando `etl_evaluaciones`

----------------------------------------------------------------------
"""

__author__ = "Andrés Sanabria"
__version__ = "1.1.0"

import logging
from django.core.management.base import BaseCommand, CommandError
from commons.etl import evaluaciones


# Configurar logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Comando de Django que ejecuta el proceso ETL de evaluaciones."""

    help = "Ejecuta el ETL de evaluaciones desde un archivo Excel."

    def add_arguments(self, parser) -> None:
        """Define los argumentos disponibles para el comando."""
        parser.add_argument(
            "file_path",
            type=str,
            help="Ruta al archivo Excel con las evaluaciones."
        )
        parser.add_argument(
            "--chunksize",
            type=int,
            default=5000,
            help="Tamaño de los chunks para lectura del Excel (default: 5000)."
        )

    def handle(self, *args: tuple, **options: dict) -> None:
        """Ejecuta la lógica principal del comando."""
        file_path: str = options["file_path"]
        chunksize: int = options["chunksize"]

        self.stdout.write(self.style.NOTICE(
            f"Iniciando ETL de evaluaciones: {file_path} (chunksize={chunksize})"
        ))

        try:
            evaluaciones.run_etl(file_path, chunksize=chunksize)

        except FileNotFoundError:
            msg = f"El archivo '{file_path}' no existe."
            logger.error(msg)
            raise CommandError(msg)

        except Exception as e:
            msg = f"Error ejecutando ETL: {e}"
            logger.exception(msg)
            raise CommandError(msg)

        else:
            self.stdout.write(self.style.SUCCESS("✅ ETL finalizado con éxito"))
            logger.info(f"ETL finalizado correctamente para {file_path}")
