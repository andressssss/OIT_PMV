"""
ETL de Juicios de Evaluación
----------------------------
Este módulo ejecuta un proceso ETL (Extract, Transform, Load) sobre archivos Excel
que contienen información de juicios de evaluación, sincronizando los datos
en las tablas `T_jui_eva_actu` y `T_jui_eva_diff`.

Uso:
    from commons.etl import juicios
    juicios.run_etl("ruta/al/archivo.xlsx")

Argumentos:
    file_path (str): Ruta del archivo Excel (.xlsx) a procesar.

----------------------------------------------------------------------
CHANGELOG
----------------------------------------------------------------------
    v1.2.0 (2025-11-07) - Mejora estructural:
        - Se agregaron type hints (PEP484)
        - Se documentaron funciones con docstrings estandarizados
        - Se mejoró manejo de errores y logging
        - Se corrigió formato de logs con timestamp por ejecución
        - Se aplicó estructura modular ETL
    v1.1.0 (2025-11-05) - Cache de entidades en memoria
    v1.0.0 (2025-11-01) - Versión inicial del ETL
----------------------------------------------------------------------
"""

__author__ = "Andrés Sanabria"
__version__ = "1.2.0"

from commons.models import (
    T_jui_eva_actu,
    T_jui_eva_diff,
    T_ficha,
    T_apre,
    T_raps,
    T_instru,
    T_perfil
)
from datetime import datetime, date
from django.db import transaction
from typing import Any, Generator, Optional
import logging
import os
import pandas as pd

# === CONFIG ===
CHUNK_SIZE: int = 5000
UPDATE_THRESHOLD: int = 100
LOG_DIR: str = "logs/juicios"
os.makedirs(LOG_DIR, exist_ok=True)

# === LOGGER ===


def get_logger() -> logging.Logger:
    """Crea un logger por ejecución con salida a consola y archivo"""
    logger = logging.getLogger("etl_juicios")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    now = datetime.now()
    fecha_dir = now.strftime("%Y-%m-%d")
    hora_stamp = now.strftime("%H%M%S")

    # Crear carpeta por fecha
    log_subdir = os.path.join(LOG_DIR, fecha_dir)
    os.makedirs(log_subdir, exist_ok=True)

    log_file = os.path.join(log_subdir, f"etl_log_{hora_stamp}.txt")

    fh = logging.FileHandler(log_file, encoding="utf-8")
    ch = logging.StreamHandler()
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    fh.setFormatter(fmt)
    ch.setFormatter(fmt)

    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger


logger = get_logger()


# === HELPERS ===
def safe_date(value: any) -> Optional[date]:
    """Convierte valores en fechas válidas o devuelve None si no es posible."""
    if pd.isna(value) or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    try:
        return pd.to_datetime(value, errors="coerce").date()
    except Exception:
        return None


def clean_dni(dni) -> Optional[str]:
    """Normaliza documentos de identidad extrayendo solo dígitos."""
    if pd.isna(dni):
        return None
    return "".join(ch for ch in str(dni) if ch.isdigit())


# === CACHES ===
cache_fichas: dict[str, Optional[T_ficha]] = {}
cache_perfiles: dict[str, Optional[T_perfil]] = {}
cache_apres: dict[str, Optional[T_apre]] = {}
cache_raps: dict[str, Optional[T_raps]] = {}
cache_instrus: dict[str, Optional[T_instru]] = {}


# === EXTRACT ===
def extract(file_path: str) -> Generator[pd.DataFrame, None, None]:
    """
    Convierte un archivo Excel a CSV temporal y lo lee por chunks.

    Args:
        file_path: Ruta al archivo Excel de entrada.

    Yields:
        pd.DataFrame: Fragmentos del dataset procesable por transform().
    """
    if not os.path.exists(file_path):
        logger.error(f"Archivo no encontrado: {file_path}")
        raise FileNotFoundError(f"El archivo '{file_path}' no existe.")
    csv_path = file_path.replace(".xlsx", ".csv")

    try:
        if not os.path.exists(csv_path):
            logger.info(f"Convirtiendo {file_path} → {csv_path}")
            df = pd.read_excel(file_path, engine="openpyxl")
            df.to_csv(csv_path, index=False)
    except PermissionError:
        logger.error(f"Permiso denegado para acceder a {file_path}")
        raise
    except Exception as e:
        logger.exception(f"Error leyendo Excel: {e}")
        raise

    for chunk in pd.read_csv(csv_path, dtype=str, chunksize=CHUNK_SIZE):
        yield chunk


def transform(chunk: pd.DataFrame) -> tuple[list[dict], int]:
    """
    Transforma datos crudos del chunk a registros validados.

    Args:
        chunk: Fragmento del CSV.

    Returns:
        tuple[list[dict], int]: Lista de registros válidos y cantidad de errores.
    """
    registros: list[dict] = []
    errores = 0

    for _, row in chunk.iterrows():
        try:
            fecha_repor = safe_date(row.get("FECHA_REPORTE"))
            ficha_num = row.get("FICHA")
            dni = clean_dni(row.get("NRO_DOC"))
            rap_cod = row.get("RESULTADO_ID")
            eva = row.get("EVALUACIÓN")
            fecha_eva = safe_date(row.get("FCH_EVALUACION"))
            instru_doc = clean_dni(row.get("INTRUCT_RESPONSABLE"))

            # Resolver entidades con cache
            ficha = cache_fichas.get(ficha_num)
            if ficha_num not in cache_fichas:
                ficha = T_ficha.objects.filter(num=ficha_num).first()
                cache_fichas[ficha_num] = ficha
                if not ficha:
                    logger.warning(f"Ficha no encontrada: {ficha_num}")
                    errores += 1
                    continue

            perfil = cache_perfiles.get(dni)
            if dni not in cache_perfiles:
                perfil = T_perfil.objects.filter(dni=dni).first()
                cache_perfiles[dni] = perfil
                if not perfil:
                    logger.warning(f"Perfil no encontrado: {dni}")
                    errores += 1
                    continue

            apre = cache_apres.get(dni)
            if dni not in cache_apres:
                apre = T_apre.objects.filter(perfil=perfil).first()
                cache_apres[dni] = apre
                if not apre:
                    logger.warning(f"Aprendiz no encontrado: {dni}")
                    errores += 1
                    continue

            rap = cache_raps.get(rap_cod)
            if rap_cod not in cache_raps:
                rap = T_raps.objects.filter(cod=rap_cod).first()
                cache_raps[rap_cod] = rap
                if not rap:
                    logger.warning(f"RAP no encontrado: {rap_cod}")
                    errores += 1
                    continue

            instru = None
            if instru_doc:
                instru = cache_instrus.get(instru_doc)
                if instru_doc not in cache_instrus:
                    perfil_instru = T_perfil.objects.filter(
                        dni=instru_doc).first()
                    instru = (
                        T_instru.objects.filter(perfil=perfil_instru).first()
                        if perfil_instru else None
                    )
                    cache_instrus[instru_doc] = instru
                    if not instru:
                        logger.warning(
                            f"Instructor no encontrado: {instru_doc}")

            registros.append({
                "fecha_repor": fecha_repor,
                "ficha": ficha,
                "apre": apre,
                "rap": rap,
                "eva": eva,
                "fecha_eva": fecha_eva,
                "instru": instru,
            })

        except Exception as e:
            errores += 1
            logger.error(f"Error transformando fila {row.to_dict()} → {e}")

    return registros, errores


def load(registros: list[dict]) -> tuple[int, int, int]:
    """
    Carga los registros transformados en la base de datos.

    Args:
        registros: Lista de registros listos para persistencia.

    Returns:
        tuple[int, int, int]: Cantidades de nuevos, actualizados y sin cambios.
    """
    nuevos_objs, actualizar_objs, diffs, sin_cambios = [], [], [], []

    fichas_ids = {r["ficha"].id for r in registros}
    existentes = {
        (e.ficha_id, e.apre_id, e.rap_id): e
        for e in T_jui_eva_actu.objects.filter(ficha_id__in=fichas_ids)
    }

    with transaction.atomic():
        for r in registros:
            clave = (r["ficha"].id, r["apre"].id, r["rap"].id)
            existente = existentes.get(clave)

            if not existente:
                nuevos_objs.append(T_jui_eva_actu(**r))
                diffs.append(T_jui_eva_diff(
                    ficha=r["ficha"], apre=r["apre"], instru=r["instru"],
                    tipo_cambi="nuevo", descri=f"Evaluación inicial {r['eva']}"
                ))
            else:
                cambios = []
                if existente.eva != r["eva"]:
                    cambios.append(f"eva: {existente.eva} -> {r['eva']}")
                    existente.eva = r["eva"]
                if existente.fecha_eva != r["fecha_eva"]:
                    cambios.append(
                        f"fecha_eva: {existente.fecha_eva} -> {r['fecha_eva']}")
                    existente.fecha_eva = r["fecha_eva"]
                if existente.instru_id != (r["instru"].id if r["instru"] else None):
                    cambios.append(
                        f"instru: {existente.instru} -> {r['instru']}")
                    existente.instru = r["instru"]

                if cambios:
                    actualizar_objs.append(existente)
                    diffs.append(T_jui_eva_diff(
                        ficha=r["ficha"], apre=r["apre"], instru=r["instru"],
                        tipo_cambi="actualizado", descri="; ".join(cambios),
                        jui=existente
                    ))
                else:
                    sin_cambios.append(clave)

        if nuevos_objs:
            T_jui_eva_actu.objects.bulk_create(nuevos_objs, batch_size=5000)

        if actualizar_objs:
            campos = ["eva", "fecha_eva", "instru"]
            if len(actualizar_objs) > UPDATE_THRESHOLD:
                T_jui_eva_actu.objects.bulk_update(
                    actualizar_objs, campos, batch_size=5000)
            else:
                for obj in actualizar_objs:
                    obj.save(update_fields=campos)

        if diffs:
            T_jui_eva_diff.objects.bulk_create(diffs, batch_size=5000)

    logger.info(
        f"Resumen → Nuevos: {len(nuevos_objs)}, "
        f"Actualizados: {len(actualizar_objs)}, "
        f"Sin cambios: {len(sin_cambios)}"
    )

    return len(nuevos_objs), len(actualizar_objs), len(sin_cambios)


# === MAIN ===
def run_etl(file_path: str) -> None:
    """Orquesta la ejecución completa del ETL."""
    logger.info("=== INICIO ETL ===")

    total = {"leidas": 0, "validas": 0, "errores": 0,
             "nuevos": 0, "actualizados": 0, "sin_cambios": 0}

    for chunk in extract(file_path):
        total["leidas"] += len(chunk)
        registros, errores = transform(chunk)
        total["validas"] += len(registros)
        total["errores"] += errores

        nuevos, actualizados, sin_cambios = load(registros)
        total["nuevos"] += nuevos
        total["actualizados"] += actualizados
        total["sin_cambios"] += sin_cambios

    logger.info("=== FIN ETL ===")
    logger.info(
        "Resumen total → "
        f"Leídas: {total['leidas']}, "
        f"Procesadas: {total['validas']}, "
        f"Errores: {total['errores']}, "
        f"Nuevos: {total['nuevos']}, "
        f"Actualizados: {total['actualizados']}, "
        f"Sin cambios: {total['sin_cambios']}"
    )
