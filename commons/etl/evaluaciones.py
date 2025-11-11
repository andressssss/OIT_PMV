"""
ETL de Juicios de Evaluación
=============================

Este módulo ejecuta un proceso ETL (Extract, Transform, Load) sobre archivos Excel
que contienen información de juicios de evaluación. Los datos se sincronizan con
las tablas `T_jui_eva_actu` y `T_jui_eva_diff`.

Ejemplo:
    >>> from commons.etl import juicios
    >>> juicios.run_etl("/etl_data/evaluaciones.xlsx", chunksize=5000)

Args:
    file_path (str): Ruta del archivo Excel (.xlsx) a procesar.
    chunksize (int, opcional): Tamaño de lote de lectura. Por defecto 5000.

Changelog:
    - **v1.0.0 (2025-11-01):** Versión inicial del ETL.
    - **v1.1.0 (2025-11-05):** Cache de entidades en memoria.
    - **v1.2.0 (2025-11-07):** Mejora estructural, manejo de errores y logging.
    - **v2.0.0 (2025-11-11):** Adaptación al nuevo esquema de datos.
"""


__author__ = "Andrés Sanabria"
__version__ = "2.0.0"

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
from typing import Any, Generator, Optional, Sequence
import logging
import os
import pandas as pd

# === CONFIG ===
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
def extract(file_path: str, chunksize: int) -> Generator[pd.DataFrame, None, None]:
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

    for chunk in pd.read_csv(csv_path, dtype=str, chunksize=chunksize):
        yield chunk


def transform(chunk: pd.DataFrame) -> tuple[list[dict[str, Any]], int]:
    """
    Transforma datos crudos de un fragmento (chunk) del CSV a registros validados.

    Args:
        chunk (pd.DataFrame): Fragmento del dataset leído por `extract()`.

    Returns:
        tuple[list[dict[str, Any]], int]: Lista de registros válidos y cantidad
        de errores encontrados durante la transformación.
    """
    registros: list[dict[str, Any]] = []
    errores: int = 0
    juicio_cols: list[int] = [col for col in chunk.columns if col.isdigit()]
    fecha_repor: datetime = datetime.now()

    for _, row in chunk.iterrows():
        try:
            if pd.isna(row.get("NUM_DOC_IDENTIDAD")) or pd.isna(row.get("ID_FICHA")):
                logger.warning(f"Fila con datos incompletos: {row.to_dict()}")
                errores += 1
                continue

            dni = clean_dni(row.get("NUM_DOC_IDENTIDAD"))
            ficha_num = row.get("ID_FICHA")

            ficha = cache_fichas.get(ficha_num)
            if ficha is None:
                ficha = T_ficha.objects.filter(num=ficha_num).first()
                cache_fichas[ficha_num] = ficha
                if not ficha:
                    logger.warning(f"Ficha no encontrada: {ficha_num}")
                    errores += 1
                    continue

            perfil = cache_perfiles.get(dni)
            if perfil is None:
                perfil = T_perfil.objects.filter(dni=dni).first()
                cache_perfiles[dni] = perfil
                if not perfil:
                    logger.warning(f"Perfil no encontrado: {dni}")
                    errores += 1
                    continue

            apre = cache_apres.get(dni)
            if apre is None:
                apre = T_apre.objects.filter(perfil=perfil).first()
                cache_apres[dni] = apre
                if not apre:
                    logger.warning(f"Aprendiz no encontrado: {dni}")
                    errores += 1
                    continue

            for rap_cod in juicio_cols:
                eva = row.get(rap_cod)
                if not eva or str(eva).strip() == "":
                    continue

                rap = cache_raps.get(rap_cod)
                if rap is None:
                    rap = T_raps.objects.filter(cod=rap_cod).first()
                    cache_raps[rap_cod] = rap
                    if not rap:
                        logger.warning(f"RAP no encontrado: {rap_cod}")
                        errores += 1
                        continue

                registros.append({
                    "fecha_repor": fecha_repor,
                    "ficha": ficha,
                    "apre": apre,
                    "rap": rap,
                    "eva": eva,
                })

        except (AttributeError, ValueError, TypeError) as e:
            errores += 1
            logger.warning(f"Error de datos: {e}")
        except Exception as e:
            errores += 1
            logger.error(f"Error transformando fila {row.to_dict()} → {e}", exc_info=True)

    return registros, errores


def load(registros: Sequence[dict[str, Any]]) -> tuple[int, int, int]:
    """
    Carga los registros transformados en la base de datos.

    Args:
        registros (Sequence[dict[str, Any]]): Lista de registros validados y listos
            para ser persistidos en la base de datos.

    Returns:
        tuple[int, int, int]: Tupla con las cantidades de registros nuevos,
        actualizados y sin cambios.
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
                    ficha=r["ficha"], apre=r["apre"],
                    tipo_cambi="nuevo", descri=f"Evaluación inicial {r['eva']}"
                ))
            else:
                cambios = []
                if existente.eva != r["eva"]:
                    cambios.append(f"eva: {existente.eva} -> {r['eva']}")
                    existente.eva = r["eva"]

                if cambios:
                    actualizar_objs.append(existente)
                    diffs.append(T_jui_eva_diff(
                        ficha=r["ficha"], apre=r["apre"],
                        tipo_cambi="actualizado", descri="; ".join(cambios),
                        jui=existente
                    ))
                else:
                    sin_cambios.append(clave)

        if nuevos_objs:
            T_jui_eva_actu.objects.bulk_create(nuevos_objs, batch_size=5000)

        if actualizar_objs:
            campos = ["eva"]
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
def run_etl(file_path: str, chunksize: int = 5000) -> None:
    """Orquesta la ejecución completa del ETL."""
    logger.info("=== INICIO ETL ===")

    total = {"leidas": 0, "validas": 0, "errores": 0,
             "nuevos": 0, "actualizados": 0, "sin_cambios": 0}

    for chunk in extract(file_path, chunksize=chunksize):
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
