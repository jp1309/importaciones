"""
Módulo compartido: carga de datos y preprocesamiento de importaciones.
Fuente: BCE - Importaciones por Grupo, Subgrupo CUODE, Subpartida y País Origen
"""
import os
import unicodedata
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

# Colores fijos por subgrupo CUODE — lógica semántica por categoría
SUBGRUPO_COLORS = {
    # Consumo No Duradero — verdes
    "Productos Alimenticios":              "#16a34a",  # Verde
    "Bebidas":                             "#4ade80",  # Verde claro
    "Tabaco":                              "#854d0e",  # Marrón oscuro
    "Productos Farmacéuticos y de Tocador":"#34d399",  # Esmeralda
    "Vestuario y Confecciones":            "#6ee7b7",  # Verde menta
    "Otros Bienes de Consumo No Duradero": "#bbf7d0",  # Verde muy claro
    # Consumo Duradero — rosas/rojos
    "Utensilios Domésticos":               "#f43f5e",  # Rosa fuerte
    "Objetos de Adorno y Uso Personal":    "#fb7185",  # Rosa
    "Muebles y Equipo para el Hogar":      "#fda4af",  # Rosa claro
    "Máquinas y Aparatos de Uso Doméstico":"#e11d48",  # Rojo rosa
    "Vehículos de Transporte Particular":  "#9f1239",  # Rojo oscuro
    "Armas y Equipo Militar":              "#4c0519",  # Granate
    # Combustibles — negros/grises oscuros
    "Combustibles":                        "#000000",  # Negro
    "Lubricantes":                         "#374151",  # Gris muy oscuro
    "Electricidad":                        "#facc15",  # Amarillo (energía)
    # Materias Primas Agropecuarias — dorados
    "Alimentos para Animales":             "#ca8a04",  # Dorado
    "Otras Materias Primas Agrícolas":     "#fbbf24",  # Ámbar
    # Materias Primas Industriales — cyan/azul
    "Productos Alimenticios para la Industria": "#0891b2",  # Cyan
    "Prod. Agropecuarios no Alimenticios": "#06b6d4",  # Cyan claro
    "Productos Mineros para la Industria": "#164e63",  # Azul oscuro
    "Productos Químicos y Farmacéuticos":  "#0e7490",  # Teal oscuro
    # Construcción — marrones
    "Materiales de Construcción":          "#92400e",  # Marrón
    # Capital Agrícola — limas
    "Máquinas y Herramientas Agrícolas":   "#65a30d",  # Lima
    "Otro Equipo Agrícola":                "#84cc16",  # Lima claro
    "Material de Transporte Agrícola":     "#a3e635",  # Lima muy claro
    # Capital Industrial — azules
    "Máquinas de Oficina y Científicas":   "#1d4ed8",  # Azul oscuro
    "Herramientas Industriales":           "#2563eb",  # Azul
    "Partes y Accesorios de Maquinaria":   "#3b82f6",  # Azul medio
    "Maquinaria Industrial":               "#60a5fa",  # Azul claro
    "Otro Equipo Fijo Industrial":         "#93c5fd",  # Azul muy claro
    # Equipo de Transporte — rojos
    "Partes y Accesorios de Transporte":   "#dc2626",  # Rojo
    "Equipo Rodante de Transporte":        "#f87171",  # Rojo claro
    "Equipo Fijo de Transporte":           "#fca5a5",  # Rojo muy claro
    # Otros
    "Diversos":                            "#9ca3af",  # Gris
    "Tráfico Postal":                      "#d1d5db",  # Gris claro
}

# Colores por grupo CUODE — máximo contraste entre grupos
GRUPO_COLORS = {
    "Bienes de Consumo No Duradero": "#16a34a",   # Verde
    "Bienes de Consumo Duradero":    "#e11d48",   # Rosa fuerte (diferenciado de verde)
    "Combustibles y Lubricantes":    "#000000",   # Negro
    "Mat. Primas Agropecuarias":     "#ca8a04",   # Dorado
    "Mat. Primas Industriales":      "#0891b2",   # Cyan (diferenciado de azul oscuro)
    "Materiales de Construcción":    "#92400e",   # Marrón
    "Bienes de Capital Agrícola":    "#65a30d",   # Lima (diferenciado de verde oscuro)
    "Bienes de Capital Industrial":  "#1d4ed8",   # Azul oscuro
    "Equipo de Transporte":          "#dc2626",   # Rojo
    "Diversos":                      "#9ca3af",   # Gris
    "Tráfico Postal":                "#d1d5db",   # Gris claro
}

# Colores fijos por país origen (Top 15 por CIF) — mismos que COUNTRY_COLORS de exportaciones donde coinciden
COUNTRY_COLORS = {
    "ESTADOS UNIDOS":                        "#1e3a8a",  # Azul marino      (igual exportaciones)
    "CHINA":                                 "#facc15",  # Amarillo dorado  (igual exportaciones)
    "COLOMBIA":                              "#eab308",  # Amarillo         (igual exportaciones)
    "BRASIL":                                "#15803d",  # Verde oscuro
    "PER\u00da":                             "#059669",  # Verde esmeralda  (igual exportaciones)
    "COREA (SUR), REP\u00daBLICA DE":        "#7c3aed",  # Púrpura
    "M\u00c9XICO":                           "#ea580c",  # Naranja
    "PANAM\u00c1":                           "#dc2626",  # Rojo             (igual exportaciones)
    "JAP\u00d3N":                            "#0891b2",  # Cyan
    "CHILE":                                 "#2563eb",  # Azul             (igual exportaciones)
    "ALEMANIA":                              "#64748b",  # Gris azulado
    "ARGENTINA":                             "#f43f5e",  # Rosa fuerte
    "ESPA\u00d1A":                           "#f59e0b",  # Naranja          (igual exportaciones)
    "VENEZUELA, REP\u00daBLICA BOLIVARIANA": "#6d28d9",  # Violeta
    "ITALIA":                                "#16a34a",  # Verde            (igual exportaciones)
}

# Colores fijos por región geográfica (consistentes con exportaciones)
REGION_COLORS = {
    "América del Norte": "#66c2a5",  # Verde agua   (Set2[0])
    "América Latina":    "#fc8d62",  # Naranja       (Set2[1])
    "Europa":            "#8da0cb",  # Azul lavanda  (Set2[2])
    "Asia":              "#e78ac3",  # Rosa          (Set2[3])
    "Medio Oriente":     "#a6d854",  # Verde lima    (Set2[4])
    "África":            "#ffd92f",  # Amarillo      (Set2[5])
    "Oceanía":           "#e5c494",  # Beige         (Set2[6])
    "Otros":             "#b3b3b3",  # Gris          (Set2[7])
}

# Paleta de respaldo
_FALLBACK_COLORS = [
    "#2563eb", "#f59e0b", "#10b981", "#8b5cf6", "#f43f5e",
    "#06b6d4", "#84cc16", "#a855f7", "#14b8a6", "#fb923c",
    "#6366f1", "#22c55e", "#e879f9", "#38bdf8", "#facc15",
]


def get_grupo_color(grupo, index=0):
    return GRUPO_COLORS.get(grupo, _FALLBACK_COLORS[index % len(_FALLBACK_COLORS)])


def get_country_color(country_name, index=0):
    return COUNTRY_COLORS.get(country_name, _FALLBACK_COLORS[index % len(_FALLBACK_COLORS)])

def _normalizar(s):
    """Quita tildes y pasa a mayúsculas para comparación robusta."""
    return "".join(
        c for c in unicodedata.normalize("NFD", str(s).upper())
        if unicodedata.category(c) != "Mn"
    )

# Regiones geográficas — mismos patrones que exportaciones, con _normalizar() para robustez
_REGION_PATTERNS = [
    # América del Norte
    ("ESTADOS UNIDOS", "América del Norte"),
    ("CANAD", "América del Norte"),
    ("MEXIC", "América del Norte"), ("MÉXIC", "América del Norte"),
    # Europa
    ("ALEMANI", "Europa"), ("ESPAÑ", "Europa"), ("FRANCI", "Europa"),
    ("ITALI", "Europa"), ("HOLANDA", "Europa"), ("PAÍSES BAJOS", "Europa"),
    ("REINO UNIDO", "Europa"), ("BÉLGI", "Europa"), ("BELGI", "Europa"), ("BELG", "Europa"),
    ("RUSI", "Europa"), ("SUIZ", "Europa"), ("PORTUG", "Europa"),
    ("SUECI", "Europa"), ("POLONI", "Europa"), ("GRECI", "Europa"),
    ("TURQU", "Europa"), ("UCRANI", "Europa"), ("NORUEG", "Europa"),
    ("DINAMARC", "Europa"), ("FINLANDI", "Europa"), ("IRLAND", "Europa"),
    ("RUMANI", "Europa"), ("AUSTRI", "Europa"), ("CHECA", "Europa"),
    ("BULGARI", "Europa"), ("ESLOVENI", "Europa"), ("LITUANI", "Europa"),
    ("CROACI", "Europa"), ("MONTENEGR", "Europa"), ("ESTONI", "Europa"),
    ("ALBANI", "Europa"), ("SERBI", "Europa"), ("MALT", "Europa"),
    ("LETONI", "Europa"), ("ESLOVAQU", "Europa"), ("HUNGR", "Europa"),
    ("MACEDONI", "Europa"), ("BOSNIA", "Europa"), ("LUXEMBURG", "Europa"),
    ("ISLANDI", "Europa"), ("LIECHTENSTEIN", "Europa"), ("ANDORR", "Europa"),
    ("SAN MARINO", "Europa"), ("MÓNACO", "Europa"), ("MONACO", "Europa"),
    ("GIBRALTAR", "Europa"), ("SANTA SEDE", "Europa"), ("VATICANO", "Europa"),
    ("FERO", "Europa"), ("YUGOESLAVI", "Europa"), ("BELAR", "Europa"),
    ("MOLDOV", "Europa"), ("GEORGI", "Europa"), ("CHIPRE", "Europa"),
    ("GUERNSEY", "Europa"), ("JERSEY", "Europa"), ("SVALBARD", "Europa"),
    ("ALAND", "Europa"),
    # Asia
    ("CHINA", "Asia"), ("JAPÓN", "Asia"), ("JAPON", "Asia"),
    ("COREA (SUR", "Asia"), ("COREA DEL SUR", "Asia"),
    ("COREA (NORTE", "Asia"),
    ("INDIA", "Asia"), ("INDONESI", "Asia"),
    ("TAILANDI", "Asia"), ("VIETNAM", "Asia"), ("MALASI", "Asia"),
    ("FILIPIN", "Asia"), ("TAIW", "Asia"), ("SINGAPUR", "Asia"),
    ("HONG KONG", "Asia"), ("MACAO", "Asia"),
    ("PAKIST", "Asia"), ("BANGLADESH", "Asia"), ("SRI LANKA", "Asia"),
    ("CAMBOYA", "Asia"), ("MYANMAR", "Asia"), ("BIRMANIA", "Asia"),
    ("BRUNÉI", "Asia"), ("BRUNEI", "Asia"), ("LAOS", "Asia"),
    ("MONGOLI", "Asia"), ("NEPAL", "Asia"), ("BHUT", "Asia"), ("MALDIV", "Asia"),
    ("KAZAJIST", "Asia"), ("KIRGUIST", "Asia"), ("UZBEKIST", "Asia"),
    ("TAYIKIST", "Asia"), ("TURKMENIST", "Asia"), ("AZERBAIY", "Asia"),
    ("ARMENI", "Asia"), ("AFGANIST", "Asia"), ("TIMOR", "Asia"),
    # Medio Oriente
    ("ARABIA SAUDITA", "Medio Oriente"), ("EMIRATOS", "Medio Oriente"),
    ("ISRAEL", "Medio Oriente"), ("IRÁN", "Medio Oriente"), ("IRAN", "Medio Oriente"),
    ("IRAK", "Medio Oriente"), ("KUWAIT", "Medio Oriente"),
    ("QATAR", "Medio Oriente"), ("OMÁN", "Medio Oriente"), ("OMAN", "Medio Oriente"),
    ("BAHREIN", "Medio Oriente"), ("BAHRÉIN", "Medio Oriente"),
    ("JORDANI", "Medio Oriente"), ("LÍBANO", "Medio Oriente"), ("LIBANO", "Medio Oriente"),
    ("SIRIA", "Medio Oriente"), ("YEMEN", "Medio Oriente"),
    ("PALESTIN", "Medio Oriente"),
    # Oceanía
    ("AUSTRALIA", "Oceanía"), ("NUEVA ZELAND", "Oceanía"),
    ("PAPÚA", "Oceanía"), ("PAPUA", "Oceanía"),
    ("FIJI", "Oceanía"), ("SAMOA", "Oceanía"),
    ("KIRIBATI", "Oceanía"), ("VANUATU", "Oceanía"),
    ("MARSHALL", "Oceanía"), ("SALOMÓN", "Oceanía"), ("SALOM", "Oceanía"),
    ("MICRONESIA", "Oceanía"), ("PALAU", "Oceanía"), ("NAURU", "Oceanía"),
    ("NIUE", "Oceanía"), ("COOK", "Oceanía"), ("TOKELAU", "Oceanía"),
    ("PITCAIRN", "Oceanía"), ("NORFOLK", "Oceanía"),
    ("POLINESIA", "Oceanía"), ("NUEVA CALEDONI", "Oceanía"),
    ("GUAM", "Oceanía"), ("MARIANAS", "Oceanía"),
    ("PACÍFICO", "Oceanía"), ("COCOS", "Oceanía"),
    ("TONGA", "Oceanía"), ("TUVALU", "Oceanía"),
    ("WALLIS", "Oceanía"), ("HEARD", "Oceanía"),
    ("TERRITORIOS AUSTRALES", "Oceanía"),
    # África
    ("SUDÁFRICA", "África"), ("SUDAFRICA", "África"),
    ("EGIPTO", "África"), ("NIGERIA", "África"), ("MARRUECOS", "África"),
    ("KENYA", "África"), ("KENIA", "África"), ("GHANA", "África"),
    ("ARGELIA", "África"), ("COSTA DE MARFIL", "África"),
    ("LIBIA", "África"), ("TÚNEZ", "África"), ("TUNEZ", "África"),
    ("SENEGAL", "África"), ("CAMERÚN", "África"), ("CAMERUN", "África"),
    ("CABO VERDE", "África"), ("SIERRA LEONA", "África"),
    ("GUINEA", "África"),
    ("MADAGASCAR", "África"), ("ETIOPÍA", "África"), ("ETIOP", "África"),
    ("MOZAMBIQUE", "África"), ("ANGOLA", "África"), ("TOGO", "África"),
    ("BENÍN", "África"), ("BENIN", "África"),
    ("CONGO", "África"), ("GABÓN", "África"), ("GABON", "África"),
    ("MAURICIO", "África"), ("MAURITANI", "África"),
    ("NAMIBIA", "África"), ("SUDÁN", "África"), ("SUDAN", "África"),
    ("LIBERIA", "África"), ("UGANDA", "África"), ("TANZANÍA", "África"),
    ("TANZAN", "África"), ("RWANDA", "África"), ("BURUNDI", "África"),
    ("BURKINA", "África"), ("MALÍ", "África"), ("MALI", "África"),
    ("NÍGER", "África"), ("NIGER", "África"),
    ("CHAD", "África"), ("GAMBIA", "África"),
    ("DJIBOUTI", "África"), ("COMORAS", "África"),
    ("SANTO TOMÉ", "África"), ("SANTO TOM", "África"),
    ("SEYCHELLES", "África"), ("SWAZILANDIA", "África"),
    ("LESOTHO", "África"), ("BOTSWANA", "África"),
    ("ZAMBIA", "África"), ("ZIMBABWE", "África"), ("MALAWI", "África"),
    ("CENTROAFRICANA", "África"), ("SAHARA", "África"),
    ("MAYOTE", "África"), ("REUNIÓN", "África"), ("REUNION", "África"),
    ("ERITREA", "África"), ("SOMALIA", "África"),
    ("SANTA ELENA", "África"),
    # América Latina y Caribe
    ("COLOMBIA", "América Latina"), ("PERÚ", "América Latina"), ("PERU", "América Latina"),
    ("CHILE", "América Latina"), ("ARGENTINA", "América Latina"),
    ("BRASIL", "América Latina"), ("VENEZUELA", "América Latina"),
    ("PANAMÁ", "América Latina"), ("PANAMA", "América Latina"),
    ("GUATEMALA", "América Latina"), ("COSTA RICA", "América Latina"),
    ("HONDURAS", "América Latina"), ("EL SALVADOR", "América Latina"),
    ("NICARAGUA", "América Latina"), ("BOLIVIA", "América Latina"),
    ("PARAGUAY", "América Latina"), ("URUGUAY", "América Latina"),
    ("DOMINICANA", "América Latina"), ("DOMINICA", "América Latina"),
    ("CUBA", "América Latina"), ("PUERTO RICO", "América Latina"),
    ("HAIT", "América Latina"), ("JAMAICA", "América Latina"),
    ("TRINIDAD", "América Latina"), ("BAHAMAS", "América Latina"),
    ("BARBADOS", "América Latina"), ("BÁRB", "América Latina"),
    ("SANTA LUCÍA", "América Latina"), ("SANTA LUC", "América Latina"),
    ("SAN VICENTE", "América Latina"), ("GRANADA", "América Latina"),
    ("ANTIGUA Y BARBUDA", "América Latina"), ("SAINT KITTS", "América Latina"),
    ("BELICE", "América Latina"), ("SURINAM", "América Latina"),
    ("GUYANA", "América Latina"), ("GUAYANA", "América Latina"),
    ("GUADALUPE", "América Latina"), ("MARTINICA", "América Latina"),
    ("ARUBA", "América Latina"), ("CURAZAO", "América Latina"), ("CURACAO", "América Latina"),
    ("ANTILLAS", "América Latina"), ("BONAIRE", "América Latina"),
    ("CAIMÁN", "América Latina"), ("CAIMAN", "América Latina"),
    ("BERMUDA", "América Latina"), ("MONTSERRAT", "América Latina"),
    ("ANGUILA", "América Latina"), ("TURCAS Y CAICOS", "América Latina"),
    ("VÍRGENES", "América Latina"), ("VIRGENES", "América Latina"),
    ("SAN MARTÍN", "América Latina"), ("SAN MART", "América Latina"),
    ("SAINT PIERRE", "América Latina"), ("SAN PEDRO", "América Latina"),
    ("ECUADOR", "América Latina"),
    # Zonas especiales / no determinados
    ("ZONA FRANCA", "Otros"),
    ("AGUAS INTERNACIONALES", "Otros"),
    ("TERRITORIO BRIT", "Otros"),
    ("GEORGIAS DEL SUR", "Otros"),
    ("NO DEFINIDO", "Otros"),
    ("NO DETERMINADO", "Otros"),
    ("OTROS PA", "Otros"),
    ("ANTÁRTI", "Otros"), ("ANTARTI", "Otros"),
    ("BOUVET", "Otros"),
    # Casos especiales importaciones
    ("GROENLANDIA", "América del Norte"),
    ("MAN, ISLA", "Europa"),
    ("NAVIDAD (CHRISTMAS)", "Oceanía"), ("CHRISTMAS", "Oceanía"),
    ("SAN BARTOLOM", "América Latina"),
]

def _asignar_region(pais):
    pais_norm = _normalizar(pais)
    for patron, region in _REGION_PATTERNS:
        if _normalizar(patron) in pais_norm:
            return region
    return "Otros"


def _asignar_regiones_vectorizado(serie_paises):
    """Versión vectorizada: calcula región solo para países únicos y hace merge."""
    paises_unicos = serie_paises.unique()
    mapa = {p: _asignar_region(p) for p in paises_unicos}
    return serie_paises.map(mapa)



@st.cache_data(ttl=3600)
def load_data_aggregated():
    """Datos agregados a nivel Grupo-Subgrupo-País-Mes (sin Subpartida).
    Agrega las 6.7M filas del parquet a ~390K ANTES de convertir a string,
    evitando asignaciones de memoria gigantes. Mucho más rápido."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "importaciones_ecuador.parquet")
    cols = ["Fecha", "Anio", "Mes", "Cod_Grupo", "Cod_Subgrupo",
            "Pais_Origen", "CIF", "FOB", "TM"]
    df = pd.read_parquet(path, columns=cols)

    # Groupby con columnas Categorical directamente (rápido, sin conversión a str)
    agg = (df.groupby(
               ["Fecha", "Anio", "Mes", "Cod_Grupo", "Cod_Subgrupo", "Pais_Origen"],
               observed=True)
             .agg(CIF=("CIF","sum"), FOB=("FOB","sum"), TM=("TM","sum"))
             .reset_index())

    # Ahora convertir: solo 254 países/categorías (trivial vs 6.7M filas)
    agg["Pais_Origen"]  = agg["Pais_Origen"].astype(str).str.strip()
    agg["Cod_Grupo"]    = agg["Cod_Grupo"].astype(str)
    agg["Cod_Subgrupo"] = agg["Cod_Subgrupo"].astype(str)

    # Mapear nombres CUODE y regiones sobre las ~390K filas
    agg["Grupo"]    = agg["Cod_Grupo"].map(GRUPO_MAP).fillna("Otro")
    agg["Subgrupo"] = agg["Cod_Subgrupo"].map(SUBGRUPO_MAP).fillna("Otro")
    # Vectorizado: evalúa _asignar_region solo para los 254 países únicos
    agg["Region"]   = _asignar_regiones_vectorizado(agg["Pais_Origen"])

    # CIF/FOB en miles USD → millones
    agg["CIF"] = agg["CIF"] / 1000
    agg["FOB"] = agg["FOB"] / 1000

    return agg


@st.cache_data(ttl=3600)
def load_data():
    """Carga el parquet completo (con Subpartida). Solo para drilldown."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "importaciones_ecuador.parquet")
    df = pd.read_parquet(path)

    # Renombrar categorías in-place (solo ~11/35/254 valores, NO 6.7M filas)
    # Esto mantiene Categorical y evita asignar GBs de RAM.
    for col in ["Pais_Origen", "Cod_Grupo", "Cod_Subgrupo",
                "Cod_Subpartida", "Subpartida"]:
        if hasattr(df[col], "cat"):
            df[col] = df[col].cat.rename_categories(
                {c: str(c).strip() for c in df[col].cat.categories}
            )

    # Mapear nombres CUODE: construir mapa de categoría→nombre
    grupo_rename = {c: GRUPO_MAP.get(c, "Otro") for c in df["Cod_Grupo"].cat.categories}
    df["Grupo"] = df["Cod_Grupo"].cat.rename_categories(grupo_rename)

    subgrupo_rename = {c: SUBGRUPO_MAP.get(c, "Otro") for c in df["Cod_Subgrupo"].cat.categories}
    df["Subgrupo"] = df["Cod_Subgrupo"].cat.rename_categories(subgrupo_rename)

    # Región de origen (vectorizado: solo evalúa los ~254 países únicos)
    df["Region"] = _asignar_regiones_vectorizado(df["Pais_Origen"])

    # CIF en miles USD → millones
    df["CIF"] = df["CIF"] / 1000
    if "FOB" in df.columns:
        df["FOB"] = df["FOB"] / 1000

    return df


def filtros_sidebar(df, key_prefix=""):
    """Filtros en cascada: Año → Grupo → Subgrupo → Región → País."""
    st.sidebar.title("Filtros")

    # 1. Rango de años
    anio_min, anio_max = int(df["Anio"].min()), int(df["Anio"].max())
    rango = st.sidebar.slider("Rango de años", anio_min, anio_max,
                              (anio_min, anio_max), key=f"{key_prefix}_anio")
    df_disp = df[(df["Anio"] >= rango[0]) & (df["Anio"] <= rango[1])]

    # 2. Grupo CUODE
    grupo_opts = df_disp[["Cod_Grupo", "Grupo"]].drop_duplicates().copy()
    grupo_opts["Cod_Grupo"] = grupo_opts["Cod_Grupo"].astype(str)
    grupo_opts["Grupo"]     = grupo_opts["Grupo"].astype(str)
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
    subgrupo_opts = df_disp[["Cod_Subgrupo", "Subgrupo"]].drop_duplicates().copy()
    subgrupo_opts["Cod_Subgrupo"] = subgrupo_opts["Cod_Subgrupo"].astype(str)
    subgrupo_opts["Subgrupo"]     = subgrupo_opts["Subgrupo"].astype(str)
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
