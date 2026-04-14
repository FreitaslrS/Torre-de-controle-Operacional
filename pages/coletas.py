import streamlit as st
import pandas as pd
import plotly.express as px

from core.repository import buscar_datas_coletas, buscar_coletas
from utils.style import aplicar_css_global, tabela_padrao, rodape_autoria, fmt_numero
from utils.theme import grafico_barra

COR_PRINCIPAL  = "#053B31"
COR_SECUNDARIA = "#009640"
COR_ALERTA     = "#DE121C"
COR_AMARELO    = "#F0A202"


def _kpis(df):
    total_veiculos = df["placa"].nunique()
    total_pac_c    = int(df["pacotes_carregados"].sum())
    total_pac_dc   = int(df["pacotes_descarregados"].sum())
    dif_total      = int(df["dif_pacotes"].sum())
    total_sacos_c  = int(df["sacos_carregados"].sum())
    return total_veiculos, total_pac_c, total_pac_dc, dif_total, total_sacos_c


def _tab_descarregamento(data_sel):
    df = buscar_coletas(data_sel, tipo="descarregamento")

    if df.empty:
        st.warning("Sem registros de descarregamento para a data selecionada.")
        return

    veic, pac_c, pac_dc, dif, sacos_c = _kpis(df)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Veículos",              veic)
    col2.metric("Pacotes Carregados",    fmt_numero(pac_c))
    col3.metric("Pacotes Descarregados", fmt_numero(pac_dc))
    col4.metric("Diferença Pacotes",     f"+{fmt_numero(dif)}" if dif >= 0 else f"-{fmt_numero(abs(dif))}",
                delta_color="inverse" if dif < 0 else "normal")
    col5.metric("Sacos Carregados",      fmt_numero(sacos_c))

    st.divider()

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("**Pacotes Recebidos por Rede de Origem**")
        df_orig = (df.groupby("rede_carregador")
                   .agg(pacotes=("pacotes_descarregados", "sum"))
                   .reset_index()
                   .sort_values("pacotes", ascending=False))
        if not df_orig.empty:
            cores = [COR_PRINCIPAL] + [COR_SECUNDARIA] * (len(df_orig) - 1)
            fig_orig = grafico_barra(df_orig, x="rede_carregador", y="pacotes", text="pacotes")
            fig_orig.update_traces(
                marker_color=cores,
                hovertemplate="<b>%{x}</b><br>Pacotes desc.: %{y}<extra></extra>"
            )
            st.plotly_chart(fig_orig, use_container_width=True, key="fig_orig_desc")

    with col_g2:
        st.markdown("**Diferença por Rede de Origem (Carregado vs Descarregado)**")
        df_dif = (df.groupby("rede_carregador")
                  .agg(dif=("dif_pacotes", "sum"),
                       pac_c=("pacotes_carregados", "sum"),
                       pac_dc=("pacotes_descarregados", "sum"))
                  .reset_index()
                  .sort_values("dif"))
        if not df_dif.empty:
            cores_dif = [COR_ALERTA if v < 0 else COR_SECUNDARIA for v in df_dif["dif"]]
            fig_dif = grafico_barra(df_dif, x="rede_carregador", y="dif", text="dif")
            fig_dif.update_traces(
                marker_color=cores_dif,
                texttemplate="%{text:+,}",
                hovertemplate="<b>%{x}</b><br>Diferença: %{y:+,}<extra></extra>"
            )
            fig_dif.update_layout(yaxis_title="Diferença (pacotes)")
            st.plotly_chart(fig_dif, use_container_width=True, key="fig_dif_desc")

    st.divider()

    st.markdown("**Timeline de Descarregamento (por hora)**")
    df_time = df[df["tempo_descarga"].notna()].copy()
    if not df_time.empty:
        df_time["hora"] = pd.to_datetime(df_time["tempo_descarga"]).dt.hour
        df_hora = (df_time.groupby("hora")
                   .agg(veiculos=("placa", "nunique"),
                        pacotes=("pacotes_descarregados", "sum"))
                   .reset_index())
        fig_time = grafico_barra(df_hora, x="hora", y="pacotes", text="veiculos")
        fig_time.update_traces(
            marker_color=COR_SECUNDARIA,
            texttemplate="%{text} veíc.",
            hovertemplate="<b>%{x}h</b><br>Pacotes: %{y}<br>Veículos: %{text}<extra></extra>"
        )
        fig_time.update_layout(xaxis_title="Hora", yaxis_title="Pacotes Descarregados")
        st.plotly_chart(fig_time, use_container_width=True, key="fig_time_desc")

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


def _tab_saida(data_sel):
    df = buscar_coletas(data_sel, tipo="saida")

    if df.empty:
        st.warning("Sem registros de saída para a data selecionada.")
        return

    veic, pac_c, pac_dc, dif, sacos_c = _kpis(df)
    total_destinos = df["secao_destino"].nunique()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Veículos",            veic)
    col2.metric("Destinos",            total_destinos)
    col3.metric("Pacotes Enviados",    fmt_numero(pac_c))
    col4.metric("Sacos Enviados",      fmt_numero(sacos_c))
    col5.metric("Confirmados (Desc.)", fmt_numero(pac_dc),
                delta=f"+{fmt_numero(dif)} pendentes" if dif >= 0 else f"-{fmt_numero(abs(dif))} pendentes",
                delta_color="inverse" if dif < 0 else "normal")

    st.divider()

    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("**Volume Enviado por Destino (Top 15)**")
        df_dest = (df.groupby("secao_destino")
                   .agg(pacotes=("pacotes_carregados", "sum"))
                   .reset_index()
                   .sort_values("pacotes", ascending=False)
                   .head(15))
        if not df_dest.empty:
            cores = [COR_PRINCIPAL] + [COR_SECUNDARIA] * (len(df_dest) - 1)
            fig_dest = grafico_barra(df_dest, x="secao_destino", y="pacotes", text="pacotes")
            fig_dest.update_traces(
                marker_color=cores,
                hovertemplate="<b>%{x}</b><br>Pacotes: %{y}<extra></extra>"
            )
            fig_dest.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_dest, use_container_width=True, key="fig_dest_saida")

    with col_g2:
        st.markdown("**Diferença por Destino (Enviado vs Confirmado)**")
        df_conf = df[df["pacotes_descarregados"] > 0].copy()
        if not df_conf.empty:
            df_dif_dest = (df_conf.groupby("secao_destino")
                           .agg(dif=("dif_pacotes", "sum"))
                           .reset_index()
                           .sort_values("dif"))
            cores_dif = [COR_ALERTA if v < 0 else COR_SECUNDARIA for v in df_dif_dest["dif"]]
            fig_dif = grafico_barra(df_dif_dest, x="secao_destino", y="dif", text="dif")
            fig_dif.update_traces(
                marker_color=cores_dif,
                texttemplate="%{text:+,}",
                hovertemplate="<b>%{x}</b><br>Diferença: %{y:+,}<extra></extra>"
            )
            fig_dif.update_layout(yaxis_title="Diferença (pacotes)")
            st.plotly_chart(fig_dif, use_container_width=True, key="fig_dif_saida")
        else:
            st.info("Nenhum descarregamento confirmado neste período.")

    st.divider()

    st.markdown("**Timeline de Carregamento (por hora)**")
    df_time = df[df["tempo_carga"].notna()].copy()
    if not df_time.empty:
        df_time["hora"] = pd.to_datetime(df_time["tempo_carga"]).dt.hour
        df_hora = (df_time.groupby("hora")
                   .agg(veiculos=("placa", "nunique"),
                        pacotes=("pacotes_carregados", "sum"))
                   .reset_index())
        fig_time = grafico_barra(df_hora, x="hora", y="pacotes", text="veiculos")
        fig_time.update_traces(
            marker_color=COR_PRINCIPAL,
            texttemplate="%{text} veíc.",
            hovertemplate="<b>%{x}h</b><br>Pacotes env.: %{y}<extra></extra>"
        )
        fig_time.update_layout(xaxis_title="Hora", yaxis_title="Pacotes Carregados")
        st.plotly_chart(fig_time, use_container_width=True, key="fig_time_saida")

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
        <h2 style="margin:0;font-size:20px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">
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
