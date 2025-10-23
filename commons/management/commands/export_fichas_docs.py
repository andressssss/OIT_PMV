import os
import csv
import shutil
import zipfile
import tempfile
from django.core.management.base import BaseCommand
from commons.models import T_DocumentFolder, T_ficha

# Ajusta las rutas de carpetas que deseas exportar
TARGET_PATHS = [
    "4. GFPI-F-023-PLANEACIÓN, SEGUIMIENTO Y EVALUACIÓN ETAPA PRODUCTIVA > GFPI-F-023-PLANEACIÓN, SEGUIMIENTO Y EVALUACIÓN ETAPA PRODUCTIVA",
    "8. FORMATO DE HOMOLOGACIÓN"
]


class Command(BaseCommand):
    help = "Exporta los documentos de las fichas desde las dos carpetas MPTT específicas y genera un log CSV."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output",
            type=str,
            default="./export_fichas",
            help="Ruta base donde se guardarán los ZIPs y el log CSV",
        )

    def handle(self, *args, **options):
        base_dir = options["output"]
        os.makedirs(base_dir, exist_ok=True)
        log_path = os.path.join(base_dir, "faltantes.csv")

        self.stdout.write(self.style.SUCCESS(f"Iniciando exportación en: {base_dir}"))
        faltantes = []

        fichas = T_ficha.objects.all()
        total = fichas.count()
        self.stdout.write(f"Procesando {total} fichas...\n")

        for i, ficha in enumerate(fichas.iterator(chunk_size=50), start=1):
            try:
                self.stdout.write(f"[{i}/{total}] Ficha ID: {ficha.id}")
                target_folders = self.get_target_folders(ficha)

                if not target_folders:
                    faltantes.append((ficha.id, "Sin estructura"))
                    continue

                temp_dir = tempfile.mkdtemp()
                ficha_dir = os.path.join(temp_dir, f"ficha_{ficha.id}")
                os.makedirs(ficha_dir, exist_ok=True)

                has_docs = False
                for folder in target_folders:
                    docs = self.get_documents_from_folder(folder)
                    folder_dir = os.path.join(
                        ficha_dir, folder.name.replace("/", "_")[:60]
                    )
                    os.makedirs(folder_dir, exist_ok=True)

                    if not docs:
                        faltantes.append((ficha.num if ficha.num else f"G{ficha.grupo_id}", f"Sin documentos en {folder.name}"))
                        continue

                    for doc in docs:
                        file_field = getattr(doc, "archi", None)
                        if file_field and file_field.path and os.path.exists(file_field.path):
                            shutil.copy(file_field.path, folder_dir)
                            has_docs = True
                        else:
                            faltantes.append(
                                (ficha.num if ficha.num else f"G{ficha.grupo_id}", f"Documento no encontrado o sin archivo: {doc.nom}")
                            )

                if has_docs:
                    zip_path = os.path.join(base_dir, f"ficha_{ficha.num}.zip" if ficha.num else f"ficha_G{ficha.grupo_id}.zip")
                    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                        for root, _, files in os.walk(ficha_dir):
                            for f in files:
                                full_path = os.path.join(root, f)
                                rel_path = os.path.relpath(full_path, ficha_dir)
                                zipf.write(full_path, rel_path)

                shutil.rmtree(temp_dir)

            except Exception as e:
                faltantes.append((ficha.id, f"Error: {str(e)}"))

        # Guardar log de faltantes
        with open(log_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Ficha_ID", "Observación"])
            writer.writerows(faltantes)

        self.stdout.write(self.style.SUCCESS(f"\nProceso completado. Log guardado en {log_path}"))

    # === Funciones auxiliares ===

    def get_target_folders(self, ficha):
        """Busca las carpetas objetivo dentro del árbol de la ficha."""
        folders = []
        for path in TARGET_PATHS:
            parts = [p.strip() for p in path.split(">")]
            current_parent = None
            for name in parts:
                folder = T_DocumentFolder.objects.filter(
                    name=name, ficha=ficha, parent=current_parent
                ).first()
                if not folder:
                    current_parent = None
                    break
                current_parent = folder
            if current_parent:
                folders.append(current_parent)
        return folders

    def get_documents_from_folder(self, folder):
        """Obtiene todos los documentos reales (T_docu) bajo una carpeta dada."""
        descendants = folder.get_descendants(include_self=True)
        documents = [
            node.documento
            for node in descendants
            if node.tipo == "documento" and node.documento
        ]
        return documents
