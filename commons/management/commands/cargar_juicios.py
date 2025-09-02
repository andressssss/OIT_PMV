from django.core.management.base import BaseCommand, CommandError
from commons.etl import evaluaciones


class Command(BaseCommand):
    help = "Ejecuta el ETL de evaluaciones desde un archivo Excel"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            type=str,
            help="Ruta al archivo Excel con las evaluaciones"
        )

        parser.add_argument(
            "--chunksize",
            type=int,
            default=5000,
            help="Tamaño de los chunks para lectura del Excel (default: 5000)"
        )

    def handle(self, *args, **options):
        file_path = options["file_path"]
        chunksize = options["chunksize"]

        try:
            self.stdout.write(self.style.NOTICE(
                f"🚀 Iniciando ETL de evaluaciones para {file_path} con chunksize={chunksize}..."
            ))

            evaluaciones.run_etl(file_path)

            self.stdout.write(self.style.SUCCESS("✅ ETL finalizado con éxito"))

        except Exception as e:
            raise CommandError(f"Error ejecutando ETL: {e}")
