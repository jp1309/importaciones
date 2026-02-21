"""
Módulo 4: Drilldown a nivel de subpartida arancelaria
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from data_loader import load_data, filtros_sidebar, _FALLBACK_COLORS

st.set_page_config(page_title="Drilldown Subpartida", layout="wide")
st.title("Drilldown por Subpartida Arancelaria")
st.caption("Valores en millones USD (CIF). Usa los filtros para navegar la jerarquía.")

df = load_data()
dff, rango, grupos_sel, paises = filtros_sidebar(df, key_prefix="drill")

# ── Selector cascada Grupo → Subgrupo → Subpartida ───────────────────
datos = dff[["Cod_Grupo", "Grupo", "Cod_Subgrupo", "Subgrupo",
             "Cod_Subpartida", "Subpartida"]].drop_duplicates()

c1, c2, c3 = st.columns(3)

with c1:
    grupo_opts = datos[["Cod_Grupo", "Grupo"]].drop_duplicates()
    grupo_opts["Label"] = grupo_opts["Cod_Grupo"] + " – " + grupo_opts["Grupo"]
    grupo_opts["_sort"] = grupo_opts["Cod_Grupo"].apply(
        lambda x: "ZZZ" if not str(x).isdigit() else str(x).zfill(3)
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
        sg_opts = datos[datos["Grupo"] == grupo_nombre][["Cod_Subgrupo", "Subgrupo"]].drop_duplicates()
        sg_opts["Label"] = sg_opts["Cod_Subgrupo"] + " – " + sg_opts["Subgrupo"]
        sg_opts["_sort"] = sg_opts["Cod_Subgrupo"].apply(
            lambda x: "ZZZ" if not str(x).isdigit() else str(x).zfill(4)
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

with c3:
    if subgrupo_sel:
        subgrupo_nombre = subgrupo_sel.split(" – ", 1)[1]
        sp_opts = datos[datos["Subgrupo"] == subgrupo_nombre][["Cod_Subpartida", "Subpartida"]].drop_duplicates()
        sp_opts["Label"] = sp_opts["Cod_Subpartida"] + " — " + sp_opts["Subpartida"].str[:50]
        sp_opts = sp_opts.sort_values("Cod_Subpartida")
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
nombre_sp = dfsp["Subpartida"].iloc[0] if len(dfsp) > 0 else cod_sp
st.markdown(f"**Subpartida:** {cod_sp} — {nombre_sp}")

# ── Gráfico 1: Serie mensual CIF ──────────────────────────────────────
st.subheader("Serie mensual (CIF)")
serie = dfsp.groupby("Fecha")[["CIF", "TM"]].sum().reset_index().sort_values("Fecha")
serie["MA12"] = serie["CIF"].rolling(12).mean()

fig1 = go.Figure()
fig1.add_trace(go.Bar(
    x=serie["Fecha"], y=serie["CIF"],
    name="CIF mensual", marker_color="#93c5fd",
    hovertemplate="<b>%{x|%b %Y}</b><br>CIF: $%{y:,.2f} M<extra></extra>",
))
fig1.add_trace(go.Scatter(
    x=serie["Fecha"], y=serie["MA12"],
    name="Promedio móvil 12M", mode="lines",
    line=dict(color="#1d4ed8", width=2),
    hovertemplate="<b>%{x|%b %Y}</b><br>MA12: $%{y:,.2f} M<extra></extra>",
))
fig1.update_layout(
    height=360,
    yaxis=dict(title="Millones USD (CIF)", tickformat=",.2f"),
    legend=dict(orientation="h", y=1.08),
    hovermode="x unified",
)
st.plotly_chart(fig1, use_container_width=True)

st.divider()

col_l, col_r = st.columns(2)

# ── Gráfico 2: Top países ─────────────────────────────────────────────
with col_l:
    st.subheader("Top países de origen")
    top_p = (dfsp.groupby("Pais_Origen")["CIF"].sum()
             .sort_values(ascending=True).tail(10).reset_index())
    fig2 = go.Figure(go.Bar(
        x=top_p["CIF"], y=top_p["Pais_Origen"],
        orientation="h", marker_color="#1d4ed8",
        hovertemplate="<b>%{y}</b><br>CIF: $%{x:,.2f} M<extra></extra>",
    ))
    fig2.update_layout(height=360, xaxis=dict(title="Millones USD (CIF)", tickformat=",.2f"))
    st.plotly_chart(fig2, use_container_width=True)

# ── Gráfico 3: Precio implícito CIF/TM ───────────────────────────────
with col_r:
    st.subheader("Precio implícito CIF/TM")
    serie_p = serie.copy()
    serie_p["Precio"] = (serie_p["CIF"] * 1000) / serie_p["TM"].replace(0, float("nan"))
    serie_p["MA12_p"] = serie_p["Precio"].rolling(12).mean()
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=serie_p["Fecha"], y=serie_p["Precio"],
        name="USD/TM", mode="lines",
        line=dict(color="#93c5fd", width=1),
    ))
    fig3.add_trace(go.Scatter(
        x=serie_p["Fecha"], y=serie_p["MA12_p"],
        name="MA 12M", mode="lines",
        line=dict(color="#1d4ed8", width=2),
    ))
    fig3.update_layout(
        height=360,
        yaxis=dict(title="USD / TM (CIF)", tickformat=",.0f"),
        legend=dict(orientation="h", y=1.08),
        hovermode="x unified",
    )
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ── Tabla detalle anual ───────────────────────────────────────────────
st.subheader("Detalle anual por país")
tabla = (dfsp.groupby(["Anio", "Pais_Origen"])
         .agg(CIF=("CIF", "sum"), TM=("TM", "sum"))
         .reset_index().sort_values(["Anio", "CIF"], ascending=[False, False]))
tabla["CIF"] = tabla["CIF"].apply(lambda x: f"{x:,.2f}")
tabla["TM"]  = tabla["TM"].apply(lambda x: f"{x:,.1f}")
tabla.columns = ["Año", "País de Origen", "CIF (M USD)", "TM"]
st.dataframe(tabla, use_container_width=True, hide_index=True)
