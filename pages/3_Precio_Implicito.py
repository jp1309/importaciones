"""
Módulo 3: Precio Implícito CIF/TM de importaciones
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from data_loader import load_data_aggregated, filtros_sidebar, GRUPO_MAP, SUBGRUPO_MAP

st.set_page_config(page_title="Precio Implícito – Importaciones", page_icon="💲", layout="wide")
st.title("Precio Implícito de Importaciones")
st.caption(
    "Precio implícito = CIF acumulado 12 meses / Toneladas métricas acumuladas 12 meses | "
    "Resultado en USD/TM | Promedio móvil para suavizar estacionalidad"
)
st.info(
    "**Interpretación:** El precio implícito refleja el costo unitario promedio por tonelada "
    "métrica importada en los últimos 12 meses. Permite identificar tendencias de precios, "
    "comparar subgrupos y detectar cambios estructurales."
)

PLOT_BG    = "white"
GRID_COLOR = "#f0f0f0"

df = load_data_aggregated()


@st.cache_data
def calcular_precio_implicito(data):
    agg = data.groupby(["Fecha", "Grupo", "Subgrupo"])[["CIF","TM"]].sum().reset_index()
    agg = agg.sort_values("Fecha")
    result = []
    for (grp, sub), g in agg.groupby(["Grupo","Subgrupo"]):
        g = g.copy()
        g["CIF_12M"] = g["CIF"].rolling(12).sum()
        g["TM_12M"]  = g["TM"].rolling(12).sum()
        g["Precio"]  = g["CIF_12M"] / g["TM_12M"] * 1_000_000
        result.append(g)
    return pd.concat(result, ignore_index=True)


precios = calcular_precio_implicito(df)

# ── Selector cascada: Grupo → Subgrupo ───────────────────────────────
col_g, col_s = st.columns(2)

grupos_disp = df["Grupo"].unique()
grupos_opts = []
for k, v in sorted(GRUPO_MAP.items(), key=lambda x: x[0]):
    if v in grupos_disp:
        grupos_opts.append(f"{k} – {v}")
# Agregar grupos sin código al final
codificados = {v for k, v in GRUPO_MAP.items()}
for g in grupos_disp:
    if g not in codificados:
        grupos_opts.append(g)

with col_g:
    grp_label = st.selectbox("Grupo CUODE", ["(selecciona un grupo)"] + grupos_opts,
                              key="pi_grupo")

if grp_label == "(selecciona un grupo)":
    st.info("Selecciona un Grupo CUODE para explorar el precio implícito.")
    st.stop()

grp_sel = grp_label.split(" – ", 1)[1] if " – " in grp_label else grp_label

subs_disp = df[df["Grupo"] == grp_sel]["Subgrupo"].unique()
subs_opts = []
for k, v in sorted(SUBGRUPO_MAP.items(), key=lambda x: x[0]):
    if v in subs_disp:
        subs_opts.append(f"{k} – {v}")
# Agregar subgrupos sin código al final
codificados_s = {v for k, v in SUBGRUPO_MAP.items()}
for s in subs_disp:
    if s not in codificados_s:
        subs_opts.append(s)

with col_s:
    sub_label = st.selectbox("Subgrupo", ["(selecciona un subgrupo)"] + subs_opts,
                              key="pi_subgrupo")

if sub_label == "(selecciona un subgrupo)":
    st.info("Selecciona un Subgrupo para ver el precio implícito.")
    st.stop()

sub_sel = sub_label.split(" – ", 1)[1] if " – " in sub_label else sub_label

serie = precios[(precios["Grupo"] == grp_sel) & (precios["Subgrupo"] == sub_sel)].dropna(subset=["Precio"])

if serie.empty:
    st.warning("No hay datos suficientes para calcular el precio implícito de este subgrupo.")
    st.stop()

# ── KPIs ─────────────────────────────────────────────────────────────
ultimo_precio = serie["Precio"].iloc[-1]
precio_12 = serie["Precio"].iloc[-13] if len(serie) > 12 else None
var_12 = (ultimo_precio - precio_12) / precio_12 * 100 if precio_12 else None
precio_max = serie["Precio"].max()
precio_min = serie["Precio"][serie["Precio"] > 0].min()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Precio actual (USD/TM)", f"${ultimo_precio:,.0f}")
k2.metric("Variación 12M", f"{var_12:+.1f}%" if var_12 is not None else "N/D")
k3.metric("Máximo histórico (USD/TM)", f"${precio_max:,.0f}")
k4.metric("Mínimo histórico (USD/TM)", f"${precio_min:,.0f}")

st.divider()

# ── Gráfico 1: Precio implícito con banda ±2σ ─────────────────────────
st.subheader(f"Precio Implícito CIF/TM — {sub_sel}")

serie_p = serie.copy()
serie_p["MA24"]  = serie_p["Precio"].rolling(24).mean()
serie_p["Std24"] = serie_p["Precio"].rolling(24).std()
serie_p["Upper"] = serie_p["MA24"] + 2 * serie_p["Std24"]
serie_p["Lower"] = (serie_p["MA24"] - 2 * serie_p["Std24"]).clip(lower=0)

outliers = serie_p[
    (serie_p["Precio"] > serie_p["Upper"]) | (serie_p["Precio"] < serie_p["Lower"])
].dropna(subset=["Upper"])

fig1 = go.Figure()
fig1.add_trace(go.Scatter(
    x=pd.concat([serie_p["Fecha"], serie_p["Fecha"].iloc[::-1]]),
    y=pd.concat([serie_p["Upper"], serie_p["Lower"].iloc[::-1]]),
    fill="toself", fillcolor="rgba(37,99,235,0.08)",
    line=dict(color="rgba(0,0,0,0)"),
    name="Banda ±2σ", hoverinfo="skip",
))
fig1.add_trace(go.Scatter(
    x=serie_p["Fecha"], y=serie_p["Precio"],
    name="Precio CIF/TM", mode="lines",
    line=dict(color="#2563eb", width=2),
    hovertemplate="%{x|%b %Y}: $%{y:,.0f} USD/TM<extra></extra>",
))
fig1.add_trace(go.Scatter(
    x=serie_p["Fecha"], y=serie_p["MA24"],
    name="Media móvil 24M", mode="lines",
    line=dict(color="#f59e0b", width=1.5, dash="dot"),
    hovertemplate="%{x|%b %Y}: $%{y:,.0f} USD/TM<extra></extra>",
))
if not outliers.empty:
    fig1.add_trace(go.Scatter(
        x=outliers["Fecha"], y=outliers["Precio"],
        name="Outlier", mode="markers",
        marker=dict(color="#dc2626", size=8, symbol="diamond"),
        hovertemplate="%{x|%b %Y}: $%{y:,.0f} USD/TM<extra></extra>",
    ))
fig1.update_layout(
    height=420, hovermode="x unified", margin=dict(t=20, b=30),
    legend=dict(orientation="h", y=1.08),
    yaxis_title="Precio Implícito (USD/TM)",
    plot_bgcolor=PLOT_BG,
)
fig1.update_xaxes(gridcolor=GRID_COLOR)
fig1.update_yaxes(gridcolor=GRID_COLOR, tickformat=",.0f")
st.plotly_chart(fig1, use_container_width=True)

st.divider()

# ── Gráfico 2: Precio implícito por país de origen ────────────────────
st.subheader(f"Precio Implícito CIF/TM por país de origen — {sub_sel}")
raw_sub = df[(df["Grupo"] == grp_sel) & (df["Subgrupo"] == sub_sel)]
pais_precio = (raw_sub.groupby("Pais_Origen").agg(CIF=("CIF","sum"), TM=("TM","sum"))
               .reset_index())
pais_precio = pais_precio[pais_precio["TM"] > 0].copy()
pais_precio["Precio"] = pais_precio["CIF"] / pais_precio["TM"] * 1_000_000
pais_precio = pais_precio.sort_values("Precio", ascending=True).tail(10)

fig2 = go.Figure(go.Bar(
    x=pais_precio["Precio"], y=pais_precio["Pais_Origen"],
    orientation="h",
    marker_color="#8b5cf6",
    hovertemplate="<b>%{y}</b><br>$%{x:,.0f} USD/TM<extra></extra>",
))
fig2.update_layout(
    height=400, margin=dict(l=200, t=10, b=30, r=20),
    xaxis=dict(title=f"Precio Implícito de {sub_sel} (USD/TM)",
               tickformat=",.0f", gridcolor=GRID_COLOR),
    plot_bgcolor=PLOT_BG,
)
fig2.update_xaxes(gridcolor=GRID_COLOR)
fig2.update_yaxes(gridcolor=GRID_COLOR)
st.plotly_chart(fig2, use_container_width=True)
