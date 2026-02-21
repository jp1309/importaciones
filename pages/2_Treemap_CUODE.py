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
    color_by = st.radio("Color por", ["Grupo", "Valor absoluto", "Crecimiento % último año"],
                        horizontal=True, key="tree_color")

tree = dff.groupby(["Grupo", "Subgrupo"]).agg(CIF=("CIF","sum"), TM=("TM","sum")).reset_index()
tree["Grupo"]    = tree["Grupo"].astype(str)
tree["Subgrupo"] = tree["Subgrupo"].astype(str)
tree = tree[tree[val_col] > 0]

# ── Gráfico 1: Treemap completo Grupo → Subgrupo ──────────────────────
st.subheader("Treemap: Grupo → Subgrupo")

if color_by == "Grupo":
    fig1 = px.treemap(
        tree, path=["Grupo", "Subgrupo"], values=val_col,
        color="Grupo", color_discrete_map=GRUPO_COLORS,
        custom_data=["CIF", "TM"],
    )
elif color_by == "Valor absoluto":
    fig1 = px.treemap(
        tree, path=["Grupo", "Subgrupo"], values=val_col,
        color=val_col,
        color_continuous_scale="Blues",
        custom_data=["CIF", "TM"],
    )
else:
    # Crecimiento último año
    max_a = int(dff["Anio"].max())
    cur  = dff[dff["Anio"] == max_a].groupby(["Grupo","Subgrupo"])[val_col].sum().reset_index(name="cur")
    prev = dff[dff["Anio"] == max_a-1].groupby(["Grupo","Subgrupo"])[val_col].sum().reset_index(name="prev")
    crec = cur.merge(prev, on=["Grupo","Subgrupo"], how="left")
    crec["Crec"] = ((crec["cur"] - crec["prev"]) / crec["prev"] * 100).clip(-100, 200)
    tree = tree.merge(crec[["Grupo","Subgrupo","Crec"]], on=["Grupo","Subgrupo"], how="left")
    fig1 = px.treemap(
        tree, path=["Grupo", "Subgrupo"], values=val_col,
        color="Crec", color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        range_color=[-100, 200],
        custom_data=["CIF", "TM"],
    )

fig1.update_traces(
    textinfo="label+value+percent parent",
    hovertemplate="<b>%{label}</b><br>CIF: $%{customdata[0]:,.1f} M<br>TM: %{customdata[1]:,.0f}<extra></extra>",
)
fig1.update_layout(height=650, margin=dict(t=30, b=10, l=10, r=10))
st.plotly_chart(fig1, use_container_width=True)

st.divider()

col_t2, col_t3 = st.columns(2)

# ── Gráfico 2: Treemap por grupo (1 nivel) ────────────────────────────
with col_t2:
    st.subheader("Composición por grupo")
    grp_flat = dff.groupby("Grupo")[["CIF","TM"]].sum().reset_index()
    grp_flat["Grupo"] = grp_flat["Grupo"].astype(str)
    grp_flat = grp_flat[grp_flat["CIF"] > 0]
    fig2 = px.treemap(
        grp_flat, path=["Grupo"], values="CIF",
        color="Grupo", color_discrete_map=GRUPO_COLORS,
    )
    fig2.update_traces(textinfo="label+percent root")
    fig2.update_layout(height=400, margin=dict(t=30, b=10, l=10, r=10), showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)

# ── Gráfico 3: Sunburst Grupo → Subgrupo ─────────────────────────────
with col_t3:
    st.subheader("Sunburst: Grupo → Subgrupo")
    fig3 = px.sunburst(
        tree[tree["CIF"] > 0],
        path=["Grupo", "Subgrupo"], values="CIF",
        color="Grupo", color_discrete_map=GRUPO_COLORS,
    )
    fig3.update_traces(
        textinfo="label+percent parent",
        insidetextorientation="radial",
        sort=False,
    )
    fig3.update_layout(height=400, margin=dict(t=30, b=10, l=10, r=10))
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ── Gráfico 4: Evolución anual por grupo (area 100% sólida) ──────────
st.subheader("Evolución de la composición sectorial (% del total)")
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
st.plotly_chart(fig4, use_container_width=True)

st.divider()

# ── Treemap por País de Origen ────────────────────────────────────────
st.subheader("Treemap: Grupo → Subgrupo → País de Origen (Top 15)")
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
st.plotly_chart(fig5, use_container_width=True)

st.divider()

# ── Tabla detalle ─────────────────────────────────────────────────────
st.subheader("Tabla detalle")
tabla = (dff.groupby(["Grupo", "Subgrupo"]).agg(
    CIF=("CIF",          "sum"),
    TM=("TM",            "sum"),
    N_Paises=("Pais_Origen", "nunique"),
).reset_index().sort_values("CIF", ascending=False))
tabla["CIF"] = tabla["CIF"].apply(lambda x: f"{x:,.1f}")
tabla["TM"]  = tabla["TM"].apply(lambda x: f"{x:,.0f}")
tabla.columns = ["Grupo", "Subgrupo", "CIF (M USD)", "TM", "N° Países"]
st.dataframe(tabla, use_container_width=True, hide_index=True, height=500)
