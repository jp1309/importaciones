"""
Módulo 2: Treemap y Sunburst de composición CUODE
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from data_loader import load_data_aggregated, filtros_sidebar, GRUPO_COLORS

st.set_page_config(page_title="Treemap CUODE", layout="wide")
st.title("Composición CUODE — Treemap y Sunburst")
st.caption("Valores en millones USD (CIF).")

df = load_data_aggregated()
dff, rango, grupos_sel, paises = filtros_sidebar(df, key_prefix="tree")

tree = dff.groupby(["Grupo", "Subgrupo"])["CIF"].sum().reset_index()
tree = tree[tree["CIF"] > 0]

# ── Gráfico 1: Treemap ────────────────────────────────────────────────
st.subheader("Treemap: Grupo → Subgrupo")
fig1 = px.treemap(
    tree,
    path=["Grupo", "Subgrupo"],
    values="CIF",
    color="Grupo",
    color_discrete_map=GRUPO_COLORS,
)
fig1.update_traces(
    textinfo="label+value+percent parent",
    hovertemplate="<b>%{label}</b><br>CIF: $%{value:,.1f} M<br>%{percentParent:.1%} del grupo<extra></extra>",
)
fig1.update_layout(height=500, margin=dict(t=30, b=10, l=10, r=10))
st.plotly_chart(fig1, use_container_width=True)

st.divider()

# ── Gráfico 2: Sunburst ───────────────────────────────────────────────
st.subheader("Sunburst: Grupo → Subgrupo")
fig2 = px.sunburst(
    tree,
    path=["Grupo", "Subgrupo"],
    values="CIF",
    color="Grupo",
    color_discrete_map=GRUPO_COLORS,
)
fig2.update_traces(
    textinfo="label+percent parent",
    insidetextorientation="radial",
)
fig2.update_layout(height=550, margin=dict(t=30, b=10, l=10, r=10))
st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── Gráfico 3: Evolución anual por grupo (area 100% sólida) ──────────
st.subheader("Evolución de la composición por grupo (% del total)")
grupo_anual = dff.groupby(["Anio", "Grupo"])["CIF"].sum().reset_index()
total_anual = grupo_anual.groupby("Anio")["CIF"].sum().rename("Total")
grupo_anual = grupo_anual.merge(total_anual, on="Anio")
grupo_anual["Pct"] = grupo_anual["CIF"] / grupo_anual["Total"] * 100

grupos_ord = (grupo_anual.groupby("Grupo")["CIF"].sum()
              .sort_values(ascending=False).index.tolist())
fig3 = go.Figure()
for grupo in reversed(grupos_ord):
    sub = grupo_anual[grupo_anual["Grupo"] == grupo]
    color = GRUPO_COLORS.get(grupo, "#d1d5db")
    fig3.add_trace(go.Scatter(
        x=sub["Anio"], y=sub["Pct"], name=grupo,
        mode="lines", stackgroup="one",
        line=dict(width=0.5, color=color), fillcolor=color,
        hovertemplate=f"<b>{grupo}</b><br>%{{y:.1f}}%<extra></extra>",
    ))
fig3.update_layout(
    height=420,
    yaxis=dict(title="Participación (%)", ticksuffix="%", dtick=10, range=[0, 100]),
    legend=dict(orientation="h", y=-0.3),
)
st.plotly_chart(fig3, use_container_width=True)
