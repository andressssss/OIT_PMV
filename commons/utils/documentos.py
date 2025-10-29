from django.core.files.storage import default_storage
from rest_framework import status
from rest_framework.response import Response
from commons.models import T_docu
from rest_framework.exceptions import ValidationError

EXTENSIONES_PERMITIDAS = [
    "pdf", "jpg", "jpeg", "png", "ppt", "pptx", "mp3", "mp4", "xls", "psc", "sql", "zip",
    "rar", "7z", "docx", "doc", "dotx", "dotm", "docm", "dot", "htm", "html", "mht", "mhtml",
    "xlt", "xltx", "xltm", "xml", "xlsb", "xlsx", "csv", "pptm", "pps", "ppsx", "ppsm",
    "pot", "potx", "potm", "sldx", "sldm", "pst", "ost", "msg", "eml", "mdb", "accdb",
    "accde", "accdt", "accdr", "one", "pub", "vsd", "vsdx", "xps", "txt", "gif", "svg",
    "avi", "wav", "flac"
]


def guardar_documento(archivo, ruta, max_size_mb=50):
    """
    Guarda un archivo validando extensión y tamaño.
    Retorna instancia de T_docu si es válido o Response con error si no.

    Parámetros:
      - archivo: File recibido desde request.FILES
      - ruta: ruta donde se guardará el archivo en el storage
      - max_size_mb: tamaño máximo permitido (por defecto 50 MB)
    """
    if not archivo:
        raise ValidationError("No se proporcionó ningún archivo")

    extension = archivo.name.split('.')[-1].lower()

    # Validar extensión
    if extension not in EXTENSIONES_PERMITIDAS:
        raise ValidationError({"message": f"{archivo.name}: tipo no permitido"})

    max_size = max_size_mb * 1024 * 1024

    if archivo.size > max_size:
        raise ValidationError({
            "message": f"{archivo.name}: excede tamaño máximo "
            f"({'1GB' if max_size > 50*1024*1024 else '50MB'})"})

    try:
        ruta_guardada = default_storage.save(ruta, archivo)
    except Exception as e:
        raise ValidationError({"archivo": f"Error al guardar el archivo: {e}"})

    size = (
        f"{archivo.size} B" if archivo.size < 1024 else
        f"{archivo.size // 1024} KB"
    )

    # Crear registro en base de datos
    try:
        new_docu = T_docu.objects.create(
            nom=archivo.name,
            tipo=extension,
            tama=size,
            archi=ruta_guardada,
            priva="No",
            esta="Activo"
        )
    except Exception as e:
        default_storage.delete(ruta_guardada)
        raise ValidationError(
            {"archivo": f"Error al registrar el documento: {e}"})
    return new_docu
