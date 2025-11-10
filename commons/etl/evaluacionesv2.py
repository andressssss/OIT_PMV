from datetime import datetime
import os
import logging
import pandas as pd
from django.db import transaction
from commons.models import (
    T_jui_eva_actu,
    T_jui_eva_diff,
    T_ficha,
    T_apre,
    T_raps,
    T_instru,
    T_perfil
)

# === CONFIG ===
CHUNK_SIZE = 5000
UPDATE_THRESHOLD = 100
LOG_DIR = "logs/juicios"
os.makedirs(LOG_DIR, exist_ok=True)

# === LOGGER ===
def get_logger():
    """Crea un logger por ejecución con salida a consola y archivo"""
    logger = logging.getLogger("etl_juicios")
    logger.setLevel(logging.INFO)

    # Evitar duplicación de handlers
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
def safe_date(value):
    """Convierte fecha a date seguro"""
    if pd.isna(value) or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    try:
        return pd.to_datetime(value).date()
    except Exception:
        return None


def clean_dni(dni):
    """Extrae solo los números del documento"""
    if pd.isna(dni):
        return None
    return "".join(ch for ch in str(dni) if ch.isdigit())



# === CACHES ===
cache_fichas = {}
cache_perfiles = {}
cache_apres = {}
cache_raps = {}
cache_instrus = {}


# === EXTRACT ===
def extract(file_path):
    """Convierte Excel → CSV para soportar chunks"""
    csv_path = file_path.replace(".xlsx", ".csv")

    if not os.path.exists(csv_path):
        logger.info(f"Convirtiendo {file_path} → {csv_path}")
        df = pd.read_excel(file_path, engine="openpyxl")
        df.to_csv(csv_path, index=False)

    for chunk in pd.read_csv(csv_path, dtype=str, chunksize=CHUNK_SIZE):
        yield chunk


def transform(chunk):
    registros = []
    errores = 0  # 👈 contador de errores

    for _, row in chunk.iterrows():
        try:
            fecha_repor = safe_date(row.get("FECHA_REPORTE"))
            ficha_num = row.get("FICHA")
            dni = clean_dni(row.get("NRO_DOC"))
            rap_cod = row.get("RESULTADO_ID")
            eva = row.get("EVALUACIÓN")
            fecha_eva = safe_date(row.get("FCH_EVALUACION"))
            instru_doc = clean_dni(row.get("INTRUCT_RESPONSABLE"))
            

            # --- Resolver Ficha ---
            if ficha_num not in cache_fichas:
                try:
                    cache_fichas[ficha_num] = T_ficha.objects.get(num=ficha_num)
                except T_ficha.DoesNotExist:
                    logger.warning(f"Ficha no encontrada: {ficha_num}")
                    cache_fichas[ficha_num] = None
            ficha = cache_fichas[ficha_num]
            if not ficha:
                errores += 1
                continue

            # --- Resolver Perfil ---
            if dni not in cache_perfiles:
                try:
                    cache_perfiles[dni] = T_perfil.objects.get(dni=dni)
                except T_perfil.DoesNotExist:
                    logger.warning(f"Perfil no encontrado: {dni}")
                    cache_perfiles[dni] = None
            perfil = cache_perfiles[dni]
            if not perfil:
                errores += 1
                continue

            # --- Resolver Aprendiz ---
            if dni not in cache_apres:
                try:
                    cache_apres[dni] = T_apre.objects.get(perfil=perfil)
                except T_apre.DoesNotExist:
                    logger.warning(f"Aprendiz no encontrado: {dni}")
                    cache_apres[dni] = None
            apre = cache_apres[dni]
            if not apre:
                errores += 1
                continue

            # --- Resolver RAP ---
            if rap_cod not in cache_raps:
                try:
                    cache_raps[rap_cod] = T_raps.objects.get(cod=rap_cod)
                except T_raps.DoesNotExist:
                    logger.warning(f"RAP no encontrado: {rap_cod}")
                    cache_raps[rap_cod] = None
            rap = cache_raps[rap_cod]
            if not rap:
                errores += 1
                continue

            # --- Resolver Instructor ---
            instru = None
            if instru_doc:
                if instru_doc not in cache_instrus:
                    try:
                        perfil_instru = T_perfil.objects.get(dni=instru_doc)
                        cache_instrus[instru_doc] = T_instru.objects.get(perfil=perfil_instru)
                    except (T_perfil.DoesNotExist, T_instru.DoesNotExist):
                        logger.warning(f"Instructor no encontrado: {instru_doc}")
                        cache_instrus[instru_doc] = None
                instru = cache_instrus[instru_doc]

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


def load(registros):
    nuevos_objs, actualizar_objs, diffs = [], [], []
    sin_cambios = []

    fichas_ids = {r["ficha"].id for r in registros}
    existentes = {
        (e.ficha_id, e.apre_id, e.rap_id): e
        for e in T_jui_eva_actu.objects.filter(ficha_id__in=fichas_ids)
    }

    with transaction.atomic():
        for r in registros:
            clave = (r["ficha"].id, r["apre"].id, r["rap"].id)

            if clave not in existentes:
                obj = T_jui_eva_actu(**r)
                nuevos_objs.append(obj)
                diffs.append(T_jui_eva_diff(
                    ficha=r["ficha"], apre=r["apre"], instru=r["instru"],
                    tipo_cambi="nuevo", descri=f"Evaluación inicial {r['eva']}"
                ))
                logger.info(
                    f"Nuevo → ficha {r['ficha'].id}, apre {r['apre'].id}, rap {r['rap'].id}, eva={r['eva']}, instru={r['instru']}"
                )

            else:
                existente = existentes[clave]
                cambios = []

                if existente.eva != r["eva"]:
                    cambios.append(f"eva: {existente.eva} -> {r['eva']}")
                    existente.eva = r["eva"]

                if existente.fecha_eva != r["fecha_eva"]:
                    cambios.append(f"fecha_eva: {existente.fecha_eva} -> {r['fecha_eva']}")
                    existente.fecha_eva = r["fecha_eva"]

                if existente.instru_id != (r["instru"].id if r["instru"] else None):
                    cambios.append(f"instru: {existente.instru} -> {r['instru']}")
                    existente.instru = r["instru"]

                if cambios:
                    actualizar_objs.append(existente)
                    diffs.append(T_jui_eva_diff(
                        ficha=r["ficha"], apre=r["apre"], instru=r["instru"],
                        tipo_cambi="actualizado", descri="; ".join(cambios),
                        jui=existente
                    ))
                    logger.info(
                        f"Actualizado → ficha {r['ficha'].id}, apre {r['apre'].id}, rap {r['rap'].id} | {', '.join(cambios)}"
                    )
                else:
                    sin_cambios.append(clave)

        # Insertar nuevos
        if nuevos_objs:
            T_jui_eva_actu.objects.bulk_create(nuevos_objs, batch_size=5000)

        # Actualizar existentes
        if actualizar_objs:
            if len(actualizar_objs) > UPDATE_THRESHOLD:
                T_jui_eva_actu.objects.bulk_update(
                    actualizar_objs, ["eva", "fecha_eva", "instru"], batch_size=5000
                )
            else:
                for obj in actualizar_objs:
                    obj.save(update_fields=["eva", "fecha_eva", "instru"])

        # Guardar diffs
        if diffs:
            T_jui_eva_diff.objects.bulk_create(diffs, batch_size=5000)

    for clave in sin_cambios:
        logger.info(f"Sin cambios → ficha {clave[0]}, apre {clave[1]}, rap {clave[2]}")

    logger.info(
        f"Resumen → Nuevos: {len(nuevos_objs)}, "
        f"Actualizados: {len(actualizar_objs)}, "
        f"Sin cambios: {len(sin_cambios)}"
    )
    
    return len(nuevos_objs), len(actualizar_objs), len(sin_cambios)


# === MAIN ===
def run_etl(file_path):
    logger.info("=== INICIO ETL ===")

    total_leidas = 0
    total_validas = 0
    total_errores = 0
    total_nuevos = 0
    total_actualizados = 0
    total_sin_cambios = 0

    for chunk in extract(file_path):
        total_leidas += len(chunk)  # 👈 todas las filas leídas
        registros, errores = transform(chunk)

        total_validas += len(registros)
        total_errores += errores

        nuevos, actualizados, sin_cambios = load(registros)
        total_nuevos += nuevos
        total_actualizados += actualizados
        total_sin_cambios += sin_cambios

    logger.info("=== FIN ETL ===")
    logger.info(
        f"Resumen total → Leídas: {total_leidas}, "
        f"Procesadas: {total_validas}, "
        f"Errores: {total_errores}, "
        f"Nuevos: {total_nuevos}, "
        f"Actualizados: {total_actualizados}, "
        f"Sin cambios: {total_sin_cambios}"
    )
