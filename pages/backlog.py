import streamlit as st
import plotly.express as px
import pandas as pd
import io
import json
import os as _os
from core.repository import (
    buscar_backlog_resumo,
    carregar_backlog_atual_completo,
    buscar_sla_por_estado,
)
from utils.theme import grafico_barra, aplicar_layout_padrao
from utils.style import tabela_padrao, rodape_autoria, aplicar_css_global, fmt_numero
from utils.i18n import t

COR_PRINCIPAL  = "#009640"
COR_SECUNDARIA = "#053B31"
COR_APOIO      = "#2B2D42"

_GEOJSON_PATH = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "assets", "brasil_estados.json")

@st.cache_resource
def _carregar_geojson():
    if not _os.path.exists(_GEOJSON_PATH):
        return None
    with open(_GEOJSON_PATH, encoding="utf-8") as f:
        return json.load(f)


def render():
    aplicar_css_global()

    st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:0.5rem;">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
         stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
    </svg>
    <div>
        <h2 style="margin:0;font-size:20px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("backlog.titulo")}</h2>
        <p style="margin:0;font-size:12px;color:#6b7280;font-family:'Montserrat',sans-serif;">{t("backlog.subtitulo")}</p>
    </div>
</div>
""", unsafe_allow_html=True)

    df_resumo = buscar_backlog_resumo()

    if df_resumo.empty:
        st.warning(t("comum.sem_dados"))
        return

    # =========================
    # 📊 KPIs
    # =========================
    total = df_resumo["qtd"].sum()
    b24 = df_resumo["b24"].sum()
    b48 = df_resumo["b48"].sum()
    b72 = df_resumo["b72"].sum()
    perc = (b72 / total * 100) if total else 0
    def cor_kpi(valor, total):
        p = valor / total if total else 0
        return "(!)" if p > 0.3 else "(~)" if p > 0.15 else "(ok)"

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total", fmt_numero(total))
    col2.metric("+24H", fmt_numero(b24))
    col3.metric("+48H", fmt_numero(b48))
    col4.metric("+72H", fmt_numero(b72))
    col5.metric("+96H", fmt_numero(int(df_resumo["b96"].sum())))
    col6.metric(t("backlog.pct_critico"), f"{perc:.1f}%")

    # KPIs por faixa de dias
    _FAIXAS_DIAS = ["1 dia", "1-5 dias", "5-10 dias", "10-20 dias", "20-30 dias", "30+ dias"]
    df_kpi_faixas = carregar_backlog_atual_completo()
    kpi_cols = st.columns(len(_FAIXAS_DIAS))
    for col, fx in zip(kpi_cols, _FAIXAS_DIAS):
        qtd_fx = int(df_kpi_faixas.loc[df_kpi_faixas["faixa_backlog_snapshot"] == fx, "qtd"].sum())
        col.metric(fx, fmt_numero(qtd_fx))

    if perc > 30:
        st.error(t("backlog.critico"))
    elif perc > 15:
        st.warning(t("backlog.atencao"))
    else:
        st.success(t("backlog.controlado"))

    st.divider()

    # =========================
    # 🎛️ FILTROS GLOBAIS
    # =========================
    st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("comum.filtros")}</span>
</div>""", unsafe_allow_html=True)

    col_f1, col_f2 = st.columns(2)
    remover_estados  = col_f1.multiselect(t("comum.remover_estados"),  options=sorted(df_resumo["estado"].unique()))
    remover_clientes = col_f2.multiselect(t("comum.remover_clientes"), options=sorted(df_resumo["cliente"].unique()))

    col_f3, col_f4 = st.columns(2)
    faixa_horas = col_f3.selectbox(t("comum.filtro_horas"),      [t("comum.todos"), t("comum.ate_24h"), "+24h", "+48h", "+72h", "+96h"], key="bk_faixa_h")
    faixa_dias  = col_f4.selectbox(t("comum.filtro_dias"), [t("comum.todos"), "1 dia", "1-5 dias", "5-10 dias", "10-20 dias", "20-30 dias", "30+ dias"], key="bk_faixa_d")

    # =========================
    # 📊 DADOS — 1 query com cache, filtros em Python
    # =========================
    df_base = carregar_backlog_atual_completo()

    if remover_estados:
        df_base = df_base[~df_base["estado"].isin(remover_estados)]
    if remover_clientes:
        df_base = df_base[~df_base["cliente"].isin(remover_clientes)]

    _faixas_acima = {
        t("comum.ate_24h"): lambda df: df[df["horas_max"] <= 24],
        "+24h":    lambda df: df[df["horas_max"] > 24],
        "+48h":    lambda df: df[df["horas_max"] > 48],
        "+72h":    lambda df: df[df["horas_max"] > 72],
        "+96h":    lambda df: df[df["horas_max"] > 96],
    }
    if faixa_horas in _faixas_acima:
        df_base = _faixas_acima[faixa_horas](df_base)
    if faixa_dias != t("comum.todos"):
        df_base = df_base[df_base["faixa_backlog_snapshot"] == faixa_dias]

    df_estado  = df_base.groupby("estado",  as_index=False)["qtd"].sum()
    df_cliente = df_base.groupby("cliente", as_index=False)["qtd"].sum()
    df_pre     = (df_base.groupby("pre_entrega", as_index=False)["qtd"]
                         .sum().sort_values("qtd", ascending=False).head(10))
    _pp        = df_base["proximo_ponto"].replace("", None).fillna("Sem informação")
    df_proximo = (df_base.assign(proximo_ponto=_pp)
                         .groupby("proximo_ponto", as_index=False)["qtd"].sum())

    # =========================
    # 📊 GRÁFICOS
    # =========================
    df_estado_sorted  = df_estado.sort_values("qtd", ascending=False)
    df_cliente_sorted = df_cliente.sort_values("qtd", ascending=False)

    fig_estado = grafico_barra(df_estado_sorted, x="estado", y="qtd", text="qtd")
    fig_estado.update_traces(
        marker_color=[COR_SECUNDARIA] + [COR_PRINCIPAL] * (len(df_estado_sorted) - 1),
        hovertemplate="<b>%{x}</b><br>Volume: %{y}<extra></extra>"
    )

    fig_cliente = grafico_barra(df_cliente_sorted, x="cliente", y="qtd", text="qtd")
    fig_cliente.update_traces(
        marker_color=[COR_SECUNDARIA] + [COR_PRINCIPAL] * (len(df_cliente_sorted) - 1)
    )

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/><line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("col.estado")}</span>
</div>""", unsafe_allow_html=True)
        st.plotly_chart(fig_estado, use_container_width=True)

    with col_g2:
        st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
<path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("col.cliente")}</span>
</div>""", unsafe_allow_html=True)
        st.plotly_chart(fig_cliente, use_container_width=True)

    st.divider()

    # =========================
    # 🗺️ MAPA GEOGRÁFICO
    # =========================
    st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/>
<path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("backlog.distribuicao_geo")}</span>
</div>""", unsafe_allow_html=True)

    _geojson_brasil = _carregar_geojson()
    if _geojson_brasil:
        fig_mapa = px.choropleth(
            df_estado,
            geojson=_geojson_brasil,
            locations="estado",
            featureidkey="properties.sigla",
            color="qtd",
            color_continuous_scale=[[0, "#e8f5e9"], [0.4, "#009640"], [1, "#053B31"]],
            labels={"qtd": t("backlog.lbl_volume"), "estado": t("col.estado")},
            hover_name="estado",
            hover_data={"qtd": True, "estado": False}
        )
        fig_mapa.update_geos(fitbounds="locations", visible=False)
        fig_mapa.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            paper_bgcolor="rgba(0,0,0,0)",
            coloraxis_colorbar=dict(
                title=t("backlog.lbl_volume"),
                thicknessmode="pixels", thickness=14,
                lenmode="fraction", len=0.6,
                tickfont=dict(family="Montserrat", size=11)
            ),
            height=420
        )
        st.plotly_chart(fig_mapa, use_container_width=True, key="mapa_backlog")
    else:
        st.info(t("backlog.geojson_nao_encontrado"))

    st.divider()

    # =========================
    # 📊 PRÓXIMO PONTO + PRÉ-ENTREGA
    # =========================
    col_pp1, col_pp2 = st.columns(2)

    with col_pp1:
        st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18M15 3v18"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("comum.proximo_ponto")}</span>
</div>""", unsafe_allow_html=True)
        df_proximo_fmt = df_proximo.sort_values("qtd", ascending=False).reset_index(drop=True).copy()
        df_proximo_fmt.columns = [t("col.proximo_ponto"), t("col.qtd")]
        tabela_padrao(df_proximo_fmt)

    with col_pp2:
        st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/>
<path d="M4 22h16"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2z"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("backlog.top10_pre")}</span>
</div>""", unsafe_allow_html=True)
        fig_pre = grafico_barra(df_pre, x="qtd", y="pre_entrega", text="qtd", cor=COR_PRINCIPAL)
        fig_pre.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_pre, use_container_width=True)

    st.divider()

    # ===========================
    # 📊 BACKLOG POR ESTADO (SLA)
    # ===========================
    st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("backlog.por_estado_sla")}</span>
</div>""", unsafe_allow_html=True)
    tabela_padrao(buscar_sla_por_estado())

    st.divider()

    # =========================
    # ⬇️ DOWNLOAD WAYBILLS (via tabela pedidos — mantida linha a linha)
    # =========================
    st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
<polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("backlog.download_waybills")}</span>
</div>""", unsafe_allow_html=True)

    from core.repository import buscar_pedidos
    df_pedidos = buscar_pedidos(limit=200000)
    if not df_pedidos.empty:
        # Aplica os mesmos filtros de estado/cliente selecionados
        if remover_estados:
            df_pedidos = df_pedidos[~df_pedidos["estado"].isin(remover_estados)]
        if remover_clientes:
            df_pedidos = df_pedidos[~df_pedidos["cliente"].isin(remover_clientes)]

        df_export = df_pedidos[[
            "waybill", "estado", "cliente", "cidade",
            "pre_entrega", "horas_backlog_snapshot"
        ]].copy()
        df_export["proximo_ponto"] = df_pedidos["proximo_ponto"] if "proximo_ponto" in df_pedidos.columns else "—"
        df_export["tempo_backlog"] = df_export["horas_backlog_snapshot"].apply(
            lambda h: "—" if pd.isna(h) else (f"{int(h)}h" if h <= 72 else f"{h/24:.1f} dias")
        )
        df_export = df_export.drop(columns=["horas_backlog_snapshot"])
        df_export.columns = [
            t("col.waybill"), t("col.estado"), t("col.cliente"), t("col.cidade"),
            t("col.pre_entrega"), t("col.proximo_ponto"), t("col.tempo_backlog"),
        ]
        df_export = df_export.sort_values(t("col.waybill"))

        buffer = io.BytesIO()
        df_export.to_excel(buffer, index=False)
        st.download_button(
            label=t("backlog.btn_baixar").format(n=fmt_numero(len(df_export))),
            data=buffer.getvalue(),
            file_name="backlog_waybills.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info(t("backlog.sem_waybill"))

    rodape_autoria()
