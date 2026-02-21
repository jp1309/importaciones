"""
Módulo 4: Drilldown a nivel de subpartida arancelaria
Usa load_data_aggregated() para selectores y solo carga el dataset completo
cuando se necesita el detalle a nivel subpartida.
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from data_loader import (load_data, load_data_aggregated, filtros_sidebar,
                         _FALLBACK_COLORS, get_country_color,
                         GRUPO_MAP, SUBGRUPO_MAP)

st.set_page_config(page_title="Drilldown Subpartida – Importaciones", page_icon="🔍", layout="wide")
st.title("Drilldown por Subpartida Arancelaria")
st.caption("Explora el detalle a nivel de subpartida arancelaria para cada subgrupo y origen | Valores en millones USD (CIF)")

PLOT_BG    = "white"
GRID_COLOR = "#f0f0f0"

# ── Datos livianos para selectores (~390K filas, carga en 4s) ─────────
df_agg = load_data_aggregated()
dff_agg, rango, grupos_sel, paises = filtros_sidebar(df_agg, key_prefix="drill")

# ── Selector cascada Grupo → Subgrupo ────────────────────────────────
datos = dff_agg[["Cod_Grupo", "Grupo", "Cod_Subgrupo", "Subgrupo"]].drop_duplicates()

c1, c2, c3 = st.columns(3)

with c1:
    grupo_opts = datos[["Cod_Grupo", "Grupo"]].drop_duplicates().copy()
    grupo_opts["Label"] = grupo_opts["Cod_Grupo"] + " – " + grupo_opts["Grupo"]
    grupo_opts["_sort"] = grupo_opts["Cod_Grupo"].apply(
        lambda x: "ZZZ" if not x.isdigit() else x.zfill(3)
    )
    grupo_opts = grupo_opts.sort_values("_sort")
    grupo_sel = st.selectbox(
        "Grupo CUODE",
        [""] + grupo_opts["Label"].tolist(),
        format_func=lambda x: "Seleccionar grupo..." if x == "" else x,
        key="drill_grupo_sel"
    )

with c2:
    if grupo_sel:
        grupo_nombre = grupo_sel.split(" – ", 1)[1]
        sg_opts = datos[datos["Grupo"] == grupo_nombre][["Cod_Subgrupo", "Subgrupo"]].drop_duplicates().copy()
        sg_opts["Label"] = sg_opts["Cod_Subgrupo"] + " – " + sg_opts["Subgrupo"]
        sg_opts["_sort"] = sg_opts["Cod_Subgrupo"].apply(
            lambda x: "ZZZ" if not x.isdigit() else x.zfill(4)
        )
        sg_opts = sg_opts.sort_values("_sort")
        subgrupo_sel = st.selectbox(
            "Subgrupo",
            [""] + sg_opts["Label"].tolist(),
            format_func=lambda x: "Seleccionar subgrupo..." if x == "" else x,
            key="drill_subgrupo_sel"
        )
    else:
        st.selectbox("Subgrupo", [""], format_func=lambda x: "Seleccionar grupo primero...", key="drill_sg_empty")
        subgrupo_sel = ""

# ── Selector de Subpartida: AQUÍ cargamos el dataset completo ────────
with c3:
    if subgrupo_sel:
        subgrupo_nombre = subgrupo_sel.split(" – ", 1)[1]
        # Cargar dataset completo (con subpartidas) solo ahora
        with st.spinner("Cargando subpartidas..."):
            df_full = load_data()
        # Aplicar los mismos filtros que se aplicaron al agregado
        dff = df_full[(df_full["Anio"] >= rango[0]) & (df_full["Anio"] <= rango[1])]
        if grupos_sel:
            dff = dff[dff["Grupo"].isin(grupos_sel)]
        if paises:
            dff = dff[dff["Pais_Origen"].isin(paises)]

        sp_opts = (dff[dff["Subgrupo"] == subgrupo_nombre]
                   .groupby(["Cod_Subpartida","Subpartida"], observed=True)["CIF"].sum()
                   .reset_index().sort_values("CIF", ascending=False))
        # Usar .values.astype(str) para evitar expandir Categorical completo en RAM
        sp_opts["Label"] = (sp_opts["Cod_Subpartida"].values.astype(str)
                            + " — "
                            + pd.Series(sp_opts["Subpartida"].values.astype(str)).str[:50].values)
        subpartida_sel = st.selectbox(
            "Subpartida",
            [""] + sp_opts["Label"].tolist(),
            format_func=lambda x: "Seleccionar subpartida..." if x == "" else x,
            key="drill_sp_sel"
        )
    else:
        st.selectbox("Subpartida", [""], format_func=lambda x: "Seleccionar subgrupo primero...", key="drill_sp_empty")
        subpartida_sel = ""

if not grupo_sel or not subgrupo_sel or not subpartida_sel:
    st.info("Selecciona Grupo → Subgrupo → Subpartida para ver el análisis.")
    st.stop()

cod_sp = subpartida_sel.split(" — ")[0]
dfsp = dff[dff["Cod_Subpartida"] == cod_sp].copy()
nombre_sp = str(dfsp["Subpartida"].iloc[0]) if len(dfsp) > 0 else cod_sp

n_dest = dfsp["Pais_Origen"].nunique()
cif_total = dfsp["CIF"].sum()
st.markdown(
    f"**{nombre_sp}** — {n_dest} orígenes | "
    f"CIF total: ${cif_total:,.1f} millones USD"
)

# ── KPIs de la subpartida ─────────────────────────────────────────────
tm_total   = dfsp["TM"].sum()
precio_imp = cif_total / tm_total * 1_000_000 if tm_total > 0 else 0
n_origenes = dfsp["Pais_Origen"].nunique()

k1, k2, k3, k4 = st.columns(4)
k1.metric("CIF Total (millones USD)", f"${cif_total:,.1f} M")
k2.metric("Volumen Total (TM)", f"{tm_total:,.0f}")
k3.metric("Precio Implícito (USD/TM)", f"${precio_imp:,.0f}")
k4.metric("N° Países de Origen", f"{n_origenes}")

st.divider()

# ── Gráfico 1-2: Composición por subpartida (bar + donut) ─────────────
st.subheader(f"Composición por subpartida — {subgrupo_nombre}")
n_sub_slider = st.slider("Subpartidas a mostrar", 3, 15, 8, key="n_sub_evol")
top_sp = (dff[dff["Subgrupo"] == subgrupo_nombre]
          .groupby(["Cod_Subpartida","Subpartida"])["CIF"].sum()
          .sort_values(ascending=False).head(n_sub_slider).reset_index())

col_bar, col_pie = st.columns(2)
with col_bar:
    fig_bar = go.Figure(go.Bar(
        x=top_sp["CIF"],
        y=[str(s)[:50] for s in top_sp["Subpartida"]],
        orientation="h",
        marker_color="#2563eb",
        customdata=top_sp[["Cod_Subpartida"]].values,
        hovertemplate="<b>%{y}</b><br>Código: %{customdata[0]}<br>CIF: $%{x:,.1f} M<extra></extra>",
    ))
    fig_bar.update_layout(
        height=500, plot_bgcolor=PLOT_BG,
        xaxis=dict(title="Millones USD (CIF)", tickformat=",.1f", gridcolor=GRID_COLOR),
        margin=dict(l=300),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_pie:
    fig_pie = go.Figure(go.Pie(
        labels=[str(s)[:40] for s in top_sp["Subpartida"]],
        values=top_sp["CIF"],
        hole=0.4,
        textinfo="percent",
        textposition="inside",
        hovertemplate="<b>%{label}</b><br>$%{value:,.1f} M<br>%{percent}<extra></extra>",
    ))
    fig_pie.update_layout(
        height=500, showlegend=True,
        legend=dict(orientation="v", font=dict(size=9)),
        margin=dict(t=30),
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# ── Gráfico 3: Evolución temporal de principales subpartidas ──────────
st.subheader(f"Evolución temporal — principales subpartidas de {subgrupo_nombre}")
evol = (dff[dff["Subgrupo"] == subgrupo_nombre]
        .groupby(["Anio", "Subpartida"])["CIF"].sum().reset_index())
top_sp_names = top_sp["Subpartida"].tolist()
evol_top = evol[evol["Subpartida"].isin(top_sp_names)]

fig_evol = px.line(
    evol_top, x="Anio", y="CIF", color="Subpartida",
    labels={"CIF": "Millones USD (CIF)", "Anio": "Año"},
)
fig_evol.update_layout(
    height=420, plot_bgcolor=PLOT_BG,
    margin=dict(t=20, b=30),
    yaxis=dict(title="Millones USD (CIF)", tickformat=",.1f", gridcolor=GRID_COLOR),
    legend=dict(orientation="h", y=-0.2, font=dict(size=9)),
    hovermode="x unified",
)
fig_evol.update_xaxes(gridcolor=GRID_COLOR)
fig_evol.update_yaxes(gridcolor=GRID_COLOR)
st.plotly_chart(fig_evol, use_container_width=True)

st.divider()

# ── Detalle de la subpartida seleccionada ─────────────────────────────
st.subheader(f"Detalle — {nombre_sp}")

col_anual, col_paises = st.columns(2)

with col_anual:
    st.markdown("**Evolución anual (CIF)**")
    anual_sp = dfsp.groupby("Anio")["CIF"].sum().reset_index()
    fig_a = go.Figure(go.Bar(
        x=anual_sp["Anio"], y=anual_sp["CIF"],
        marker_color="#2563eb",
        hovertemplate="<b>%{x}</b><br>CIF: $%{y:,.1f} M<extra></extra>",
    ))
    fig_a.update_layout(
        height=350, plot_bgcolor=PLOT_BG,
        margin=dict(t=10, b=30),
        yaxis=dict(title="Millones USD (CIF)", tickformat=",.1f", gridcolor=GRID_COLOR),
        xaxis_title="Año",
    )
    fig_a.update_xaxes(gridcolor=GRID_COLOR)
    fig_a.update_yaxes(gridcolor=GRID_COLOR)
    st.plotly_chart(fig_a, use_container_width=True)

with col_paises:
    st.markdown("**Top 10 países de origen**")
    top_p = (dfsp.groupby("Pais_Origen")["CIF"].sum()
             .sort_values(ascending=True).tail(10).reset_index())
    colors_p = [get_country_color(str(p), i) for i, p in enumerate(top_p["Pais_Origen"])]
    fig_p = go.Figure(go.Bar(
        x=top_p["CIF"], y=[str(p) for p in top_p["Pais_Origen"]],
        orientation="h", marker_color=colors_p,
        hovertemplate="<b>%{y}</b><br>CIF: $%{x:,.1f} M<extra></extra>",
    ))
    fig_p.update_layout(
        height=350, plot_bgcolor=PLOT_BG,
        xaxis=dict(title="Millones USD (CIF)", tickformat=",.1f", gridcolor=GRID_COLOR),
        margin=dict(l=180, t=10, b=30, r=20),
    )
    fig_p.update_xaxes(gridcolor=GRID_COLOR)
    fig_p.update_yaxes(gridcolor=GRID_COLOR)
    st.plotly_chart(fig_p, use_container_width=True)

