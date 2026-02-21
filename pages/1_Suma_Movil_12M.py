"""
Módulo 1: Suma Móvil 12 meses de importaciones
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from plotly.subplots import make_subplots

from data_loader import (
    load_data_aggregated, filtros_sidebar,
    GRUPO_COLORS, SUBGRUPO_COLORS, _FALLBACK_COLORS, get_country_color,
)

st.set_page_config(page_title="Suma Móvil 12M – Importaciones", page_icon="📈", layout="wide")
st.title("Suma Móvil 12 Meses")
st.caption("Suma acumulada de 12 meses para suavizar estacionalidad y visualizar tendencia | Valores en millones USD (CIF)")

PLOT_BG    = "white"
GRID_COLOR = "#f0f0f0"

df = load_data_aggregated()
dff, rango, grupos_sel, paises = filtros_sidebar(df, key_prefix="sm")

# Preparar serie mensual total
serie = dff.groupby("Fecha")[["CIF", "TM"]].sum().reset_index().sort_values("Fecha")
serie["CIF_12M"] = serie["CIF"].rolling(12, min_periods=12).sum()
serie["TM_12M"]  = serie["TM"].rolling(12, min_periods=12).sum()

# ── Gráfico 1: Total CIF (dual axis con TM) ───────────────────────────
st.subheader("1. Suma móvil 12M — Total importaciones (CIF)")
fig1 = make_subplots(specs=[[{"secondary_y": True}]])
fig1.add_trace(go.Scatter(
    x=serie["Fecha"], y=serie["CIF"],
    name="Mensual CIF", mode="lines",
    line=dict(color="#93c5fd", width=0.8),
    opacity=0.4,
    hovertemplate="<b>%{x|%b %Y}</b><br>CIF: $%{y:,.1f} M<extra></extra>",
), secondary_y=False)
fig1.add_trace(go.Scatter(
    x=serie["Fecha"], y=serie["CIF_12M"],
    name="Suma 12M CIF", mode="lines",
    line=dict(color="#2563eb", width=2.5),
    fill="tozeroy", fillcolor="rgba(37,99,235,0.06)",
    hovertemplate="<b>%{x|%b %Y}</b><br>12M CIF: $%{y:,.1f} M<extra></extra>",
), secondary_y=False)
fig1.add_trace(go.Scatter(
    x=serie["Fecha"], y=serie["TM_12M"],
    name="Suma 12M TM", mode="lines",
    line=dict(color="#f59e0b", width=2, dash="dot"),
    hovertemplate="<b>%{x|%b %Y}</b><br>12M TM: %{y:,.0f}<extra></extra>",
), secondary_y=True)
fig1.update_layout(
    height=420, hovermode="x unified", margin=dict(t=20, b=30),
    legend=dict(orientation="h", y=1.1), plot_bgcolor=PLOT_BG,
)
fig1.update_yaxes(title_text="Millones USD (CIF)", secondary_y=False, gridcolor=GRID_COLOR, tickformat=",.1f")
fig1.update_yaxes(title_text="Volumen (TM)", secondary_y=True, gridcolor=GRID_COLOR, tickformat=",.0f")
fig1.update_xaxes(gridcolor=GRID_COLOR)
st.plotly_chart(fig1, use_container_width=True)

st.divider()

# ── Gráfico 2: Por grupo CUODE ────────────────────────────────────────
st.subheader("2. Suma móvil 12M por grupo CUODE")
n_grupos = st.slider("Número de grupos a mostrar", 3, 10, 6, key="n_movil_grupo")
grupo_serie = (dff.groupby(["Fecha", "Grupo"])["CIF"].sum()
               .reset_index().sort_values("Fecha"))
top_grupos = (dff.groupby("Grupo")["CIF"].sum()
              .sort_values(ascending=False).head(n_grupos).index.tolist())

fig2 = go.Figure()
for i, grupo in enumerate(top_grupos):
    sub = grupo_serie[grupo_serie["Grupo"] == grupo].copy()
    sub["CIF_12M"] = sub["CIF"].rolling(12, min_periods=12).sum()
    color = GRUPO_COLORS.get(grupo, _FALLBACK_COLORS[i % len(_FALLBACK_COLORS)])
    fig2.add_trace(go.Scatter(
        x=sub["Fecha"], y=sub["CIF_12M"],
        name=grupo, mode="lines",
        line=dict(color=color, width=2),
        hovertemplate=f"<b>{grupo}</b><br>%{{x|%b %Y}}: $%{{y:,.1f}} M<extra></extra>",
    ))
fig2.update_layout(
    height=420, plot_bgcolor=PLOT_BG,
    yaxis=dict(title="Millones USD (CIF)", tickformat=",.1f", gridcolor=GRID_COLOR),
    legend=dict(orientation="h", y=-0.15, font=dict(size=10)),
    hovermode="x unified",
)
fig2.update_xaxes(gridcolor=GRID_COLOR)
st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── Gráfico 3: Por país de origen ─────────────────────────────────────
st.subheader("3. Suma móvil 12M por país de origen")
n_paises_n = st.slider("Número de países a mostrar", 3, 10, 5, key="n_movil_pais")
pais_serie = (dff.groupby(["Fecha", "Pais_Origen"])["CIF"].sum()
              .reset_index().sort_values("Fecha"))
top_paises = (dff.groupby("Pais_Origen")["CIF"].sum()
              .sort_values(ascending=False).head(n_paises_n).index.tolist())

fig3 = go.Figure()
for i, pais in enumerate(top_paises):
    sub = pais_serie[pais_serie["Pais_Origen"] == pais].copy()
    sub["CIF_12M"] = sub["CIF"].rolling(12, min_periods=12).sum()
    color = get_country_color(str(pais), i)
    fig3.add_trace(go.Scatter(
        x=sub["Fecha"], y=sub["CIF_12M"],
        name=str(pais), mode="lines",
        line=dict(color=color, width=2),
        hovertemplate=f"<b>{pais}</b><br>%{{x|%b %Y}}: $%{{y:,.1f}} M<extra></extra>",
    ))
fig3.update_layout(
    height=420, plot_bgcolor=PLOT_BG,
    yaxis=dict(title="Millones USD (CIF)", tickformat=",.1f", gridcolor=GRID_COLOR),
    legend=dict(orientation="h", y=-0.15, font=dict(size=10)),
    hovermode="x unified",
)
fig3.update_xaxes(gridcolor=GRID_COLOR)
st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ── Gráfico 4: Por subgrupo CUODE ─────────────────────────────────────
st.subheader("4. Suma móvil 12M por subgrupo CUODE")
n_subgrupos = st.slider("Número de subgrupos a mostrar", 3, 10, 6, key="n_movil_subgrupo")
subgrupo_serie = (dff.groupby(["Fecha", "Subgrupo"])["CIF"].sum()
                  .reset_index().sort_values("Fecha"))
top_subgrupos = (dff.groupby("Subgrupo")["CIF"].sum()
                 .sort_values(ascending=False).head(n_subgrupos).index.tolist())

fig4 = go.Figure()
for i, sub_nombre in enumerate(top_subgrupos):
    sub = subgrupo_serie[subgrupo_serie["Subgrupo"] == sub_nombre].copy()
    sub["CIF_12M"] = sub["CIF"].rolling(12, min_periods=12).sum()
    color = SUBGRUPO_COLORS.get(sub_nombre, _FALLBACK_COLORS[i % len(_FALLBACK_COLORS)])
    fig4.add_trace(go.Scatter(
        x=sub["Fecha"], y=sub["CIF_12M"],
        name=sub_nombre, mode="lines",
        line=dict(color=color, width=2),
        hovertemplate=f"<b>{sub_nombre}</b><br>%{{x|%b %Y}}: $%{{y:,.1f}} M<extra></extra>",
    ))
fig4.update_layout(
    height=420, plot_bgcolor=PLOT_BG,
    yaxis=dict(title="Millones USD (CIF)", tickformat=",.1f", gridcolor=GRID_COLOR),
    legend=dict(orientation="h", y=-0.2, font=dict(size=10)),
    hovermode="x unified",
)
fig4.update_xaxes(gridcolor=GRID_COLOR)
st.plotly_chart(fig4, use_container_width=True)

st.divider()

# ── Tabla: Último dato suma móvil 12M por grupo ───────────────────────
st.subheader("5. Tabla: último dato suma móvil 12M por grupo CUODE")
ultima_fecha = serie["Fecha"].max()
ventana = dff[dff["Fecha"] > (ultima_fecha - pd.DateOffset(months=12))]
tabla_grp = ventana.groupby("Grupo").agg(
    CIF_12M=("CIF", "sum"),
    TM_12M=("TM",  "sum"),
    N_Paises=("Pais_Origen", "nunique"),
).reset_index().sort_values("CIF_12M", ascending=False)
tabla_grp["CIF_12M"] = tabla_grp["CIF_12M"].apply(lambda x: f"{x:,.1f}")
tabla_grp["TM_12M"]  = tabla_grp["TM_12M"].apply(lambda x: f"{x:,.0f}")
tabla_grp.columns = ["Grupo CUODE", "CIF 12M (M USD)", "TM 12M", "N° Países"]
st.dataframe(tabla_grp, use_container_width=True, hide_index=True, height=500)
