"""
Módulo compartido: carga de datos y preprocesamiento de importaciones.
Fuente: BCE - Importaciones por Grupo, Subgrupo CUODE, Subpartida y País Origen
"""
import os
import streamlit as st
import pandas as pd

# ── Clasificación CUODE ──────────────────────────────────────────────
GRUPO_MAP = {
    "01": "Bienes de Consumo No Duradero",
    "02": "Bienes de Consumo Duradero",
    "03": "Combustibles y Lubricantes",
    "04": "Mat. Primas Agropecuarias",
    "05": "Mat. Primas Industriales",
    "06": "Materiales de Construcción",
    "07": "Bienes de Capital Agrícola",
    "08": "Bienes de Capital Industrial",
    "09": "Equipo de Transporte",
    "10": "Diversos",
    "99": "Tráfico Postal",
}

SUBGRUPO_MAP = {
    "011": "Productos Alimenticios",
    "012": "Bebidas",
    "013": "Tabaco",
    "014": "Productos Farmacéuticos y de Tocador",
    "015": "Vestuario y Confecciones",
    "019": "Otros Bienes de Consumo No Duradero",
    "021": "Utensilios Domésticos",
    "022": "Objetos de Adorno y Uso Personal",
    "023": "Muebles y Equipo para el Hogar",
    "024": "Máquinas y Aparatos de Uso Doméstico",
    "025": "Vehículos de Transporte Particular",
    "029": "Armas y Equipo Militar",
    "031": "Combustibles",
    "032": "Lubricantes",
    "033": "Electricidad",
    "041": "Alimentos para Animales",
    "042": "Otras Materias Primas Agrícolas",
    "051": "Productos Alimenticios para la Industria",
    "052": "Prod. Agropecuarios no Alimenticios",
    "053": "Productos Mineros para la Industria",
    "055": "Productos Químicos y Farmacéuticos",
    "061": "Materiales de Construcción",
    "071": "Máquinas y Herramientas Agrícolas",
    "072": "Otro Equipo Agrícola",
    "073": "Material de Transporte Agrícola",
    "081": "Máquinas de Oficina y Científicas",
    "082": "Herramientas Industriales",
    "083": "Partes y Accesorios de Maquinaria",
    "084": "Maquinaria Industrial",
    "085": "Otro Equipo Fijo Industrial",
    "091": "Partes y Accesorios de Transporte",
    "092": "Equipo Rodante de Transporte",
    "093": "Equipo Fijo de Transporte",
    "100": "Diversos",
    "999": "Tráfico Postal",
}

# Colores por grupo CUODE
GRUPO_COLORS = {
    "Bienes de Consumo No Duradero": "#16a34a",   # Verde
    "Bienes de Consumo Duradero":    "#22c55e",   # Verde claro
    "Combustibles y Lubricantes":    "#000000",   # Negro
    "Mat. Primas Agropecuarias":     "#ca8a04",   # Dorado
    "Mat. Primas Industriales":      "#2563eb",   # Azul
    "Materiales de Construcción":    "#92400e",   # Marrón
    "Bienes de Capital Agrícola":    "#15803d",   # Verde oscuro
    "Bienes de Capital Industrial":  "#1d4ed8",   # Azul oscuro
    "Equipo de Transporte":          "#dc2626",   # Rojo
    "Diversos":                      "#9ca3af",   # Gris
    "Tráfico Postal":                "#d1d5db",   # Gris claro
}

# Regiones geográficas (misma lógica que exportaciones)
_REGION_PATTERNS = [
    ("ESTADOS UNIDOS", "América del Norte"), ("CANAD", "América del Norte"),
    ("MEXIC", "América del Norte"), ("MÉXIC", "América del Norte"),
    ("ALEMANI", "Europa"), ("ESPAÑ", "Europa"), ("FRANCI", "Europa"),
    ("ITALI", "Europa"), ("HOLANDA", "Europa"), ("PAÍSES BAJOS", "Europa"),
    ("REINO UNIDO", "Europa"), ("BÉLGI", "Europa"), ("BELGI", "Europa"),
    ("RUSI", "Europa"), ("SUIZ", "Europa"), ("PORTUG", "Europa"),
    ("SUECI", "Europa"), ("POLONI", "Europa"), ("GRECI", "Europa"),
    ("TURQU", "Europa"), ("UCRANI", "Europa"), ("NORUEG", "Europa"),
    ("DINAMARC", "Europa"), ("FINLANDI", "Europa"), ("IRLAND", "Europa"),
    ("RUMANI", "Europa"), ("AUSTRI", "Europa"), ("CHECA", "Europa"),
    ("BULGARI", "Europa"), ("ESLOVENI", "Europa"), ("LITUANI", "Europa"),
    ("CROACI", "Europa"), ("MONTENEGR", "Europa"), ("HUNGR", "Europa"),
    ("LUXEMBURG", "Europa"), ("BELAR", "Europa"), ("MOLDOV", "Europa"),
    ("CHIPRE", "Europa"), ("SERBIA", "Europa"), ("ALBANI", "Europa"),
    ("CHINA", "Asia"), ("JAPÓN", "Asia"), ("JAPON", "Asia"),
    ("COREA (SUR", "Asia"), ("COREA DEL SUR", "Asia"),
    ("INDIA", "Asia"), ("INDONESI", "Asia"), ("TAILANDI", "Asia"),
    ("VIETNAM", "Asia"), ("MALASI", "Asia"), ("FILIPIN", "Asia"),
    ("TAIW", "Asia"), ("SINGAPUR", "Asia"), ("HONG KONG", "Asia"),
    ("PAKIST", "Asia"), ("BANGLADESH", "Asia"),
    ("KAZAJIST", "Asia"), ("AZERBAIY", "Asia"),
    ("ARABIA SAUDITA", "Medio Oriente"), ("EMIRATOS", "Medio Oriente"),
    ("ISRAEL", "Medio Oriente"), ("IRÁN", "Medio Oriente"), ("IRAN", "Medio Oriente"),
    ("IRAK", "Medio Oriente"), ("KUWAIT", "Medio Oriente"),
    ("QATAR", "Medio Oriente"), ("OMÁN", "Medio Oriente"),
    ("AUSTRALIA", "Oceanía"), ("NUEVA ZELAND", "Oceanía"),
    ("SUDÁFRICA", "África"), ("SUDAFRICA", "África"),
    ("EGIPTO", "África"), ("NIGERIA", "África"), ("MARRUECOS", "África"),
    ("KENYA", "África"), ("KENIA", "África"), ("GHANA", "África"),
    ("ARGELIA", "África"), ("ANGOLA", "África"), ("TUNEZ", "África"),
    ("COLOMBIA", "América Latina"), ("PERÚ", "América Latina"), ("PERU", "América Latina"),
    ("CHILE", "América Latina"), ("ARGENTINA", "América Latina"),
    ("BRASIL", "América Latina"), ("VENEZUELA", "América Latina"),
    ("PANAMÁ", "América Latina"), ("PANAMA", "América Latina"),
    ("GUATEMALA", "América Latina"), ("COSTA RICA", "América Latina"),
    ("HONDURAS", "América Latina"), ("EL SALVADOR", "América Latina"),
    ("NICARAGUA", "América Latina"), ("BOLIVIA", "América Latina"),
    ("PARAGUAY", "América Latina"), ("URUGUAY", "América Latina"),
    ("DOMINICANA", "América Latina"), ("CUBA", "América Latina"),
    ("ECUADOR", "América Latina"),
    ("ZONA FRANCA", "Otros"), ("AGUAS INTERNACIONALES", "Otros"),
]

def _asignar_region(pais):
    pais_upper = str(pais).upper()
    for patron, region in _REGION_PATTERNS:
        if patron in pais_upper:
            return region
    return "Otros"

# Paleta de respaldo
_FALLBACK_COLORS = [
    "#2563eb", "#f59e0b", "#10b981", "#8b5cf6", "#f43f5e",
    "#06b6d4", "#84cc16", "#a855f7", "#14b8a6", "#fb923c",
    "#6366f1", "#22c55e", "#e879f9", "#38bdf8", "#facc15",
]

def get_grupo_color(grupo, index=0):
    return GRUPO_COLORS.get(grupo, _FALLBACK_COLORS[index % len(_FALLBACK_COLORS)])


@st.cache_data
def load_data():
    """Carga el parquet completo (con Subpartida). Solo para drilldown."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "importaciones_ecuador.parquet")
    df = pd.read_parquet(path)

    # Convertir categoricals a string eficientemente
    for col in ["Pais_Origen", "Cod_Grupo", "Cod_Subgrupo", "Cod_Subpartida",
                "Grupo", "Subgrupo", "Subpartida"]:
        if hasattr(df[col], "cat"):
            df[col] = df[col].cat.rename_categories(
                lambda x: x.strip() if isinstance(x, str) else x
            )
        else:
            df[col] = df[col].astype(str).str.strip()

    # Normalizar nombres de grupos usando los mapas (sobreescribe el valor del CSV)
    df["Grupo"]    = df["Cod_Grupo"].astype(str).map(GRUPO_MAP).fillna("Otro")
    df["Subgrupo"] = df["Cod_Subgrupo"].astype(str).map(SUBGRUPO_MAP).fillna("Otro")

    # Región de origen
    df["Region"] = df["Pais_Origen"].apply(_asignar_region)

    # CIF ya está en miles USD → convertir a millones
    df["CIF"] = df["CIF"] / 1000
    df["FOB"] = df["FOB"] / 1000

    return df


@st.cache_data
def load_data_aggregated():
    """Datos agregados a nivel Grupo-Subgrupo-País-Mes (sin Subpartida).
    Mucho más liviano para la mayoría de visualizaciones."""
    df = load_data()
    agg = df.groupby(
        ["Fecha", "Anio", "Mes", "Cod_Grupo", "Grupo",
         "Cod_Subgrupo", "Subgrupo", "Pais_Origen", "Region"],
        observed=True
    ).agg(
        CIF=("CIF", "sum"),
        FOB=("FOB", "sum"),
        TM=("TM",  "sum"),
    ).reset_index()
    return agg


def filtros_sidebar(df, key_prefix=""):
    """Filtros en cascada: Año → Grupo → Subgrupo → Región → País."""
    st.sidebar.title("Filtros")

    # 1. Rango de años
    anio_min, anio_max = int(df["Anio"].min()), int(df["Anio"].max())
    rango = st.sidebar.slider("Rango de años", anio_min, anio_max,
                              (anio_min, anio_max), key=f"{key_prefix}_anio")
    df_disp = df[(df["Anio"] >= rango[0]) & (df["Anio"] <= rango[1])]

    # 2. Grupo CUODE
    grupo_opts = df_disp[["Cod_Grupo", "Grupo"]].drop_duplicates()
    grupo_opts["Label"] = grupo_opts["Cod_Grupo"] + " – " + grupo_opts["Grupo"]
    grupo_opts["_sort"] = grupo_opts["Cod_Grupo"].apply(
        lambda x: "ZZZ" if not x.isdigit() else x.zfill(3)
    )
    grupo_opts = grupo_opts.sort_values("_sort")
    grupo_labels = st.sidebar.multiselect(
        "Grupo CUODE (vacío = todos)",
        grupo_opts["Label"].tolist(),
        key=f"{key_prefix}_grupo"
    )
    if grupo_labels:
        grupos_sel = [l.split(" – ", 1)[1] for l in grupo_labels]
        df_disp = df_disp[df_disp["Grupo"].isin(grupos_sel)]
    else:
        grupos_sel = []

    # 3. Subgrupo
    subgrupo_opts = df_disp[["Cod_Subgrupo", "Subgrupo"]].drop_duplicates()
    subgrupo_opts["Label"] = subgrupo_opts["Cod_Subgrupo"] + " – " + subgrupo_opts["Subgrupo"]
    subgrupo_opts["_sort"] = subgrupo_opts["Cod_Subgrupo"].apply(
        lambda x: "ZZZ" if not x.isdigit() else x.zfill(4)
    )
    subgrupo_opts = subgrupo_opts.sort_values("_sort")
    subgrupo_labels = st.sidebar.multiselect(
        "Subgrupo (vacío = todos)",
        subgrupo_opts["Label"].tolist(),
        key=f"{key_prefix}_subgrupo"
    )
    if subgrupo_labels:
        subgrupos_sel = [l.split(" – ", 1)[1] for l in subgrupo_labels]
        df_disp = df_disp[df_disp["Subgrupo"].isin(subgrupos_sel)]
    else:
        subgrupos_sel = []

    # 4. Región de origen
    regiones = st.sidebar.multiselect(
        "Región de origen (vacío = todas)",
        sorted(df_disp["Region"].unique()),
        key=f"{key_prefix}_region"
    )
    if regiones:
        df_disp = df_disp[df_disp["Region"].isin(regiones)]

    # 5. País de origen
    paises = st.sidebar.multiselect(
        "País de origen (vacío = todos)",
        sorted(df_disp["Pais_Origen"].unique()),
        key=f"{key_prefix}_pais"
    )
    if paises:
        df_disp = df_disp[df_disp["Pais_Origen"].isin(paises)]

    return df_disp, rango, grupos_sel, paises
