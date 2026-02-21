"""
Dashboard de Importaciones del Ecuador (2000–2025)
Fuente: Banco Central del Ecuador
Autor: Juan Pablo Erráez
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import threading
from plotly.subplots import make_subplots

from data_loader import (
    load_data_aggregated, load_data, filtros_sidebar,
    GRUPO_COLORS, SUBGRUPO_COLORS, _FALLBACK_COLORS, get_country_color, REGION_COLORS,
)

st.set_page_config(
    page_title="Importaciones Ecuador",
    page_icon="📦",
    layout="wide",
)

# ── Estilos CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stMetric"] {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 12px 16px;
}
[data-testid="stMetric"] label {
    color: #495057;
    font-size: 0.85rem;
}
.module-card {
    background: #f8f9fa;
    border: 1px solid #e2e8f0;
    border-radius: 10px;
    padding: 18px;
    margin-bottom: 10px;
    height: 100%;
}
.module-card h4 {
    margin-top: 0;
    color: #1e3a5f;
}
.module-card p {
    color: #4a5568;
    font-size: 0.92rem;
    line-height: 1.5;
}
</style>
""", unsafe_allow_html=True)

# ── Datos y filtros ──────────────────────────────────────────────────
df = load_data_aggregated()
dff, rango, grupos_sel, paises = filtros_sidebar(df, key_prefix="inicio")

# ── Precalentar cache del Drilldown en segundo plano ─────────────────
# load_data() (6.7M filas) se lanza en un thread para que al llegar
# a la página Drilldown ya esté cacheado y cargue instantáneamente.
threading.Thread(target=load_data, daemon=True).start()

# ── Header ───────────────────────────────────────────────────────────
st.title("Inicio")
st.markdown("### Dashboard de Importaciones del Ecuador")
st.caption(
    "Datos mensuales: Enero 2000 – Diciembre 2025 | "
    "Valores CIF en millones de USD | "
    "Fuente: Banco Central del Ecuador (BCE)"
)

st.divider()

st.markdown("""
Este dashboard interactivo permite explorar y analizar las **importaciones del Ecuador**
durante el periodo **2000–2025**. La herramienta ofrece visualizaciones dinámicas para entender
la estructura, evolución y composición del comercio exterior ecuatoriano a nivel de
grupo CUODE, subgrupo, país de origen y subpartida arancelaria.

Los datos provienen del **Banco Central del Ecuador (BCE)** y abarcan más de **6 millones de registros**
con detalle mensual de valores CIF, volúmenes en toneladas métricas y clasificación arancelaria.
""")

st.info(
    "¿Te interesa el otro lado de la balanza comercial? Explora también el "
    "**[Dashboard de Exportaciones del Ecuador](https://jp1309-exportaciones.streamlit.app/)** — "
    "productos FOB, precios implícitos y drilldown por subpartida.",
    icon="🔗"
)

st.divider()

# ── Módulos de visualización ──────────────────────────────────────────
st.subheader("Módulos de visualización")
st.markdown("Navega a cada módulo desde el menú lateral izquierdo.")

col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    <div class="module-card">
        <h4>📈 1. Suma Móvil 12M</h4>
        <p><b>Objetivo:</b> Analizar la tendencia de largo plazo de las importaciones
        eliminando la estacionalidad mediante el cálculo de la suma móvil de 12 meses.
        Permite comparar la evolución por grupo CUODE, subgrupo y país de origen.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div class="module-card">
        <h4>💲 3. Precio Implícito CIF/TM</h4>
        <p><b>Objetivo:</b> Calcular y monitorear el precio implícito de importación
        (CIF/TM) con promedio móvil de 12 meses. Incluye detección de outliers,
        bandas de confianza y comparativa por origen.</p>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="module-card">
        <h4>🌳 2. Treemap CUODE</h4>
        <p><b>Objetivo:</b> Visualizar la estructura jerárquica de las importaciones
        (Grupo → Subgrupo) mediante treemaps y sunbursts interactivos.
        Permite identificar la composición por CUODE y su evolución temporal.</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div class="module-card">
        <h4>🔍 4. Drilldown Subpartida</h4>
        <p><b>Objetivo:</b> Explorar el detalle granular a nivel de subpartida arancelaria
        para cada subgrupo. Incluye evolución temporal, composición y análisis
        por país de origen.</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ── KPIs ─────────────────────────────────────────────────────────────
total_cif   = dff["CIF"].sum()
total_tm    = dff["TM"].sum()
n_paises    = dff["Pais_Origen"].nunique()
n_subgrupos = dff["Subgrupo"].nunique()

max_anio = int(dff["Anio"].max())
cif_max  = dff[dff["Anio"] == max_anio]["CIF"].sum()
cif_prev = dff[dff["Anio"] == max_anio - 1]["CIF"].sum()
var_anio  = (cif_max - cif_prev) / cif_prev * 100 if cif_prev else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Importado (CIF)", f"${total_cif:,.1f} M")
k2.metric("Volumen Total (TM)", f"{total_tm:,.0f}")
k3.metric(f"CIF {max_anio} (millones USD)", f"${cif_max:,.0f} M",
          delta=f"{var_anio:+.1f}% vs {max_anio-1}")
k4.metric("Países de Origen", f"{n_paises}")
k5.metric("Subgrupos CUODE", f"{n_subgrupos}")

st.divider()

# ── Gráfico 1: Serie anual CIF + variación % ─────────────────────────
st.subheader("Importaciones anuales CIF")

anual = dff.groupby("Anio").agg(CIF=("CIF", "sum"), TM=("TM", "sum")).reset_index()
anual["Var_pct"] = anual["CIF"].pct_change() * 100
var_min = anual["Var_pct"].min()
var_max = anual["Var_pct"].max()
pad = (var_max - var_min) * 0.1
y2_range = [var_min - pad, var_max + pad]

fig1 = make_subplots(specs=[[{"secondary_y": True}]])
fig1.add_trace(go.Bar(
    x=anual["Anio"], y=anual["CIF"], name="CIF (millones USD)",
    marker_color="#2563eb", opacity=0.85,
    hovertemplate="<b>%{x}</b><br>CIF: $%{y:,.1f} M<extra></extra>"
), secondary_y=False)
fig1.add_trace(go.Scatter(
    x=anual["Anio"], y=anual["Var_pct"], name="Crecimiento %",
    mode="lines+markers",
    line=dict(color="#dc2626", width=2), marker=dict(size=5),
    hovertemplate="<b>%{x}</b><br>Crec: %{y:.1f}%<extra></extra>"
), secondary_y=True)
fig1.update_layout(
    height=380,
    yaxis=dict(title="CIF (millones USD)", tickformat=",.1f"),
    yaxis2=dict(title="Crecimiento (%)", overlaying="y", side="right",
                zeroline=True, zerolinecolor="#555", range=y2_range),
    legend=dict(orientation="h", y=1.08),
    hovermode="x unified",
    margin=dict(t=30, b=30),
    plot_bgcolor="white",
)
fig1.update_xaxes(gridcolor="#f0f0f0")
fig1.update_yaxes(gridcolor="#f0f0f0")
st.plotly_chart(fig1, use_container_width=True)

st.divider()

# ── Gráfico 2–3: Top 10 subgrupos y orígenes ─────────────────────────
st.subheader("Top 10 subgrupos y orígenes")
col_left, col_right = st.columns(2)

# ── Gráfico 2: Top 10 subgrupos CUODE ────────────────────────────────
with col_left:
    top_subgrupos = (
        dff.groupby("Subgrupo")["CIF"].sum()
        .sort_values(ascending=True).tail(10)
        .reset_index()
    )
    colors_sg = [SUBGRUPO_COLORS.get(s, _FALLBACK_COLORS[i % len(_FALLBACK_COLORS)])
                 for i, s in enumerate(top_subgrupos["Subgrupo"])]
    fig2 = go.Figure(go.Bar(
        x=top_subgrupos["CIF"], y=top_subgrupos["Subgrupo"],
        orientation="h", marker_color=colors_sg,
        hovertemplate="<b>%{y}</b><br>CIF: $%{x:,.1f} M<extra></extra>",
    ))
    fig2.update_layout(
        height=450, plot_bgcolor="white",
        xaxis=dict(title="Millones USD (CIF)", tickformat=",.1f", gridcolor="#f0f0f0"),
        margin=dict(l=220, t=10, b=30, r=20),
    )
    fig2.update_xaxes(gridcolor="#f0f0f0")
    st.plotly_chart(fig2, use_container_width=True)

# ── Gráfico 3: Top 10 países de origen ───────────────────────────────
with col_right:
    top_paises = (
        dff.groupby("Pais_Origen")["CIF"].sum()
        .sort_values(ascending=True).tail(10)
        .reset_index()
    )
    colors_p = [get_country_color(str(p), i) for i, p in enumerate(top_paises["Pais_Origen"])]
    fig3 = go.Figure(go.Bar(
        x=top_paises["CIF"], y=top_paises["Pais_Origen"],
        orientation="h", marker_color=colors_p,
        hovertemplate="<b>%{y}</b><br>CIF: $%{x:,.1f} M<extra></extra>",
    ))
    fig3.update_layout(
        height=450, plot_bgcolor="white",
        xaxis=dict(title="Millones USD (CIF)", tickformat=",.1f", gridcolor="#f0f0f0"),
        margin=dict(l=200, t=10, b=30, r=20),
    )
    fig3.update_xaxes(gridcolor="#f0f0f0")
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

col_l2, col_r2 = st.columns(2)

# ── Gráfico 4: Composición por región (pie donut) ─────────────────────
with col_l2:
    st.subheader("Composición por región de origen")
    reg = dff.groupby("Region")["CIF"].sum().sort_values(ascending=False).reset_index()
    fig4 = go.Figure(go.Pie(
        labels=reg["Region"], values=reg["CIF"],
        marker_colors=[REGION_COLORS.get(r, "#b3b3b3") for r in reg["Region"]],
        hole=0.45, textposition="inside", textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>CIF: $%{value:,.1f} M<br>%{percent}<extra></extra>",
    ))
    fig4.update_layout(height=380, margin=dict(t=20, b=20), showlegend=True,
                       legend=dict(orientation="v", font=dict(size=10)))
    st.plotly_chart(fig4, use_container_width=True)

# ── Gráfico 5: Evolución regional (área apilada valores absolutos) ─────
with col_r2:
    st.subheader("Importaciones por región por año")
    reg_anual = dff.groupby(["Anio", "Region"])["CIF"].sum().reset_index()
    regiones_ord = reg_anual.groupby("Region")["CIF"].sum().sort_values(ascending=False).index.tolist()
    fig5 = go.Figure()
    for reg_name in reversed(regiones_ord):
        sub = reg_anual[reg_anual["Region"] == reg_name]
        color = REGION_COLORS.get(reg_name, "#b3b3b3")
        fig5.add_trace(go.Scatter(
            x=sub["Anio"], y=sub["CIF"], name=reg_name,
            mode="lines", stackgroup="one",
            line=dict(width=0.5, color=color), fillcolor=color,
            hovertemplate=f"<b>{reg_name}</b><br>CIF: $%{{y:,.1f}} M<extra></extra>",
        ))
    fig5.update_layout(
        height=380, margin=dict(t=20, b=30), plot_bgcolor="white",
        yaxis=dict(title="CIF (millones USD)", tickformat=",.1f", gridcolor="#f0f0f0"),
        legend=dict(orientation="h", y=-0.2, font=dict(size=10)),
    )
    fig5.update_xaxes(gridcolor="#f0f0f0")
    st.plotly_chart(fig5, use_container_width=True)

st.divider()

# ── Gráfico 6: Participación por subgrupo CUODE (100% stacked area) ───
st.subheader("Participación por subgrupo CUODE (Top 10)")
top_sub_list = (
    dff.groupby("Subgrupo")["CIF"].sum()
    .sort_values(ascending=False).head(10).index.tolist()
)
n_resto = dff["Subgrupo"].nunique() - len(top_sub_list)
resto_label = f"RESTO ({n_resto} subgrupos)"

sub_anual = dff.groupby(["Anio", "Subgrupo"])["CIF"].sum().reset_index()
total_anual2 = sub_anual.groupby("Anio")["CIF"].sum().rename("Total")
sub_anual = sub_anual.merge(total_anual2, on="Anio")
sub_anual["Pct"] = sub_anual["CIF"] / sub_anual["Total"] * 100

area_top = sub_anual[sub_anual["Subgrupo"].isin(top_sub_list)]
resto_cif = sub_anual[sub_anual["Subgrupo"].isin(top_sub_list)].groupby("Anio")["CIF"].sum().rename("CIF_top")
total_s = sub_anual.groupby("Anio")["Total"].first()
resto_df = pd.DataFrame({"CIF_top": resto_cif, "Total": total_s}).reset_index()
resto_df["Pct"] = (resto_df["Total"] - resto_df["CIF_top"]) / resto_df["Total"] * 100
resto_df["Subgrupo"] = resto_label

all_cats = top_sub_list + [resto_label]
area_data = pd.concat([
    area_top[["Anio", "Subgrupo", "Pct"]],
    resto_df[["Anio", "Subgrupo", "Pct"]]
], ignore_index=True)

fig6 = go.Figure()
for i, subg in enumerate(reversed(all_cats)):
    sub = area_data[area_data["Subgrupo"] == subg]
    color = "#d1d5db" if subg == resto_label else SUBGRUPO_COLORS.get(subg, _FALLBACK_COLORS[i % len(_FALLBACK_COLORS)])
    fig6.add_trace(go.Scatter(
        x=sub["Anio"], y=sub["Pct"], name=subg,
        mode="lines", stackgroup="one",
        line=dict(width=0.5, color=color), fillcolor=color,
        hovertemplate=f"<b>{subg}</b><br>%{{y:.1f}}%<extra></extra>",
    ))
fig6.update_layout(
    height=400, plot_bgcolor="white",
    margin=dict(t=30, b=30),
    yaxis=dict(title="Participación (%)", ticksuffix="%", dtick=10,
               range=[0, 100], gridcolor="#f0f0f0"),
    legend=dict(orientation="h", y=-0.25, font=dict(size=10)),
)
fig6.update_xaxes(gridcolor="#f0f0f0")
fig6.update_yaxes(gridcolor="#f0f0f0")
st.plotly_chart(fig6, use_container_width=True)

st.divider()

# ── Gráfico 7: Diversificación (N° subgrupos y N° orígenes) ───────────
st.subheader("Diversificación: N° de subgrupos CUODE y países de origen en el tiempo")

div_data = dff.groupby("Anio").agg(
    N_subgrupos=("Subgrupo", "nunique"),
    N_origenes=("Pais_Origen", "nunique"),
).reset_index()

fig7 = go.Figure()
fig7.add_trace(go.Scatter(
    x=div_data["Anio"], y=div_data["N_subgrupos"],
    name="N° Subgrupos CUODE", mode="lines+markers",
    line=dict(color="#2563eb", width=2),
    hovertemplate="<b>%{x}</b><br>N° Subgrupos: %{y}<extra></extra>",
))
fig7.add_trace(go.Scatter(
    x=div_data["Anio"], y=div_data["N_origenes"],
    name="N° Países de Origen", mode="lines+markers",
    line=dict(color="#f59e0b", width=2),
    yaxis="y2",
    hovertemplate="<b>%{x}</b><br>N° Países: %{y}<extra></extra>",
))
fig7.update_layout(
    height=350, margin=dict(t=10, b=30),
    yaxis=dict(title="N° Subgrupos CUODE", gridcolor="#f0f0f0", dtick=1),
    yaxis2=dict(title="N° Países de Origen", overlaying="y", side="right"),
    legend=dict(orientation="h", y=1.08),
    hovermode="x unified",
    plot_bgcolor="white",
)
fig7.update_xaxes(gridcolor="#f0f0f0")
fig7.update_yaxes(gridcolor="#f0f0f0")
st.plotly_chart(fig7, use_container_width=True)
st.caption(
    "El conteo de países de origen incluye territorios, islas y zonas especiales además de países soberanos "
    "(254 entidades en total en el dataset). El BCE registra ~32 territorios/islas y zonas francas "
    "adicionales a los ~195 países soberanos, lo que explica valores superiores a 200."
)

st.divider()

# ── Fuentes y Footer ──────────────────────────────────────────────────
st.markdown("""
| Fuente | Descripción | Período |
|--------|-------------|---------|
| [Banco Central del Ecuador (BCE)](https://www.bce.fin.ec) | Importaciones por Grupo, Subgrupo CUODE, Subpartida y País Origen | Ene 2000 – Dic 2025 |
""")

st.markdown(
    "<div style='text-align:center;color:#64748b;margin-top:16px'>"
    "Desarrollado por <b>Juan Pablo Erráez</b> · "
    "Dashboard de análisis de importaciones del Ecuador | 2025"
    "</div>",
    unsafe_allow_html=True,
)
