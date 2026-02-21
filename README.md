# Dashboard de Importaciones del Ecuador

Dashboard interactivo para explorar y analizar las importaciones del Ecuador durante el periodo **2000–2025**, desarrollado con **Streamlit** y **Plotly**.

Los datos provienen del **Banco Central del Ecuador (BCE)** y abarcan mas de **6.7 millones de registros** con detalle mensual de valores CIF, volumenes en toneladas metricas y clasificacion arancelaria a nivel de subpartida, bajo la nomenclatura **CUODE** (Clasificacion por Uso o Destino Economico).

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red)
![Plotly](https://img.shields.io/badge/Plotly-5.0+-purple)

---

## Estructura del proyecto

```
importaciones/
├── app.py                           # Pagina principal (Inicio)
├── data_loader.py                   # Modulo central: carga de datos, filtros, colores
├── etl_excel_to_parquet.py          # ETL: convierte Excel del BCE a Parquet
├── importaciones_ecuador.parquet    # Datos procesados (~6.7M filas)
├── requirements.txt                 # Dependencias del proyecto
├── README.md
└── pages/
    ├── 1_Suma_Movil_12M.py          # Modulo 1: Suma movil 12 meses
    ├── 2_Treemap_CUODE.py           # Modulo 2: Treemap jerarquico CUODE
    ├── 3_Precio_Implicito.py        # Modulo 3: Precio implicito
    └── 4_Drilldown_Subpartida.py    # Modulo 4: Drilldown por subpartida
```

## Modulos

### Inicio (`app.py`)
Pagina principal con resumen ejecutivo del comercio exterior ecuatoriano:
- KPIs principales (CIF total, volumen, variacion interanual, subgrupos, origenes)
- Serie anual de importaciones CIF con tasa de crecimiento
- Top 10 subgrupos y paises de origen
- Distribucion por region geografica (pie chart + area apilada)
- Diversificacion temporal (N° de subgrupos y origenes activos)
- Participacion por grupo CUODE (stacked area al 100%)

### 1. Suma Movil 12M
Analiza la tendencia de largo plazo eliminando estacionalidad:
- Suma movil 12M total (CIF + Volumen en doble eje)
- Suma movil por subgrupo CUODE (Top N seleccionable, colores fijos)
- Suma movil por pais de origen (Top N seleccionable, colores fijos)

### 2. Treemap Jerarquico CUODE
Visualiza la estructura de importaciones por clasificacion CUODE:
- Treemap completo: Grupo → Subgrupo (coloreado por grupo o valor absoluto)
- Evolucion de la composicion por grupo (% del total, stacked area)
- Treemap por pais de origen (Top 15)

### 3. Precio Implicito
Calcula el precio promedio de importacion (CIF/TM) con suavizado 12M:
- Selector en cascada: Grupo CUODE → Subgrupo
- Selector de rango de anos en sidebar
- Serie temporal con banda de confianza (±2 sigma) y deteccion de outliers
- KPIs: precio actual, variacion 12M, maximo y minimo historico

### 4. Drilldown Subpartida
Explora el detalle granular a nivel de subpartida arancelaria:
- Selector en cascada: Grupo CUODE → Subgrupo
- El subgrupo equivale al "producto" (no existe nivel intermedio en CUODE)
- Composicion por subpartida (Top N por CIF, slider 3-15, barras horizontales con codigo)
- Evolucion temporal de las principales subpartidas (lineas por ano)
- Detalle de una subpartida especifica: KPIs, evolucion anual y top 10 paises de origen

## Datos

| Campo | Detalle |
|-------|---------|
| **Fuente** | Banco Central del Ecuador (BCE) |
| **Periodo** | Enero 2000 – Diciembre 2025 |
| **Granularidad** | Mensual, por Subgrupo CUODE × Pais Origen × Subpartida |
| **Registros** | ~6,700,000 filas |
| **Variables** | CIF (millones USD), Volumen (TM), Codigo arancelario |

### Jerarquia CUODE
La clasificacion CUODE organiza las importaciones por uso economico:
- **Grupo** (2 digitos): 10 grupos (Consumo No Duradero, Consumo Duradero, Combustibles, Mat. Primas, Capital, etc.)
- **Subgrupo** (3 digitos): 35 subgrupos (ej: Productos Alimenticios, Vehiculos, Maquinaria Industrial, etc.)
- **Subpartida** (10 digitos): ~5,400 subpartidas arancelarias

### Pipeline de datos
```
Excel BCE (multiples sheets)
    ↓  etl_excel_to_parquet.py
Parquet (~6.7M filas)
    ↓  data_loader.py
    ├── load_data()            → 6.7M filas (con subpartida, para Drilldown)
    └── load_data_aggregated() → 390K filas (sin subpartida, para resto de modulos)
```

## Instalacion

### Requisitos
- Python 3.10 o superior

### Pasos

1. Clonar el repositorio:
```bash
git clone https://github.com/jp1309/importaciones.git
cd importaciones
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Ejecutar el dashboard:
```bash
streamlit run app.py
```

El dashboard se abrira en `http://localhost:8502`.

### Regenerar datos (opcional)
Si se cuenta con el archivo Excel original del BCE:
```bash
python etl_excel_to_parquet.py
```

## Configuracion de colores

El dashboard usa paletas de colores fijas para mantener consistencia visual:

- **35 subgrupos CUODE**: colores semanticos por categoria (verde = consumo no duradero, negro = combustibles, azul = capital industrial, rojo = equipo de transporte, etc.)
- **11 grupos CUODE**: colores de maximo contraste entre categorias
- **15 paises de origen**: colores fijos alineados con el dashboard de exportaciones donde coinciden (EE.UU. = azul marino, China = amarillo dorado, Panama = rojo, etc.)

Los colores se definen en `data_loader.py` en los diccionarios `SUBGRUPO_COLORS`, `GRUPO_COLORS` y `COUNTRY_COLORS`.

## Filtros

### Filtros globales (sidebar)
Disponibles en Inicio, Suma Movil, Treemap y Drilldown:
- Rango de anos
- Grupo CUODE (multiselect)
- Subgrupo CUODE (multiselect)
- Region de origen
- Pais de origen

### Selectores internos
En Precio Implicito y Drilldown, selectores en cascada Grupo → Subgrupo dentro de la pagina.

## Tecnologias

- **[Streamlit](https://streamlit.io/)** — Framework para dashboards interactivos
- **[Plotly](https://plotly.com/python/)** — Graficos interactivos (go.Scatter, go.Bar, px.treemap, px.line)
- **[Pandas](https://pandas.pydata.org/)** — Manipulacion y analisis de datos
- **[PyArrow](https://arrow.apache.org/docs/python/)** — Lectura de archivos Parquet

---

Desarrollado por **Juan Pablo Erraez** | 2025
