"""
Módulo 2: Treemap y Sunburst de composición CUODE
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from data_loader import load_data_aggregated, filtros_sidebar, GRUPO_COLORS, _FALLBACK_COLORS

st.set_page_config(page_title="Treemap CUODE – Importaciones", page_icon="🌳", layout="wide")
st.title("Treemap Jerárquico de Importaciones")
st.caption("Estructura: Grupo → Subgrupo | Clasificación CUODE del Banco Central del Ecuador")

PLOT_BG    = "white"
GRID_COLOR = "#f0f0f0"

df = load_data_aggregated()
dff, rango, grupos_sel, paises = filtros_sidebar(df, key_prefix="tree")

# ── Selectores de métrica y color ─────────────────────────────────────
col_opt1, col_opt2 = st.columns([1, 2])
with col_opt1:
    metrica = st.radio("Métrica", ["CIF (millones USD)", "Volumen (TM)"],
                       horizontal=True, key="tree_metrica")
    val_col = "CIF" if "CIF" in metrica else "TM"
with col_opt2:
    color_by = st.radio("Color por", ["Grupo", "Valor absoluto"],
                        horizontal=True, key="tree_color")

tree = dff.groupby(["Grupo", "Subgrupo"]).agg(CIF=("CIF","sum"), TM=("TM","sum")).reset_index()
tree["Grupo"]    = tree["Grupo"].astype(str)
tree["Subgrupo"] = tree["Subgrupo"].astype(str)
tree = tree[tree[val_col] > 0]

# ── Gráfico 1: Treemap completo Grupo → Subgrupo ──────────────────────
st.subheader("1. Treemap: Grupo → Subgrupo")

if color_by == "Grupo":
    fig1 = px.treemap(
        tree, path=["Grupo", "Subgrupo"], values=val_col,
        color="Grupo", color_discrete_map=GRUPO_COLORS,
        custom_data=["CIF", "TM"],
    )
else:
    fig1 = px.treemap(
        tree, path=["Grupo", "Subgrupo"], values=val_col,
        color=val_col,
        color_continuous_scale="Blues",
        custom_data=["CIF", "TM"],
    )

fig1.update_traces(
    textinfo="label+value+percent parent",
    hovertemplate="<b>%{label}</b><br>CIF: $%{customdata[0]:,.1f} M<br>TM: %{customdata[1]:,.0f}<extra></extra>",
)
fig1.update_layout(height=650, margin=dict(t=30, b=10, l=10, r=10))
st.plotly_chart(fig1, width="stretch")

st.divider()

# ── Gráfico 2: Evolución anual por grupo (area 100% sólida) ──────────
st.subheader("2. Evolución de la composición por grupo (% del total)")
grupo_anual = dff.groupby(["Anio", "Grupo"])["CIF"].sum().reset_index()
total_anual = grupo_anual.groupby("Anio")["CIF"].sum().rename("Total")
grupo_anual = grupo_anual.merge(total_anual, on="Anio")
grupo_anual["Pct"] = grupo_anual["CIF"] / grupo_anual["Total"] * 100

grupos_ord = (grupo_anual.groupby("Grupo")["CIF"].sum()
              .sort_values(ascending=False).index.tolist())
fig4 = go.Figure()
for grupo in reversed(grupos_ord):
    sub = grupo_anual[grupo_anual["Grupo"] == grupo]
    color = GRUPO_COLORS.get(grupo, "#d1d5db")
    fig4.add_trace(go.Scatter(
        x=sub["Anio"], y=sub["Pct"], name=grupo,
        mode="lines", stackgroup="one",
        line=dict(width=0.5, color=color), fillcolor=color,
        hovertemplate=f"<b>{grupo}</b><br>%{{y:.1f}}%<extra></extra>",
    ))
fig4.update_layout(
    height=420, plot_bgcolor=PLOT_BG,
    margin=dict(t=20, b=30),
    yaxis=dict(title="Participación (%)", ticksuffix="%", dtick=10,
               range=[0, 100], gridcolor=GRID_COLOR),
    legend=dict(orientation="h", y=-0.2, font=dict(size=10)),
    hovermode="x unified",
)
fig4.update_xaxes(gridcolor=GRID_COLOR)
fig4.update_yaxes(gridcolor=GRID_COLOR)
st.plotly_chart(fig4, width="stretch")

st.divider()

# ── Treemap por País de Origen ────────────────────────────────────────
st.subheader("3. Treemap: Grupo → Subgrupo → País de Origen (Top 15)")
top15_paises = (dff.groupby("Pais_Origen")["CIF"].sum()
                .sort_values(ascending=False).head(15).index.tolist())
pais_tree = (dff[dff["Pais_Origen"].isin(top15_paises)]
             .groupby(["Grupo", "Subgrupo", "Pais_Origen"])["CIF"].sum()
             .reset_index())
pais_tree["Grupo"]       = pais_tree["Grupo"].astype(str)
pais_tree["Subgrupo"]    = pais_tree["Subgrupo"].astype(str)
pais_tree["Pais_Origen"] = pais_tree["Pais_Origen"].astype(str)
pais_tree = pais_tree[pais_tree["CIF"] > 0]
fig5 = px.treemap(
    pais_tree, path=["Grupo", "Subgrupo", "Pais_Origen"], values="CIF",
    color="Grupo", color_discrete_map=GRUPO_COLORS,
)
fig5.update_traces(textinfo="label+percent parent")
fig5.update_layout(height=650, margin=dict(t=30, b=10, l=10, r=10), showlegend=False)
st.plotly_chart(fig5, width="stretch")

