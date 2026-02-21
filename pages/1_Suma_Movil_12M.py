"""
Módulo 1: Suma Móvil 12 meses de importaciones
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from data_loader import load_data_aggregated, filtros_sidebar, GRUPO_COLORS, _FALLBACK_COLORS

st.set_page_config(page_title="Suma Móvil 12M", layout="wide")
st.title("Suma Móvil 12 meses — Importaciones")
st.caption("Valores en millones USD (CIF). La suma móvil suaviza estacionalidad.")

df = load_data_aggregated()
dff, rango, grupos_sel, paises = filtros_sidebar(df, key_prefix="sm")

# Preparar serie mensual
serie = dff.groupby("Fecha")[["CIF", "TM"]].sum().reset_index().sort_values("Fecha")
serie["CIF_12M"] = serie["CIF"].rolling(12).sum()
serie["TM_12M"]  = serie["TM"].rolling(12).sum()

# ── Gráfico 1: Suma móvil 12M total (CIF) ────────────────────────────
st.subheader("Suma móvil 12M — Total importaciones (CIF)")
fig1 = go.Figure()
fig1.add_trace(go.Scatter(
    x=serie["Fecha"], y=serie["CIF"],
    name="Mensual", mode="lines",
    line=dict(color="#93c5fd", width=1),
    hovertemplate="<b>%{x|%b %Y}</b><br>CIF: $%{y:,.1f} M<extra></extra>",
))
fig1.add_trace(go.Scatter(
    x=serie["Fecha"], y=serie["CIF_12M"],
    name="Suma 12M", mode="lines",
    line=dict(color="#1d4ed8", width=2.5),
    hovertemplate="<b>%{x|%b %Y}</b><br>12M: $%{y:,.1f} M<extra></extra>",
))
fig1.update_layout(
    height=380,
    yaxis=dict(title="Millones USD (CIF)", tickformat=",.1f"),
    legend=dict(orientation="h", y=1.08),
    hovermode="x unified",
)
st.plotly_chart(fig1, use_container_width=True)

st.divider()

# ── Gráfico 2: Por grupo (líneas) ─────────────────────────────────────
st.subheader("Suma móvil 12M por grupo CUODE")
grupo_serie = (dff.groupby(["Fecha", "Grupo"])["CIF"].sum()
               .reset_index().sort_values("Fecha"))
top_grupos = (dff.groupby("Grupo")["CIF"].sum()
              .sort_values(ascending=False).head(6).index.tolist())

fig2 = go.Figure()
for i, grupo in enumerate(top_grupos):
    sub = grupo_serie[grupo_serie["Grupo"] == grupo].copy()
    sub["CIF_12M"] = sub["CIF"].rolling(12).sum()
    color = GRUPO_COLORS.get(grupo, _FALLBACK_COLORS[i % len(_FALLBACK_COLORS)])
    fig2.add_trace(go.Scatter(
        x=sub["Fecha"], y=sub["CIF_12M"],
        name=grupo, mode="lines",
        line=dict(color=color, width=2),
        hovertemplate=f"<b>{grupo}</b><br>%{{x|%b %Y}}<br>12M: $%{{y:,.1f}} M<extra></extra>",
    ))
fig2.update_layout(
    height=400,
    yaxis=dict(title="Millones USD (CIF)", tickformat=",.1f"),
    legend=dict(orientation="h", y=-0.25),
    hovermode="x unified",
)
st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── Tabla resumen anual ───────────────────────────────────────────────
st.subheader("Resumen anual")
tabla = dff.groupby("Anio").agg(
    CIF=("CIF", "sum"),
    FOB=("FOB", "sum"),
    TM=("TM",  "sum"),
).reset_index().sort_values("Anio", ascending=False)
tabla["CIF"] = tabla["CIF"].apply(lambda x: f"{x:,.1f}")
tabla["FOB"] = tabla["FOB"].apply(lambda x: f"{x:,.1f}")
tabla["TM"]  = tabla["TM"].apply(lambda x: f"{x:,.0f}")
tabla.columns = ["Año", "CIF (M USD)", "FOB (M USD)", "TM"]
st.dataframe(tabla, use_container_width=True, hide_index=True)
