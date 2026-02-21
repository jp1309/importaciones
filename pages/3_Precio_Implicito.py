"""
Módulo 3: Precio implícito CIF/TM por subgrupo y país de origen
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd

from data_loader import load_data_aggregated, GRUPO_COLORS, SUBGRUPO_MAP, GRUPO_MAP, _FALLBACK_COLORS

st.set_page_config(page_title="Precio Implícito", layout="wide")
st.title("Precio Implícito CIF/TM")
st.caption("Precio implícito = CIF (miles USD) / TM. Selecciona un subgrupo para explorar.")

df = load_data_aggregated()

# ── Selector cascada Grupo → Subgrupo ────────────────────────────────
datos = df[["Cod_Grupo", "Grupo", "Cod_Subgrupo", "Subgrupo"]].drop_duplicates()

grupo_opts = datos[["Cod_Grupo", "Grupo"]].drop_duplicates()
grupo_opts["Label"] = grupo_opts["Cod_Grupo"] + " – " + grupo_opts["Grupo"]
grupo_opts["_sort"] = grupo_opts["Cod_Grupo"].apply(
    lambda x: "ZZZ" if not str(x).isdigit() else str(x).zfill(3)
)
grupo_opts = grupo_opts.sort_values("_sort")

col1, col2 = st.columns(2)
with col1:
    grupo_sel = st.selectbox(
        "Grupo CUODE",
        [""] + grupo_opts["Label"].tolist(),
        format_func=lambda x: "Seleccionar grupo..." if x == "" else x,
        key="pi_grupo"
    )
with col2:
    if grupo_sel:
        grupo_nombre = grupo_sel.split(" – ", 1)[1]
        subgrupo_opts = datos[datos["Grupo"] == grupo_nombre][["Cod_Subgrupo", "Subgrupo"]].drop_duplicates()
        subgrupo_opts["Label"] = subgrupo_opts["Cod_Subgrupo"] + " – " + subgrupo_opts["Subgrupo"]
        subgrupo_opts["_sort"] = subgrupo_opts["Cod_Subgrupo"].apply(
            lambda x: "ZZZ" if not str(x).isdigit() else str(x).zfill(4)
        )
        subgrupo_opts = subgrupo_opts.sort_values("_sort")
        subgrupo_sel = st.selectbox(
            "Subgrupo",
            [""] + subgrupo_opts["Label"].tolist(),
            format_func=lambda x: "Seleccionar subgrupo..." if x == "" else x,
            key="pi_subgrupo"
        )
    else:
        st.selectbox("Subgrupo", [""], format_func=lambda x: "Seleccionar grupo primero...", key="pi_subgrupo_empty")
        st.stop()

if not grupo_sel or not subgrupo_sel:
    st.info("Selecciona un grupo y subgrupo para ver el precio implícito.")
    st.stop()

subgrupo_nombre = subgrupo_sel.split(" – ", 1)[1]
dff = df[df["Subgrupo"] == subgrupo_nombre].copy()
dff = dff[dff["TM"] > 0]
dff["Precio_CIF"] = (dff["CIF"] * 1000) / dff["TM"]  # USD/TM

# ── Gráfico 1: Precio implícito mensual con promedio móvil 12M ────────
st.subheader(f"Precio implícito mensual — {subgrupo_nombre}")
serie = (dff.groupby("Fecha")
         .apply(lambda x: pd.Series({
             "CIF": x["CIF"].sum(),
             "TM":  x["TM"].sum()
         })).reset_index())
serie["Precio"] = (serie["CIF"] * 1000) / serie["TM"].replace(0, float("nan"))
serie["MA12"]   = serie["Precio"].rolling(12).mean()
serie = serie.sort_values("Fecha")

fig1 = go.Figure()
fig1.add_trace(go.Scatter(
    x=serie["Fecha"], y=serie["Precio"],
    name="Precio mensual", mode="lines",
    line=dict(color="#93c5fd", width=1),
    hovertemplate="<b>%{x|%b %Y}</b><br>USD/TM: %{y:,.0f}<extra></extra>",
))
fig1.add_trace(go.Scatter(
    x=serie["Fecha"], y=serie["MA12"],
    name="Promedio móvil 12M", mode="lines",
    line=dict(color="#1d4ed8", width=2.5),
    hovertemplate="<b>%{x|%b %Y}</b><br>MA12: %{y:,.0f} USD/TM<extra></extra>",
))
fig1.update_layout(
    height=380,
    yaxis=dict(title="USD / TM (CIF)", tickformat=",.0f"),
    legend=dict(orientation="h", y=1.08),
    hovermode="x unified",
)
st.plotly_chart(fig1, use_container_width=True)

st.divider()

# ── Gráfico 2: Precio por país de origen (top 8) ─────────────────────
st.subheader(f"Precio implícito CIF/TM por país de origen")
top_paises = (dff.groupby("Pais_Origen")["CIF"].sum()
              .sort_values(ascending=False).head(8).index.tolist())

fig2 = go.Figure()
for i, pais in enumerate(top_paises):
    sub = dff[dff["Pais_Origen"] == pais].groupby("Fecha").apply(
        lambda x: pd.Series({"CIF": x["CIF"].sum(), "TM": x["TM"].sum()})
    ).reset_index()
    sub["Precio"] = (sub["CIF"] * 1000) / sub["TM"].replace(0, float("nan"))
    sub = sub.sort_values("Fecha")
    color = _FALLBACK_COLORS[i % len(_FALLBACK_COLORS)]
    fig2.add_trace(go.Scatter(
        x=sub["Fecha"], y=sub["Precio"],
        name=pais, mode="lines",
        line=dict(color=color, width=1.5),
        hovertemplate=f"<b>{pais}</b><br>%{{x|%b %Y}}<br>%{{y:,.0f}} USD/TM<extra></extra>",
    ))
fig2.update_layout(
    height=400,
    yaxis=dict(title="USD / TM (CIF)", tickformat=",.0f"),
    legend=dict(orientation="h", y=-0.3),
    hovermode="x unified",
)
st.plotly_chart(fig2, use_container_width=True)
