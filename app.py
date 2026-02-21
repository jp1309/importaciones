"""
Dashboard de Importaciones del Ecuador (2000–2025)
Fuente: Banco Central del Ecuador
Autor: Juan Pablo Erráez
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from data_loader import (
    load_data_aggregated, filtros_sidebar,
    GRUPO_COLORS, GRUPO_MAP, _FALLBACK_COLORS
)

st.set_page_config(
    page_title="Importaciones Ecuador",
    page_icon="📦",
    layout="wide",
)

# ── Datos y filtros ──────────────────────────────────────────────────
df = load_data_aggregated()
dff, rango, grupos_sel, paises = filtros_sidebar(df, key_prefix="inicio")

st.title("Importaciones del Ecuador")
st.caption(f"Período seleccionado: {rango[0]} – {rango[1]} | Valores en millones USD (CIF)")

# ── KPIs ─────────────────────────────────────────────────────────────
total_cif    = dff["CIF"].sum()
total_tm     = dff["TM"].sum()
n_paises     = dff["Pais_Origen"].nunique()
n_subgrupos  = dff["Subgrupo"].nunique()

k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Importado (CIF)", f"${total_cif:,.0f} M")
k2.metric("Peso Total", f"{total_tm:,.0f} TM")
k3.metric("Países de Origen", f"{n_paises}")
k4.metric("Subgrupos CUODE", f"{n_subgrupos}")

st.divider()

# ── Gráfico 1: Serie anual CIF + variación % ─────────────────────────
st.subheader("Evolución anual de importaciones (CIF)")

anual = dff.groupby("Anio")["CIF"].sum().reset_index()
anual["Var_pct"] = anual["CIF"].pct_change() * 100
anual["Var_pct_clip"] = anual["Var_pct"].clip(-100, 200)

fig1 = go.Figure()
fig1.add_trace(go.Bar(
    x=anual["Anio"], y=anual["CIF"],
    name="CIF (M USD)", marker_color="#2563eb",
    yaxis="y1",
    hovertemplate="<b>%{x}</b><br>CIF: $%{y:,.1f} M<extra></extra>",
))
fig1.add_trace(go.Scatter(
    x=anual["Anio"], y=anual["Var_pct_clip"],
    name="Var. % anual", mode="lines+markers",
    line=dict(color="#dc2626", width=2),
    marker=dict(size=6),
    yaxis="y2",
    customdata=anual["Var_pct"],
    hovertemplate="<b>%{x}</b><br>Var: %{customdata:.1f}%<extra></extra>",
))
fig1.update_layout(
    height=380,
    yaxis=dict(title="Millones USD (CIF)", tickformat=",.1f", side="left"),
    yaxis2=dict(title="Var. % anual", overlaying="y", side="right",
                ticksuffix="%", range=[-100, 200]),
    legend=dict(orientation="h", y=1.08),
    hovermode="x unified",
)
st.plotly_chart(fig1, use_container_width=True)

st.divider()

col_left, col_right = st.columns(2)

# ── Gráfico 2: Top 10 grupos CUODE ───────────────────────────────────
with col_left:
    st.subheader("Top grupos CUODE")
    top_grupos = (
        dff.groupby("Grupo")["CIF"].sum()
        .sort_values(ascending=True).tail(10)
        .reset_index()
    )
    colors_g = [GRUPO_COLORS.get(g, _FALLBACK_COLORS[i % len(_FALLBACK_COLORS)])
                for i, g in enumerate(top_grupos["Grupo"])]
    fig2 = go.Figure(go.Bar(
        x=top_grupos["CIF"], y=top_grupos["Grupo"],
        orientation="h", marker_color=colors_g,
        hovertemplate="<b>%{y}</b><br>CIF: $%{x:,.1f} M<extra></extra>",
    ))
    fig2.update_layout(height=380, xaxis=dict(title="Millones USD (CIF)", tickformat=",.1f"))
    st.plotly_chart(fig2, use_container_width=True)

# ── Gráfico 3: Top 10 países de origen ───────────────────────────────
with col_right:
    st.subheader("Top países de origen")
    top_paises = (
        dff.groupby("Pais_Origen")["CIF"].sum()
        .sort_values(ascending=True).tail(10)
        .reset_index()
    )
    fig3 = go.Figure(go.Bar(
        x=top_paises["CIF"], y=top_paises["Pais_Origen"],
        orientation="h", marker_color="#1e3a8a",
        hovertemplate="<b>%{y}</b><br>CIF: $%{x:,.1f} M<extra></extra>",
    ))
    fig3.update_layout(height=380, xaxis=dict(title="Millones USD (CIF)", tickformat=",.1f"))
    st.plotly_chart(fig3, use_container_width=True)

st.divider()

col_l2, col_r2 = st.columns(2)

# ── Gráfico 4: Composición por región (pie) ───────────────────────────
with col_l2:
    st.subheader("Composición por región de origen")
    REGION_COLORS = {
        "América Latina":    "#16a34a", "América del Norte": "#1e3a8a",
        "Europa":            "#2563eb", "Asia":              "#dc2626",
        "Medio Oriente":     "#ca8a04", "África":            "#ea580c",
        "Oceanía":           "#0891b2", "Otros":             "#9ca3af",
    }
    reg = dff.groupby("Region")["CIF"].sum().reset_index().sort_values("CIF", ascending=False)
    fig4 = go.Figure(go.Pie(
        labels=reg["Region"], values=reg["CIF"],
        marker_colors=[REGION_COLORS.get(r, "#d1d5db") for r in reg["Region"]],
        hole=0.35,
        hovertemplate="<b>%{label}</b><br>CIF: $%{value:,.1f} M<br>%{percent}<extra></extra>",
    ))
    fig4.update_layout(height=380, showlegend=True,
                       legend=dict(orientation="h", y=-0.15))
    st.plotly_chart(fig4, use_container_width=True)

# ── Gráfico 5: Evolución regional (area 100%) ─────────────────────────
with col_r2:
    st.subheader("Participación regional por año")
    reg_anual = dff.groupby(["Anio", "Region"])["CIF"].sum().reset_index()
    total_anual = reg_anual.groupby("Anio")["CIF"].sum().rename("Total")
    reg_anual = reg_anual.merge(total_anual, on="Anio")
    reg_anual["Pct"] = reg_anual["CIF"] / reg_anual["Total"] * 100
    regiones_ord = (reg_anual.groupby("Region")["CIF"].sum()
                    .sort_values(ascending=False).index.tolist())
    fig5 = go.Figure()
    for reg_name in reversed(regiones_ord):
        sub = reg_anual[reg_anual["Region"] == reg_name]
        color = REGION_COLORS.get(reg_name, "#d1d5db")
        fig5.add_trace(go.Scatter(
            x=sub["Anio"], y=sub["Pct"], name=reg_name,
            mode="lines", stackgroup="one",
            line=dict(width=0.5, color=color), fillcolor=color,
            hovertemplate=f"<b>{reg_name}</b><br>%{{y:.1f}}%<extra></extra>",
        ))
    fig5.update_layout(
        height=380,
        yaxis=dict(title="Participación (%)", ticksuffix="%", dtick=10, range=[0, 100]),
        legend=dict(orientation="h", y=-0.25),
    )
    st.plotly_chart(fig5, use_container_width=True)

st.divider()

# ── Gráfico 6: Participación por grupo CUODE (100% stacked area) ──────
st.subheader("Participación por grupo CUODE")
top_grupos_list = (
    dff.groupby("Grupo")["CIF"].sum()
    .sort_values(ascending=False).head(8).index.tolist()
)
n_resto = dff["Grupo"].nunique() - len(top_grupos_list)
resto_label = f"RESTO ({n_resto} grupos)"

grupo_anual = dff.groupby(["Anio", "Grupo"])["CIF"].sum().reset_index()
total_anual2 = grupo_anual.groupby("Anio")["CIF"].sum().rename("Total")
grupo_anual = grupo_anual.merge(total_anual2, on="Anio")
grupo_anual["Pct"] = grupo_anual["CIF"] / grupo_anual["Total"] * 100

area_top = grupo_anual[grupo_anual["Grupo"].isin(top_grupos_list)]
resto = (grupo_anual.groupby("Anio")
         .apply(lambda x: pd.Series({
             "CIF_top": x.loc[x["Grupo"].isin(top_grupos_list), "CIF"].sum(),
             "Total":   x["Total"].iloc[0]
         })).reset_index())
resto["Pct"] = (resto["Total"] - resto["CIF_top"]) / resto["Total"] * 100
resto["Grupo"] = resto_label

all_cats = top_grupos_list + [resto_label]
area_data = pd.concat([
    area_top[["Anio", "Grupo", "Pct"]],
    resto[["Anio", "Grupo", "Pct"]]
], ignore_index=True)

fig6 = go.Figure()
for i, grupo in enumerate(reversed(all_cats)):
    sub = area_data[area_data["Grupo"] == grupo]
    color = "#d1d5db" if grupo == resto_label else GRUPO_COLORS.get(grupo, _FALLBACK_COLORS[i % len(_FALLBACK_COLORS)])
    fig6.add_trace(go.Scatter(
        x=sub["Anio"], y=sub["Pct"], name=grupo,
        mode="lines", stackgroup="one",
        line=dict(width=0.5, color=color), fillcolor=color,
        hovertemplate=f"<b>{grupo}</b><br>%{{y:.1f}}%<extra></extra>",
    ))
fig6.update_layout(
    height=400,
    yaxis=dict(title="Participación (%)", ticksuffix="%", dtick=10, range=[0, 100]),
    legend=dict(orientation="h", y=-0.25),
)
st.plotly_chart(fig6, use_container_width=True)

st.divider()

# ── Módulos disponibles ───────────────────────────────────────────────
st.subheader("Módulos de análisis")
c1, c2 = st.columns(2)
with c1:
    st.info("**1. Suma Móvil 12M** — Tendencia suavizada por grupo, subgrupo y país")
    st.info("**2. Treemap CUODE** — Composición jerárquica: Grupo → Subgrupo")
with c2:
    st.info("**3. Precio Implícito CIF/TM** — Costo unitario por producto y origen")
    st.info("**4. Drilldown Subpartida** — Detalle a nivel de subpartida arancelaria")

st.divider()
st.caption("Fuente: Banco Central del Ecuador | Elaboración: Juan Pablo Erráez")
