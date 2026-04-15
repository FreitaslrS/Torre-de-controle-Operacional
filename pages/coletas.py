import streamlit as st
import pandas as pd
from typing import NamedTuple

from core.repository import buscar_datas_coletas, buscar_coletas
from utils.style import aplicar_css_global, tabela_padrao, rodape_autoria, fmt_numero
from utils.theme import grafico_barra

COR_PRINCIPAL  = "#053B31"
COR_SECUNDARIA = "#009640"
COR_ALERTA     = "#DE121C"


class KPIsColeta(NamedTuple):
    veiculos:   int
    pac_c:      int
    pac_dc:     int
    dif:        int
    sacos_c:    int


def _kpis(df) -> KPIsColeta:
    return KPIsColeta(
        veiculos = df["placa"].nunique(),
        pac_c    = int(df["pacotes_carregados"].sum()),
        pac_dc   = int(df["pacotes_descarregados"].sum()),
        dif      = int(df["dif_pacotes"].sum()),
        sacos_c  = int(df["sacos_carregados"].sum()),
    )


def _grafico_origem_desc(df):
    df_orig = (df.groupby("rede_carregador")
               .agg(pacotes=("pacotes_descarregados", "sum"))
               .reset_index()
               .sort_values("pacotes", ascending=False))
    if df_orig.empty:
        return
    cores = [COR_PRINCIPAL] + [COR_SECUNDARIA] * (len(df_orig) - 1)
    fig = grafico_barra(df_orig, x="rede_carregador", y="pacotes", text="pacotes")
    fig.update_traces(marker_color=cores, hovertemplate="<b>%{x}</b><br>Pacotes desc.: %{y}<extra></extra>")
    st.plotly_chart(fig, use_container_width=True, key="fig_orig_desc")


def _grafico_dif_desc(df):
    df_dif = (df.groupby("rede_carregador")
              .agg(dif=("dif_pacotes", "sum"),
                   pac_c=("pacotes_carregados", "sum"),
                   pac_dc=("pacotes_descarregados", "sum"))
              .reset_index()
              .sort_values("dif"))
    if df_dif.empty:
        return
    cores = [COR_ALERTA if v < 0 else COR_SECUNDARIA for v in df_dif["dif"]]
    fig = grafico_barra(df_dif, x="rede_carregador", y="dif", text="dif")
    fig.update_traces(marker_color=cores, texttemplate="%{text:+,}",
                      hovertemplate="<b>%{x}</b><br>Diferença: %{y:+,}<extra></extra>")
    fig.update_layout(yaxis_title="Diferença (pacotes)")
    st.plotly_chart(fig, use_container_width=True, key="fig_dif_desc")


def _grafico_timeline_desc(df):
    df_time = df[df["tempo_descarga"].notna()].copy()
    if df_time.empty:
        return
    df_time["hora"] = pd.to_datetime(df_time["tempo_descarga"]).dt.hour
    df_hora = (df_time.groupby("hora")
               .agg(veiculos=("placa", "nunique"), pacotes=("pacotes_descarregados", "sum"))
               .reset_index())
    fig = grafico_barra(df_hora, x="hora", y="pacotes", text="veiculos")
    fig.update_traces(marker_color=COR_SECUNDARIA, texttemplate="%{text} veíc.",
                      hovertemplate="<b>%{x}h</b><br>Pacotes: %{y}<br>Veículos: %{text}<extra></extra>")
    fig.update_layout(xaxis_title="Hora", yaxis_title="Pacotes Descarregados")
    st.plotly_chart(fig, use_container_width=True, key="fig_time_desc")


def _tab_descarregamento(data_sel):
    df = buscar_coletas(data_sel, tipo="descarregamento")

    if df.empty:
        st.warning("Sem registros de descarregamento para a data selecionada.")
        return

    k = _kpis(df)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Veículos",              k.veiculos)
    col2.metric("Pacotes Carregados",    fmt_numero(k.pac_c))
    col3.metric("Pacotes Descarregados", fmt_numero(k.pac_dc))
    col4.metric("Diferença Pacotes",     f"+{fmt_numero(k.dif)}" if k.dif >= 0 else f"-{fmt_numero(abs(k.dif))}",
                delta_color="inverse" if k.dif < 0 else "normal")
    col5.metric("Sacos Carregados",      fmt_numero(k.sacos_c))

    st.divider()
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("**Pacotes Recebidos por Rede de Origem**")
        _grafico_origem_desc(df)
    with col_g2:
        st.markdown("**Diferença por Rede de Origem (Carregado vs Descarregado)**")
        _grafico_dif_desc(df)

    st.divider()
    st.markdown("**Timeline de Descarregamento (por hora)**")
    _grafico_timeline_desc(df)

    st.divider()
    st.markdown("**Detalhe por Veículo**")
    df_tab = df[[
        "placa", "carregador", "rede_carregador",
        "descarregador", "tempo_descarga",
        "sacos_carregados", "sacos_descarregados",
        "pacotes_carregados", "pacotes_descarregados", "dif_pacotes"
    ]].copy()
    df_tab["tempo_descarga"] = pd.to_datetime(df_tab["tempo_descarga"]).dt.strftime("%d/%m %H:%M")
    df_tab.columns = [
        "Placa", "Carregador Orig.", "Rede Origem",
        "Descarregador", "Hora Desc.",
        "Sacos Car.", "Sacos Desc.",
        "Pac. Car.", "Pac. Desc.", "Dif. Pac."
    ]
    tabela_padrao(df_tab)


def _grafico_destino_saida(df):
    df_dest = (df.groupby("secao_destino")
               .agg(pacotes=("pacotes_carregados", "sum"))
               .reset_index()
               .sort_values("pacotes", ascending=False)
               .head(15))
    if df_dest.empty:
        return
    cores = [COR_PRINCIPAL] + [COR_SECUNDARIA] * (len(df_dest) - 1)
    fig = grafico_barra(df_dest, x="secao_destino", y="pacotes", text="pacotes")
    fig.update_traces(marker_color=cores, hovertemplate="<b>%{x}</b><br>Pacotes: %{y}<extra></extra>")
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True, key="fig_dest_saida")


def _grafico_dif_saida(df):
    df_conf = df[df["pacotes_descarregados"] > 0].copy()
    if df_conf.empty:
        st.info("Nenhum descarregamento confirmado neste período.")
        return
    df_dif = (df_conf.groupby("secao_destino")
              .agg(dif=("dif_pacotes", "sum"))
              .reset_index()
              .sort_values("dif"))
    cores = [COR_ALERTA if v < 0 else COR_SECUNDARIA for v in df_dif["dif"]]
    fig = grafico_barra(df_dif, x="secao_destino", y="dif", text="dif")
    fig.update_traces(marker_color=cores, texttemplate="%{text:+,}",
                      hovertemplate="<b>%{x}</b><br>Diferença: %{y:+,}<extra></extra>")
    fig.update_layout(yaxis_title="Diferença (pacotes)")
    st.plotly_chart(fig, use_container_width=True, key="fig_dif_saida")


def _grafico_timeline_saida(df):
    df_time = df[df["tempo_carga"].notna()].copy()
    if df_time.empty:
        return
    df_time["hora"] = pd.to_datetime(df_time["tempo_carga"]).dt.hour
    df_hora = (df_time.groupby("hora")
               .agg(veiculos=("placa", "nunique"), pacotes=("pacotes_carregados", "sum"))
               .reset_index())
    fig = grafico_barra(df_hora, x="hora", y="pacotes", text="veiculos")
    fig.update_traces(marker_color=COR_PRINCIPAL, texttemplate="%{text} veíc.",
                      hovertemplate="<b>%{x}h</b><br>Pacotes env.: %{y}<extra></extra>")
    fig.update_layout(xaxis_title="Hora", yaxis_title="Pacotes Carregados")
    st.plotly_chart(fig, use_container_width=True, key="fig_time_saida")


def _tab_saida(data_sel):
    df = buscar_coletas(data_sel, tipo="saida")

    if df.empty:
        st.warning("Sem registros de saída para a data selecionada.")
        return

    k = _kpis(df)
    total_destinos = df["secao_destino"].nunique()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Veículos",            k.veiculos)
    col2.metric("Destinos",            total_destinos)
    col3.metric("Pacotes Enviados",    fmt_numero(k.pac_c))
    col4.metric("Sacos Enviados",      fmt_numero(k.sacos_c))
    col5.metric("Confirmados (Desc.)", fmt_numero(k.pac_dc),
                delta=f"+{fmt_numero(k.dif)} pendentes" if k.dif >= 0 else f"-{fmt_numero(abs(k.dif))} pendentes",
                delta_color="inverse" if k.dif < 0 else "normal")

    st.divider()
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown("**Volume Enviado por Destino (Top 15)**")
        _grafico_destino_saida(df)
    with col_g2:
        st.markdown("**Diferença por Destino (Enviado vs Confirmado)**")
        _grafico_dif_saida(df)

    st.divider()
    st.markdown("**Timeline de Carregamento (por hora)**")
    _grafico_timeline_saida(df)

    st.divider()
    st.markdown("**Detalhe por Veículo e Destino**")
    df_tab = df[[
        "placa", "carregador", "secao_destino", "tempo_carga",
        "sacos_carregados", "pacotes_carregados",
        "sacos_descarregados", "pacotes_descarregados", "dif_pacotes"
    ]].copy()
    df_tab["tempo_carga"] = pd.to_datetime(df_tab["tempo_carga"]).dt.strftime("%d/%m %H:%M")
    df_tab.columns = [
        "Placa", "Carregador", "Destino", "Hora Car.",
        "Sacos Car.", "Pac. Car.",
        "Sacos Desc.", "Pac. Desc.", "Dif. Pac."
    ]
    tabela_padrao(df_tab)


def render():
    aplicar_css_global()

    st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:0.5rem;">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
         stroke="{COR_PRINCIPAL}" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="1" y="3" width="15" height="13"/>
        <polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/>
        <circle cx="5.5" cy="18.5" r="2.5"/>
        <circle cx="18.5" cy="18.5" r="2.5"/>
    </svg>
    <div>
        <h2 style="margin:0;font-size:20px;font-weight:700;color:{COR_PRINCIPAL};font-family:'Montserrat',sans-serif;">
            Coletas e Carregamento
        </h2>
        <p style="margin:0;font-size:12px;color:#6b7280;font-family:'Montserrat',sans-serif;">
            Descarregamento em Perus e carregamentos com saída para outras bases
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

    tab_desc, tab_saida = st.tabs([
        "Descarregamento em Perus",
        "Saída para Bases"
    ])

    df_datas_desc  = buscar_datas_coletas(tipo="descarregamento")
    df_datas_saida = buscar_datas_coletas(tipo="saida")

    with tab_desc:
        if df_datas_desc.empty:
            st.warning("Sem dados. Importe um arquivo do tipo 'Coletas — Descarregamento em Perus'.")
        else:
            datas = pd.to_datetime(df_datas_desc["data_referencia"]).dt.date.tolist()
            data_sel = st.selectbox("Data de referência", datas, key="data_desc")
            st.divider()
            _tab_descarregamento(data_sel)

    with tab_saida:
        if df_datas_saida.empty:
            st.warning("Sem dados. Importe um arquivo do tipo 'Coletas — Saída para Bases'.")
        else:
            datas_s = pd.to_datetime(df_datas_saida["data_referencia"]).dt.date.tolist()
            data_sel_s = st.selectbox("Data de referência", datas_s, key="data_saida")
            st.divider()
            _tab_saida(data_sel_s)

    rodape_autoria()
