import streamlit as st
import plotly.graph_objects as go
import io
import pandas as pd

from core.repository import buscar_backlog_historico
from utils.theme import grafico_barra, aplicar_layout_padrao
from utils.style import tabela_padrao, rodape_autoria, aplicar_css_global, fmt_numero

COR_PRINCIPAL  = "#053B31"
COR_SECUNDARIA = "#009640"
COR_APOIO      = "#2B2D42"

FAIXAS_ORDEM = ["1 dia", "1-5 dias", "5-10 dias", "10-20 dias", "20-30 dias", "30+ dias"]


def _soma_acima(df_f, usar_horas, horas):
    if usar_horas:
        return int(df_f.loc[df_f["horas_min"] > horas, "qtd"].sum())
    faixas_map = {
        24:  ["1-5 dias", "5-10 dias", "10-20 dias", "20-30 dias", "30+ dias"],
        48:  ["5-10 dias", "10-20 dias", "20-30 dias", "30+ dias"],
        72:  ["10-20 dias", "20-30 dias", "30+ dias"],
        96:  ["10-20 dias", "20-30 dias", "30+ dias"],
    }
    return int(df_f.loc[df_f["faixa_backlog_snapshot"].isin(faixas_map.get(horas, [])), "qtd"].sum())


def _soma_abaixo24(df_f, usar_horas):
    if usar_horas:
        return int(df_f.loc[df_f["horas_max"] <= 24, "qtd"].sum())
    return int(df_f.loc[df_f["faixa_backlog_snapshot"] == "1 dia", "qtd"].sum())


@st.cache_data(show_spinner=False)
def _df_para_excel(df):
    buf = io.BytesIO()
    df.to_excel(buf, index=False)
    return buf.getvalue()


def gerar_download(df, key_prefix):
    col1, col2 = st.columns(2)
    csv = df.to_csv(index=False).encode("utf-8")
    col1.download_button("CSV", csv, f"{key_prefix}.csv", "text/csv", key=f"{key_prefix}_csv")
    col2.download_button(
        "Excel", _df_para_excel(df), f"{key_prefix}.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"{key_prefix}_excel"
    )


def render():
    aplicar_css_global()

    st.markdown("""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:0.5rem;">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
         stroke="#053B31" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
    </svg>
    <div>
        <h2 style="margin:0;font-size:20px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Backlog Histórico</h2>
        <p style="margin:0;font-size:12px;color:#6b7280;font-family:'Montserrat',sans-serif;">Visão completa histórica da operação</p>
    </div>
</div>
""", unsafe_allow_html=True)

    # =========================
    # 📅 PERÍODO
    # =========================
    col1, col2 = st.columns(2)
    data_inicio = col1.date_input("Data início")
    data_fim    = col2.date_input("Data fim")

    if not data_inicio or not data_fim:
        return

    df = buscar_backlog_historico(data_inicio, data_fim)

    if df.empty:
        st.warning("Sem dados para o período selecionado.")
        return

    st.divider()

    # =========================
    # 🎛️ FILTROS
    # =========================
    st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#053B31" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Filtros</span>
</div>""", unsafe_allow_html=True)

    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    remover_estados  = col_f1.multiselect("Remover Estados",  options=sorted(df["estado"].dropna().unique()),  key="hist_rem_est")
    remover_clientes = col_f2.multiselect("Remover Clientes", options=sorted(df["cliente"].dropna().unique()), key="hist_rem_cli")
    faixa_horas      = col_f3.selectbox("Filtro por Horas",         ["Todos", "Até 24h", "+24h", "+48h", "+72h", "+96h"],                                                          key="hist_faixa_h")
    faixa_dias       = col_f4.selectbox("Filtro por Faixa de Dias", ["Todos", "1 dia", "1-5 dias", "5-10 dias", "10-20 dias", "20-30 dias", "30+ dias"], key="hist_faixa_d")

    df_f = df.copy()
    if remover_estados:
        df_f = df_f[~df_f["estado"].isin(remover_estados)]
    if remover_clientes:
        df_f = df_f[~df_f["cliente"].isin(remover_clientes)]
    LIMITES = {"Até 24h": (None, 24), "+24h": (24, None), "+48h": (48, None), "+72h": (72, None), "+96h": (96, None)}
    if faixa_horas in LIMITES:
        lo, hi = LIMITES[faixa_horas]
        if usar_horas := df_f["horas_min"].notna().any():
            if lo is not None: df_f = df_f[df_f["horas_min"] > lo]
            if hi is not None: df_f = df_f[df_f["horas_max"] <= hi]
        else:
            faixas_fallback = {
                "Até 24h": ["1 dia"],
                "+24h": ["1-5 dias", "5-10 dias", "10-20 dias", "20-30 dias", "30+ dias"],
                "+48h": ["5-10 dias", "10-20 dias", "20-30 dias", "30+ dias"],
                "+72h": ["10-20 dias", "20-30 dias", "30+ dias"],
            }
            df_f = df_f[df_f["faixa_backlog_snapshot"].isin(faixas_fallback[faixa_horas])]
    if faixa_dias != "Todos":
        df_f = df_f[df_f["faixa_backlog_snapshot"] == faixa_dias]

    if df_f.empty:
        st.warning("Sem dados para o filtro selecionado.")
        return

    st.divider()

    # =========================
    # 📊 KPIs
    # =========================
    total_periodo = int(df_f["qtd"].sum())
    usar_horas = df_f["horas_min"].notna().any()

    col1, col2, col3, col4, col5, col6 = st.columns(6)
    col1.metric("Total no Período", fmt_numero(total_periodo))
    col2.metric("<24H",  fmt_numero(_soma_abaixo24(df_f, usar_horas)))
    col3.metric("+24H",  fmt_numero(_soma_acima(df_f, usar_horas, 24)))
    col4.metric("+48H",  fmt_numero(_soma_acima(df_f, usar_horas, 48)))
    col5.metric("+72H",  fmt_numero(_soma_acima(df_f, usar_horas, 72)))
    col6.metric("+96H",  fmt_numero(_soma_acima(df_f, usar_horas, 96)))

    # KPIs por faixa de dias
    _FAIXAS_DIAS = ["1 dia", "1-5 dias", "5-10 dias", "10-20 dias", "20-30 dias", "30+ dias"]
    kpi_cols = st.columns(len(_FAIXAS_DIAS))
    for col, fx in zip(kpi_cols, _FAIXAS_DIAS):
        qtd_fx = int(df_f.loc[df_f["faixa_backlog_snapshot"] == fx, "qtd"].sum())
        col.metric(fx, fmt_numero(qtd_fx))

    st.divider()

    # =========================
    # 📈 EVOLUÇÃO POR DIA
    # =========================
    df_tempo = df_f.groupby("data_referencia")["qtd"].sum().reset_index().sort_values("data_referencia")
    df_tempo["pct_change"] = df_tempo["qtd"].pct_change() * 100
    df_tempo["pct_label"]  = df_tempo["pct_change"].apply(
        lambda x: f"{x:+.1f}%" if pd.notna(x) and x != float("inf") else ""
    )

    fig = go.Figure()
    fig.add_bar(x=df_tempo["data_referencia"], y=df_tempo["qtd"], name="Volume", marker_color=COR_PRINCIPAL)
    fig.add_trace(go.Scatter(
        x=df_tempo["data_referencia"], y=df_tempo["qtd"],
        mode="lines+markers+text", name="Tendência",
        line=dict(color=COR_SECUNDARIA, width=3),
        text=df_tempo["pct_label"], textposition="top center"
    ))
    fig = aplicar_layout_padrao(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # =========================
    # 📊 ESTADO + CLIENTE
    # =========================
    df_estado  = df_f.groupby("estado")["qtd"].sum().reset_index().sort_values("qtd", ascending=False)
    df_cliente = df_f.groupby("cliente")["qtd"].sum().reset_index().sort_values("qtd", ascending=False)

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#053B31" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/><line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Estado</span>
</div>""", unsafe_allow_html=True)
        fig_e = grafico_barra(df_estado, x="estado", y="qtd", text="qtd")
        fig_e.update_traces(marker_color=[COR_PRINCIPAL] + [COR_SECUNDARIA] * (len(df_estado) - 1))
        st.plotly_chart(fig_e, use_container_width=True)

    with col_g2:
        st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#053B31" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Cliente</span>
</div>""", unsafe_allow_html=True)
        fig_c = grafico_barra(df_cliente, x="cliente", y="qtd", text="qtd")
        fig_c.update_traces(marker_color=[COR_PRINCIPAL] + [COR_SECUNDARIA] * (len(df_cliente) - 1))
        st.plotly_chart(fig_c, use_container_width=True)

    st.divider()

    # =========================
    # 📋 PRÓXIMO PONTO + PRÉ-ENTREGA
    # =========================
    col_pp1, col_pp2 = st.columns(2)

    with col_pp1:
        if "proximo_ponto" in df_f.columns:
            st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#053B31" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18M15 3v18"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Próximo Ponto</span>
</div>""", unsafe_allow_html=True)
            df_pp = (df_f.groupby("proximo_ponto")["qtd"].sum()
                        .reset_index().sort_values("qtd", ascending=False))
            df_pp.columns = ["Próximo Ponto / 下一站", "Qtd / 数量"]
            tabela_padrao(df_pp)

    with col_pp2:
        if "pre_entrega" in df_f.columns:
            st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#053B31" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/>
<path d="M4 22h16"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2z"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Top 10 Pré-entrega</span>
</div>""", unsafe_allow_html=True)
            df_pre = (df_f.groupby("pre_entrega")["qtd"].sum()
                         .reset_index().sort_values("qtd", ascending=False).head(10))
            fig_pre = grafico_barra(df_pre, x="qtd", y="pre_entrega", text="qtd", cor=COR_SECUNDARIA)
            fig_pre.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_pre, use_container_width=True)

    st.divider()

    # =========================
    # 📊 BACKLOG POR ESTADO × FAIXA
    # =========================
    st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#053B31" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Backlog por Estado (Faixa de Tempo)</span>
</div>""", unsafe_allow_html=True)

    tabela_estado = (
        df_f.groupby(["estado", "faixa_backlog_snapshot"])["qtd"]
        .sum().unstack(fill_value=0).reset_index()
    )
    for col in FAIXAS_ORDEM:
        if col not in tabela_estado.columns:
            tabela_estado[col] = 0
    cols_faixa = [c for c in FAIXAS_ORDEM if c in tabela_estado.columns]
    tabela_estado["Total"] = tabela_estado[cols_faixa].sum(axis=1)
    tabela_padrao(tabela_estado, use_container_width=True)

    st.divider()

    # =========================
    # ⬇️ DOWNLOAD
    # =========================
    st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#053B31" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
<polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Download</span>
</div>""", unsafe_allow_html=True)
    gerar_download(df_f, "backlog_historico")

    rodape_autoria()
