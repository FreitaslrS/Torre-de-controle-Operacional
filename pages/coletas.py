import streamlit as st
import pandas as pd
import plotly.express as px

from core.database import consultar_operacional
from utils.style import aplicar_css_global, tabela_padrao, rodape_autoria
from utils.theme import grafico_barra

COR_PRINCIPAL  = "#053B31"
COR_SECUNDARIA = "#009640"
COR_ALERTA     = "#DE121C"


@st.cache_data(ttl=300)
def _datas_disponiveis():
    return consultar_operacional("""
        SELECT DISTINCT data_referencia
        FROM coletas
        ORDER BY data_referencia DESC
    """)


@st.cache_data(ttl=300)
def _buscar_coletas(data_ref):
    return consultar_operacional("""
        SELECT *
        FROM coletas
        WHERE data_referencia = %s
        ORDER BY tempo_carga
    """, [data_ref])


def render():
    aplicar_css_global()

    st.markdown("""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:0.5rem;">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
         stroke="#053B31" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="1" y="3" width="15" height="13"/>
        <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/>
        <circle cx="5.5" cy="18.5" r="2.5"/>
        <circle cx="18.5" cy="18.5" r="2.5"/>
    </svg>
    <div>
        <h2 style="margin:0;font-size:20px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Coletas e Carregamento</h2>
        <p style="margin:0;font-size:12px;color:#6b7280;font-family:'Montserrat',sans-serif;">Monitoramento de carregamento e descarregamento de veículos</p>
    </div>
</div>
""", unsafe_allow_html=True)

    df_datas = _datas_disponiveis()

    if df_datas.empty:
        st.warning("Sem dados. Importe um arquivo de Coletas na página de Importação.")
        rodape_autoria()
        return

    datas = pd.to_datetime(df_datas["data_referencia"]).dt.date.tolist()
    data_sel = st.selectbox("Data de referência", datas)

    df = _buscar_coletas(data_sel)

    if df.empty:
        st.warning("Sem dados para a data selecionada.")
        rodape_autoria()
        return

    # ── KPIs ────────────────────────────────────────────────────────
    total_veiculos    = len(df)
    total_pacotes_c   = int(df["pacotes_carregados"].sum())
    total_pacotes_dc  = int(df["pacotes_descarregados"].sum())
    dif_total         = int(df["dif_pacotes"].sum())
    total_sacos_c     = int(df["sacos_carregados"].sum())

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Veículos", total_veiculos)
    col2.metric("Pacotes Carregados", f"{total_pacotes_c:,}")
    col3.metric("Pacotes Descarregados", f"{total_pacotes_dc:,}")
    col4.metric("Diferença Pacotes", dif_total,
                delta_color="inverse" if dif_total < 0 else "normal")
    col5.metric("Sacos Carregados", f"{total_sacos_c:,}")

    st.divider()

    # ── Gráficos por origem e modo ───────────────────────────────────
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#053B31" stroke-width="2.2">
<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
<path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Pacotes por Rede de Origem</span>
</div>""", unsafe_allow_html=True)
        df_orig = (df.groupby("rede_carregador")
                   .agg(pacotes=("pacotes_carregados", "sum"))
                   .reset_index()
                   .sort_values("pacotes", ascending=False))
        if not df_orig.empty:
            cores = [COR_PRINCIPAL] + [COR_SECUNDARIA] * (len(df_orig) - 1)
            fig_orig = grafico_barra(df_orig, x="rede_carregador", y="pacotes", text="pacotes")
            fig_orig.update_traces(marker_color=cores)
            st.plotly_chart(fig_orig, use_container_width=True, key="fig_orig")

    with col_g2:
        st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#053B31" stroke-width="2.2">
<path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Modo de Operação</span>
</div>""", unsafe_allow_html=True)
        df_modo = (df.groupby("modo_operacao")
                   .agg(pacotes=("pacotes_carregados", "sum"))
                   .reset_index())
        if not df_modo.empty:
            fig_modo = px.pie(
                df_modo, names="modo_operacao", values="pacotes",
                color_discrete_sequence=[COR_PRINCIPAL, COR_SECUNDARIA, "#2B2D42"]
            )
            fig_modo.update_layout(
                margin=dict(t=0, b=0, l=0, r=0),
                paper_bgcolor="rgba(0,0,0,0)", height=300
            )
            st.plotly_chart(fig_modo, use_container_width=True, key="fig_modo")

    st.divider()

    # ── Timeline de chegadas ─────────────────────────────────────────
    st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#053B31" stroke-width="2.2">
<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Timeline de Chegadas</span>
</div>""", unsafe_allow_html=True)
    df_time = df[df["tempo_carga"].notna()].copy()
    if not df_time.empty:
        df_time["hora"] = pd.to_datetime(df_time["tempo_carga"]).dt.hour
        df_hora = (df_time.groupby("hora")
                   .agg(veiculos=("num_registro", "count"),
                        pacotes=("pacotes_carregados", "sum"))
                   .reset_index())
        fig_time = grafico_barra(df_hora, x="hora", y="pacotes", text="veiculos")
        fig_time.update_traces(
            marker_color=COR_SECUNDARIA,
            hovertemplate="<b>%{x}h</b><br>Pacotes: %{y}<br>Veículos: %{text}<extra></extra>"
        )
        fig_time.update_layout(xaxis_title="Hora", yaxis_title="Pacotes")
        st.plotly_chart(fig_time, use_container_width=True, key="fig_time")

    st.divider()

    # ── Tabela detalhada ─────────────────────────────────────────────
    st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#053B31" stroke-width="2.2">
<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18M15 3v18"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Detalhe por Veículo</span>
</div>""", unsafe_allow_html=True)
    df_tabela = df[[
        "placa", "carregador", "rede_carregador", "tempo_carga",
        "sacos_carregados", "pacotes_carregados",
        "sacos_descarregados", "pacotes_descarregados",
        "dif_pacotes", "modo_operacao"
    ]].copy()
    df_tabela["tempo_carga"] = pd.to_datetime(df_tabela["tempo_carga"]).dt.strftime("%d/%m %H:%M")
    df_tabela.columns = [
        "Placa", "Carregador", "Origem", "Chegada",
        "Sacos Car.", "Pacotes Car.",
        "Sacos Desc.", "Pacotes Desc.",
        "Dif. Pacotes", "Modo"
    ]
    tabela_padrao(df_tabela)

    rodape_autoria()
