"""
ETL: Lee los 26 ZIPs de importaciones del BCE y genera importaciones_ecuador.parquet
Fuente: BCE - Importaciones por Grupo, Subgrupo CUODE, Subpartida y País Origen
Valores originales: miles de USD (TM, FOB, CIF)
"""
import os
import zipfile
import pandas as pd

# ── Configuración ────────────────────────────────────────────────────
ZIP_DIR   = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "..", "exportaciones", "IMPORTACIONES")
OUTPUT    = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "importaciones_ecuador.parquet")
ANIOS     = list(range(2000, 2026))

MES_MAP = {
    "Ene": 1, "Feb": 2, "Mar": 3,  "Abr": 4,  "May": 5,  "Jun": 6,
    "Jul": 7, "Ago": 8, "Sep": 9,  "Oct": 10, "Nov": 11, "Dic": 12,
}

def parse_periodo(s):
    """'2024 / 01 - Ene' → (2024, 1)"""
    try:
        partes = str(s).strip().split("/")
        anio = int(partes[0].strip())
        mes_str = partes[1].strip().split("-")[1].strip()
        mes = MES_MAP.get(mes_str, None)
        return anio, mes
    except Exception:
        return None, None

def limpiar_numero(s):
    """'1.234,5' o '1,3' → float"""
    try:
        s = str(s).strip().replace(".", "").replace(",", ".")
        return float(s)
    except Exception:
        return None

def detectar_unidad(path, fname):
    """Detecta si los valores están en miles o millones de USD."""
    with zipfile.ZipFile(path) as z:
        with z.open(fname) as f:
            header = f.read(2000).decode("latin-1", errors="replace").lower()
    return "millones" if "millones" in header else "miles"


def leer_zip(anio):
    # 2007 tiene versión corregida con datos mensuales
    fname = f"{anio}f.zip" if anio == 2007 else f"{anio}.zip"
    path = os.path.join(ZIP_DIR, fname)

    # Detectar unidad del CSV
    unidad = detectar_unidad(path, "Columnas.csv")

    with zipfile.ZipFile(path) as z:
        with z.open("Columnas.csv") as f:
            df = pd.read_csv(
                f,
                encoding="latin-1",
                skiprows=6,
                header=0,
                sep=",",
                quotechar='"',
                on_bad_lines="skip",
                dtype=str,
            )

    # Renombrar por posición (col 3 es vacía)
    df.columns = [
        "Periodo", "Cod_Grupo", "Grupo", "_drop",
        "Cod_Subgrupo", "Subgrupo", "Cod_Subpartida", "Subpartida",
        "Pais_Origen", "TM", "FOB", "CIF"
    ]
    df = df.drop(columns=["_drop"])

    # Limpiar strings
    for col in ["Cod_Grupo", "Grupo", "Cod_Subgrupo", "Subgrupo",
                "Cod_Subpartida", "Subpartida", "Pais_Origen"]:
        df[col] = df[col].astype(str).str.strip()

    # Filtrar filas sin periodo válido
    df = df[df["Periodo"].str.match(r"^\d{4}\s*/", na=False)]

    # Parsear año y mes
    parsed = df["Periodo"].apply(parse_periodo)
    df["Anio"] = parsed.apply(lambda x: x[0])
    df["Mes"]  = parsed.apply(lambda x: x[1])
    df = df.dropna(subset=["Anio", "Mes"])
    df["Anio"] = df["Anio"].astype(int)
    df["Mes"]  = df["Mes"].astype(int)

    # Fecha como primer día del mes
    df["Fecha"] = pd.to_datetime(
        df["Anio"].astype(str) + "-" + df["Mes"].astype(str).str.zfill(2) + "-01"
    )

    # Convertir valores numéricos
    for col in ["TM", "FOB", "CIF"]:
        df[col] = df[col].apply(limpiar_numero)

    # Normalizar a miles de USD: si el CSV venía en millones, multiplicar x1000
    if unidad == "millones":
        for col in ["FOB", "CIF"]:
            df[col] = df[col] * 1000
        print(f"[{anio}: millones*1000]", end=" ")

    # Filtrar filas vacías (sin código de grupo válido)
    df = df[df["Cod_Grupo"].str.match(r"^\d+$", na=False)]
    df = df[df["CIF"].notna()]

    df = df.drop(columns=["Periodo"])
    return df


# ── Procesar todos los años ──────────────────────────────────────────
print("Procesando ZIPs de importaciones...")
partes = []
for anio in ANIOS:
    print(f"  {anio}...", end=" ")
    try:
        df = leer_zip(anio)
        partes.append(df)
        print(f"{len(df):,} filas")
    except Exception as e:
        print(f"ERROR: {e}")

# ── Concatenar y guardar ─────────────────────────────────────────────
print("\nConcatenando...")
df_total = pd.concat(partes, ignore_index=True)

# Tipos eficientes
for col in ["Cod_Grupo", "Grupo", "Cod_Subgrupo", "Subgrupo",
            "Cod_Subpartida", "Subpartida", "Pais_Origen"]:
    df_total[col] = df_total[col].astype("category")

print(f"Total filas: {len(df_total):,}")
print(f"Años: {df_total['Anio'].min()}–{df_total['Anio'].max()}")
print(f"Columnas: {df_total.columns.tolist()}")
print(f"Memoria: {df_total.memory_usage(deep=True).sum() / 1e6:.1f} MB")

df_total.to_parquet(OUTPUT, index=False)
print(f"\nGuardado: {OUTPUT}")
print(f"Tamaño: {os.path.getsize(OUTPUT)/1e6:.1f} MB")
