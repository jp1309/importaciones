"""
Módulo 4: Drilldown a nivel de subpartida arancelaria.

Jerarquía de selección: Grupo CUODE → Subgrupo
El subgrupo hace el rol de "producto" (no existe nivel intermedio en CUODE).
Al seleccionar un subgrupo, se muestran:
  1. Composición por subpartida (Top N por CIF, slider 3-15) — bar horizontal
     con código arancelario + nombre truncado
  2. Evolución temporal de las principales subpartidas — líneas por año
  3. Detalle de una subpartida específica (selector interno):
     - KPIs: CIF total, TM, precio implícito, N° países de origen
     - Evolución anual (barras) + Top 10 países de origen (barras coloreadas)

Estrategia de carga:
  - load_data_aggregated() para los selectores y filtros del sidebar (~390K filas)
  - load_data() solo al seleccionar un subgrupo (parquet completo, ~6.7M filas)
CIF en millones USD | TM en toneladas métricas
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from data_loader import (load_data, load_data_aggregated, filtros_sidebar,
                         get_country_color, GRUPO_MAP, SUBGRUPO_MAP)

st.set_page_config(page_title="Drilldown Subpartida – Importaciones", page_icon="🔍", layout="wide")
st.title("Drilldown por Subpartida Arancelaria")
st.caption("Explora el detalle a nivel de subpartida arancelaria para cada subgrupo y origen | Valores en millones USD (CIF)")

PLOT_BG    = "white"
GRID_COLOR = "#f0f0f0"

df_agg = load_data_aggregated()
dff_agg, rango, grupos_sel, paises = filtros_sidebar(df_agg, key_prefix="drill")

# ── Selector cascada Grupo → Subgrupo ────────────────────────────────
datos = dff_agg[["Cod_Grupo", "Grupo", "Cod_Subgrupo", "Subgrupo"]].drop_duplicates()

col_g, col_s = st.columns(2)

with col_g:
    grupo_opts = datos[["Cod_Grupo", "Grupo"]].drop_duplicates().copy()
    grupo_opts["Label"] = grupo_opts["Cod_Grupo"] + " – " + grupo_opts["Grupo"]
    grupo_opts["_sort"] = grupo_opts["Cod_Grupo"].apply(
        lambda x: "ZZZ" if not x.isdigit() else x.zfill(3)
    )
    grupo_opts = grupo_opts.sort_values("_sort")
    grupo_sel = st.selectbox(
        "Grupo CUODE", [""] + grupo_opts["Label"].tolist(),
        format_func=lambda x: "Seleccionar grupo..." if x == "" else x,
        key="drill_grupo_sel"
    )

with col_s:
    if grupo_sel:
        grupo_nombre = grupo_sel.split(" – ", 1)[1]
        sg_opts = datos[datos["Grupo"] == grupo_nombre][["Cod_Subgrupo", "Subgrupo"]].drop_duplicates().copy()
        sg_opts["Label"] = sg_opts["Cod_Subgrupo"] + " – " + sg_opts["Subgrupo"]
        sg_opts["_sort"] = sg_opts["Cod_Subgrupo"].apply(
            lambda x: "ZZZ" if not x.isdigit() else x.zfill(4)
        )
        sg_opts = sg_opts.sort_values("_sort")
        subgrupo_sel = st.selectbox(
            "Subgrupo", [""] + sg_opts["Label"].tolist(),
            format_func=lambda x: "Seleccionar subgrupo..." if x == "" else x,
            key="drill_subgrupo_sel"
        )
    else:
        st.selectbox("Subgrupo", [""],
                     format_func=lambda x: "Seleccionar grupo primero...",
                     key="drill_sg_empty")
        subgrupo_sel = ""

if not grupo_sel or not subgrupo_sel:
    st.info("Selecciona un Grupo y un Subgrupo para explorar sus subpartidas.", icon="👆")
    st.stop()

grupo_nombre   = grupo_sel.split(" – ", 1)[1]
subgrupo_nombre = subgrupo_sel.split(" – ", 1)[1]

# Cargar dataset completo (con subpartidas)
with st.spinner("Cargando subpartidas..."):
    df_full = load_data()

# Aplicar los mismos filtros del sidebar
dff = df_full[(df_full["Anio"] >= rango[0]) & (df_full["Anio"] <= rango[1])]
if grupos_sel:
    dff = dff[dff["Grupo"].isin(grupos_sel)]
if paises:
    dff = dff[dff["Pais_Origen"].isin(paises)]

dff_sg = dff[(dff["Grupo"] == grupo_nombre) & (dff["Subgrupo"] == subgrupo_nombre)]

cif_total = dff_sg["CIF"].sum()
tm_total  = dff_sg["TM"].sum()
n_sp      = dff_sg["Subpartida"].nunique()
n_paises  = dff_sg["Pais_Origen"].nunique()

st.markdown(
    f"**{subgrupo_nombre}** — {n_sp} subpartidas | "
    f"{n_paises} países de origen | "
    f"CIF total: ${cif_total:,.1f} millones USD"
)

st.divider()

# ── 1. Composición por subpartida (bar + donut) ───────────────────────
st.subheader(f"1. Composición por subpartida — {subgrupo_nombre}")
n_sub_slider = st.slider("Subpartidas a mostrar", 3, 15, 10, key="n_sub_comp")

top_sp = (dff_sg.groupby(["Cod_Subpartida", "Subpartida"], observed=True)["CIF"]
          .sum().sort_values(ascending=False).head(n_sub_slider).reset_index())

fig1a = go.Figure(go.Bar(
    x=top_sp["CIF"],
    y=[f"{str(r.Cod_Subpartida)[:10]} – {str(r.Subpartida)[:45]}" for r in top_sp.itertuples()],
    orientation="h",
    marker_color="#2563eb",
    hovertemplate="<b>%{y}</b><br>CIF: $%{x:,.1f} M<extra></extra>",
))
fig1a.update_layout(
    height=500, plot_bgcolor=PLOT_BG,
    xaxis=dict(title="Millones USD (CIF)", tickformat=",.1f", gridcolor=GRID_COLOR),
    yaxis=dict(autorange="reversed"),
    margin=dict(l=380, t=10, b=30, r=20),
)
fig1a.update_xaxes(gridcolor=GRID_COLOR)
st.plotly_chart(fig1a, width="stretch")

st.divider()

# ── 2. Evolución temporal de principales subpartidas ──────────────────
st.subheader(f"2. Evolución temporal — principales subpartidas de {subgrupo_nombre}")

evol = (dff_sg.groupby(["Anio", "Subpartida"], observed=True)["CIF"]
        .sum().reset_index())
top_sp_names = top_sp["Subpartida"].tolist()
evol_top = evol[evol["Subpartida"].isin(top_sp_names)]

fig2 = px.line(
    evol_top, x="Anio", y="CIF", color="Subpartida",
    labels={"CIF": "Millones USD (CIF)", "Anio": "Año"},
)
fig2.update_layout(
    height=420, plot_bgcolor=PLOT_BG,
    margin=dict(t=20, b=30),
    yaxis=dict(title="Millones USD (CIF)", tickformat=",.1f", gridcolor=GRID_COLOR),
    legend=dict(orientation="h", y=-0.2, font=dict(size=9)),
    hovermode="x unified",
)
fig2.update_xaxes(gridcolor=GRID_COLOR)
fig2.update_yaxes(gridcolor=GRID_COLOR)
st.plotly_chart(fig2, width="stretch")

st.divider()

# ── 3. Detalle de una subpartida específica ───────────────────────────
st.subheader("3. Detalle de una subpartida")

sp_opts = (dff_sg.groupby(["Cod_Subpartida", "Subpartida"], observed=True)["CIF"]
           .sum().sort_values(ascending=False).reset_index())
sp_opts["Label"] = (sp_opts["Cod_Subpartida"].astype(str)
                    + " – " + sp_opts["Subpartida"].astype(str).str[:60])

sp_sel_label = st.selectbox(
    "Seleccionar subpartida",
    sp_opts["Label"].tolist(),
    key="drill_sp_det"
)

cod_sp_sel = sp_sel_label.split(" – ")[0]
dfsp = dff_sg[dff_sg["Cod_Subpartida"] == cod_sp_sel].copy()
nombre_sp = str(dfsp["Subpartida"].iloc[0]) if len(dfsp) > 0 else cod_sp_sel

cif_sp  = dfsp["CIF"].sum()
tm_sp   = dfsp["TM"].sum()
precio_imp = cif_sp / tm_sp * 1_000_000 if tm_sp > 0 else 0

k1, k2, k3, k4 = st.columns(4)
k1.metric("CIF Total", f"${cif_sp:,.1f} M")
k2.metric("Volumen Total (TM)", f"{tm_sp:,.0f}")
k3.metric("Precio Implícito", f"${precio_imp:,.0f} USD/TM")
k4.metric("N° Países de Origen", f"{dfsp['Pais_Origen'].nunique()}")

col_anual, col_paises = st.columns(2)

with col_anual:
    st.markdown("**Evolución anual (CIF)**")
    anual_sp = dfsp.groupby("Anio")["CIF"].sum().reset_index()
    fig3a = go.Figure(go.Bar(
        x=anual_sp["Anio"], y=anual_sp["CIF"],
        marker_color="#2563eb",
        hovertemplate="<b>%{x}</b><br>CIF: $%{y:,.1f} M<extra></extra>",
    ))
    fig3a.update_layout(
        height=350, plot_bgcolor=PLOT_BG,
        margin=dict(t=10, b=30),
        yaxis=dict(title="Millones USD (CIF)", tickformat=",.1f", gridcolor=GRID_COLOR),
        xaxis_title="Año",
    )
    fig3a.update_xaxes(gridcolor=GRID_COLOR)
    fig3a.update_yaxes(gridcolor=GRID_COLOR)
    st.plotly_chart(fig3a, width="stretch")

with col_paises:
    st.markdown("**Top 10 países de origen**")
    top_p = (dfsp.groupby("Pais_Origen")["CIF"].sum()
             .sort_values(ascending=True).tail(10).reset_index())
    colors_p = [get_country_color(str(p), i) for i, p in enumerate(top_p["Pais_Origen"])]
    fig3b = go.Figure(go.Bar(
        x=top_p["CIF"], y=[str(p) for p in top_p["Pais_Origen"]],
        orientation="h", marker_color=colors_p,
        hovertemplate="<b>%{y}</b><br>CIF: $%{x:,.1f} M<extra></extra>",
    ))
    fig3b.update_layout(
        height=350, plot_bgcolor=PLOT_BG,
        xaxis=dict(title="Millones USD (CIF)", tickformat=",.1f", gridcolor=GRID_COLOR),
        margin=dict(l=180, t=10, b=30, r=20),
    )
    fig3b.update_xaxes(gridcolor=GRID_COLOR)
    fig3b.update_yaxes(gridcolor=GRID_COLOR)
    st.plotly_chart(fig3b, width="stretch")

