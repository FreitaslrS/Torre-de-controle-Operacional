import streamlit as st
import pandas as pd
from typing import NamedTuple

from core.repository import (
    buscar_datas_coletas, buscar_coletas,
    buscar_datas_coletas_grandes, buscar_coletas_grandes,
    buscar_datas_coleta_final, buscar_coleta_final,
)
from utils.style import aplicar_css_global, tabela_padrao, rodape_autoria, fmt_numero
from utils.theme import grafico_barra
from utils.i18n import t

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
    df_orig = (df.groupby("local_carregamento")
               .agg(pacotes=("pacotes_descarregados", "sum"))
               .reset_index()
               .sort_values("pacotes", ascending=False))
    if df_orig.empty:
        return
    cores = [COR_PRINCIPAL] + [COR_SECUNDARIA] * (len(df_orig) - 1)
    fig = grafico_barra(df_orig, x="local_carregamento", y="pacotes", text="pacotes")
    fig.update_traces(marker_color=cores, hovertemplate="<b>%{x}</b><br>Pacotes desc.: %{y}<extra></extra>")
    st.plotly_chart(fig, use_container_width=True, key="fig_orig_desc")


def _grafico_dif_desc(df):
    df_dif = (df.groupby("local_carregamento")
              .agg(dif=("dif_pacotes", "sum"),
                   pac_c=("pacotes_carregados", "sum"),
                   pac_dc=("pacotes_descarregados", "sum"))
              .reset_index()
              .sort_values("dif"))
    if df_dif.empty:
        return
    cores = [COR_ALERTA if v < 0 else COR_SECUNDARIA for v in df_dif["dif"]]
    fig = grafico_barra(df_dif, x="local_carregamento", y="dif", text="dif")
    fig.update_traces(marker_color=cores, texttemplate="%{text:+,}",
                      hovertemplate="<b>%{x}</b><br>Diferença: %{y:+,}<extra></extra>")
    fig.update_layout(yaxis_title=t("col.lbl_diferenca"))
    st.plotly_chart(fig, use_container_width=True, key="fig_dif_desc")


def _grafico_timeline_desc(df):
    df_time = df[df["tempo_carregamento"].notna()].copy()
    if df_time.empty:
        return
    df_time["hora"] = pd.to_datetime(df_time["tempo_carregamento"]).dt.hour
    df_hora = (df_time.groupby("hora")
               .agg(veiculos=("placa", "nunique"), pacotes=("pacotes_descarregados", "sum"))
               .reset_index())
    fig = grafico_barra(df_hora, x="hora", y="pacotes", text="veiculos")
    fig.update_traces(marker_color=COR_SECUNDARIA, texttemplate="%{text} veíc.",
                      hovertemplate="<b>%{x}h</b><br>Pacotes: %{y}<br>Veículos: %{text}<extra></extra>")
    fig.update_layout(xaxis_title=t("col.hora"), yaxis_title=t("col.lbl_pac_desc"))
    st.plotly_chart(fig, use_container_width=True, key="fig_time_desc")


def _tab_descarregamento(data_sel):
    df = buscar_coletas(data_sel, tipo="descarregamento")

    if df.empty:
        st.warning(t("col.sem_registros_desc"))
        return

    k = _kpis(df)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric(t("col.veiculos"),              k.veiculos)
    col2.metric(t("col.pac_carregados"),    fmt_numero(k.pac_c))
    col3.metric(t("col.pac_descarregados"), fmt_numero(k.pac_dc))
    col4.metric(t("col.dif_pacotes"),     f"+{fmt_numero(k.dif)}" if k.dif >= 0 else f"-{fmt_numero(abs(k.dif))}",
                delta_color="inverse" if k.dif < 0 else "normal")
    col5.metric(t("col.sacos_carregados"),      fmt_numero(k.sacos_c))

    st.divider()
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown(f"**{t('col.pac_por_origem')}**")
        _grafico_origem_desc(df)
    with col_g2:
        st.markdown(f"**{t('col.dif_por_origem')}**")
        _grafico_dif_desc(df)

    st.divider()
    st.markdown(f"**{t('col.timeline_desc')}**")
    _grafico_timeline_desc(df)

    st.divider()
    st.markdown(f"**{t('col.detalhe_veiculo')}**")
    df_tab = df[[
        "placa", "motorista", "estado_origem", "local_carregamento",
        "tempo_carregamento", "ja_descarregado",
        "sacos_carregados", "sacos_descarregados",
        "pacotes_carregados", "pacotes_descarregados", "dif_pacotes"
    ]].copy()
    df_tab["tempo_carregamento"] = pd.to_datetime(df_tab["tempo_carregamento"]).dt.strftime("%d/%m %H:%M")
    df_tab.columns = [
        t("col.placa"), t("col.motorista"), t("col.estado_origem"), t("col.base_origem"),
        t("col.hora_car"), t("col.descarregado"),
        t("col.sacos_car"), t("col.sacos_desc"),
        t("col.pac_car"), t("col.pac_desc"), t("col.dif_pac"),
    ]
    tabela_padrao(df_tab)


def _grafico_destino_saida(df):
    df_dest = (df.groupby("proximo_ponto")
               .agg(pacotes=("pacotes_carregados", "sum"))
               .reset_index()
               .sort_values("pacotes", ascending=False)
               .head(15))
    if df_dest.empty:
        return
    cores = [COR_PRINCIPAL] + [COR_SECUNDARIA] * (len(df_dest) - 1)
    fig = grafico_barra(df_dest, x="proximo_ponto", y="pacotes", text="pacotes")
    fig.update_traces(marker_color=cores, hovertemplate="<b>%{x}</b><br>Pacotes: %{y}<extra></extra>")
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True, key="fig_dest_saida")


def _grafico_dif_saida(df):
    df_conf = df[df["pacotes_descarregados"] > 0].copy()
    if df_conf.empty:
        st.info(t("col.sem_desc_confirmado"))
        return
    df_dif = (df_conf.groupby("proximo_ponto")
              .agg(dif=("dif_pacotes", "sum"))
              .reset_index()
              .sort_values("dif"))
    cores = [COR_ALERTA if v < 0 else COR_SECUNDARIA for v in df_dif["dif"]]
    fig = grafico_barra(df_dif, x="proximo_ponto", y="dif", text="dif")
    fig.update_traces(marker_color=cores, texttemplate="%{text:+,}",
                      hovertemplate="<b>%{x}</b><br>Diferença: %{y:+,}<extra></extra>")
    fig.update_layout(yaxis_title=t("col.lbl_diferenca"))
    st.plotly_chart(fig, use_container_width=True, key="fig_dif_saida")


def _grafico_timeline_saida(df):
    df_time = df[df["tempo_carregamento"].notna()].copy()
    if df_time.empty:
        return
    df_time["hora"] = pd.to_datetime(df_time["tempo_carregamento"]).dt.hour
    df_hora = (df_time.groupby("hora")
               .agg(veiculos=("placa", "nunique"), pacotes=("pacotes_carregados", "sum"))
               .reset_index())
    fig = grafico_barra(df_hora, x="hora", y="pacotes", text="veiculos")
    fig.update_traces(marker_color=COR_PRINCIPAL, texttemplate="%{text} veíc.",
                      hovertemplate="<b>%{x}h</b><br>Pacotes env.: %{y}<extra></extra>")
    fig.update_layout(xaxis_title=t("col.hora"), yaxis_title=t("col.lbl_pac_car"))
    st.plotly_chart(fig, use_container_width=True, key="fig_time_saida")


def _tab_saida(data_sel):
    df = buscar_coletas(data_sel, tipo="saida")

    if df.empty:
        st.warning(t("col.sem_registros_saida"))
        return

    k = _kpis(df)
    total_destinos = df["proximo_ponto"].nunique()

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric(t("col.veiculos"),            k.veiculos)
    col2.metric(t("col.destinos"),            total_destinos)
    col3.metric(t("col.pac_enviados"),    fmt_numero(k.pac_c))
    col4.metric(t("col.sacos_enviados"),      fmt_numero(k.sacos_c))
    col5.metric(t("col.confirmados_desc"), fmt_numero(k.pac_dc),
                delta=f"+{fmt_numero(k.dif)} pendentes" if k.dif >= 0 else f"-{fmt_numero(abs(k.dif))} pendentes",
                delta_color="inverse" if k.dif < 0 else "normal")

    st.divider()
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.markdown(f"**{t('col.vol_por_destino')}**")
        _grafico_destino_saida(df)
    with col_g2:
        st.markdown(f"**{t('col.dif_por_destino')}**")
        _grafico_dif_saida(df)

    st.divider()
    st.markdown(f"**{t('col.timeline_saida')}**")
    _grafico_timeline_saida(df)

    st.divider()
    st.markdown(f"**{t('col.detalhe_veiculo_destino')}**")
    df_tab = df[[
        "placa", "motorista", "proximo_ponto",
        "tempo_carregamento", "ja_descarregado",
        "sacos_carregados", "pacotes_carregados",
        "pacotes_descarregados", "dif_pacotes"
    ]].copy()
    df_tab["tempo_carregamento"] = pd.to_datetime(df_tab["tempo_carregamento"]).dt.strftime("%d/%m %H:%M")
    df_tab.columns = [
        t("col.placa"), t("col.motorista"), t("col.destino"),
        t("col.hora_car"), t("col.confirmado_desc"),
        t("col.sacos_car"), t("col.pac_enviados"),
        t("col.pac_desc"), t("col.dif_pac"),
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
            {t("col.titulo")}
        </h2>
        <p style="margin:0;font-size:12px;color:#6b7280;font-family:'Montserrat',sans-serif;">
            {t("col.subtitulo")}
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

    tab_desc, tab_saida, tab_coleta = st.tabs([
        t("col.tab_desc"),
        t("col.tab_saida"),
        "Coletas",
    ])

    df_datas_desc  = buscar_datas_coletas(tipo="descarregamento")
    df_datas_saida = buscar_datas_coletas(tipo="saida")

    with tab_desc:
        if df_datas_desc.empty:
            st.warning(t("col.sem_dados_desc"))
        else:
            datas = pd.to_datetime(df_datas_desc["data_referencia"]).dt.date.tolist()
            data_sel = st.selectbox(t("comum.data_referencia"), datas, key="data_desc")
            st.divider()
            _tab_descarregamento(data_sel)

    with tab_saida:
        if df_datas_saida.empty:
            st.warning(t("col.sem_dados_saida"))
        else:
            datas_s = pd.to_datetime(df_datas_saida["data_referencia"]).dt.date.tolist()
            data_sel_s = st.selectbox(t("comum.data_referencia"), datas_s, key="data_saida")
            st.divider()
            _tab_saida(data_sel_s)

    with tab_coleta:
        df_datas_grandes = buscar_datas_coletas_grandes()
        df_datas_final   = buscar_datas_coleta_final()

        if df_datas_grandes.empty and df_datas_final.empty:
            st.warning("Sem dados. Importe 'Registro de coleta de itens grandes' e 'Monitoramento de Dados de Coleta Final'.")
        else:
            datas_ref = sorted(
                set(
                    pd.to_datetime(df_datas_grandes["data_referencia"]).dt.date.tolist()
                    + pd.to_datetime(df_datas_final["data_referencia"]).dt.date.tolist()
                ),
                reverse=True
            ) if not df_datas_grandes.empty or not df_datas_final.empty else []
            data_sel_c = st.selectbox("Data de referência", datas_ref, key="data_coleta")
            st.divider()

            # ── MONITORAMENTO FINAL ───────────────────────────────────────────────────────────────────
            df_final = buscar_coleta_final(data_sel_c)
            if not df_final.empty:
                st.markdown("**Resumo Geral de Coletas por Cliente**")

                total_a_coletar  = int(df_final["pac_a_coletar"].sum())
                total_coletados  = int(df_final["pac_coletados"].sum())
                total_nao_col    = int(df_final["pedidos_nao_coletados"].sum())
                total_carregados = int(df_final["pac_carregados"].sum())
                taxa_geral = round(total_coletados / total_a_coletar * 100, 1) if total_a_coletar > 0 else 0

                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric("A Coletar",     fmt_numero(total_a_coletar))
                col2.metric("Coletados",     fmt_numero(total_coletados))
                col3.metric("Taxa Coleta",   f"{taxa_geral}%")
                col4.metric("Não Coletados", fmt_numero(total_nao_col))
                col5.metric("Carregados",    fmt_numero(total_carregados))

                st.divider()

                df_chart = df_final[df_final["pac_coletados"] > 0].nlargest(15, "pac_coletados")
                if not df_chart.empty:
                    cores = [COR_PRINCIPAL] + [COR_SECUNDARIA] * (len(df_chart) - 1)
                    fig = grafico_barra(df_chart, x="cliente", y="pac_coletados", text="pac_coletados")
                    fig.update_traces(marker_color=cores)
                    fig.update_layout(xaxis_tickangle=-45, xaxis_title="Cliente", yaxis_title="Pacotes Coletados")
                    st.markdown("**Pacotes Coletados por Cliente (Top 15)**")
                    st.plotly_chart(fig, use_container_width=True, key="fig_col_cliente")

                st.markdown("**Detalhe por Cliente**")
                df_tab_final = df_final.copy()
                df_tab_final["taxa_coleta"] = df_tab_final["taxa_coleta"].apply(
                    lambda x: f"{x:.1f}%" if pd.notna(x) else "-"
                )
                df_tab_final.columns = [
                    "Data", "Cliente", "A Coletar", "Coletados", "Taxa",
                    "Dif. Coleta", "Não Coletados", "Falta Bipagem Col.",
                    "Perda Coleta", "Carregados", "Dif. Carga",
                    "Falta Bipagem Carga", "Perda Carga"
                ]
                tabela_padrao(df_tab_final)

            st.divider()

            # ── ITENS GRANDES ────────────────────────────────────────────────────────────────────────────
            df_grandes = buscar_coletas_grandes(data_sel_c)
            if not df_grandes.empty:
                st.markdown("**Coleta de Itens Grandes**")

                col1, col2, col3 = st.columns(3)
                col1.metric("Total Waybills", fmt_numero(len(df_grandes)))
                col2.metric("Clientes",       df_grandes["cliente"].nunique())
                col3.metric("Coletadores",    df_grandes["coletador"].nunique())

                df_cli = (
                    df_grandes.groupby("cliente")
                    .size().reset_index(name="qtd")
                    .sort_values("qtd", ascending=False)
                )
                if not df_cli.empty:
                    cores = [COR_PRINCIPAL] + [COR_SECUNDARIA] * (len(df_cli) - 1)
                    fig2 = grafico_barra(df_cli, x="cliente", y="qtd", text="qtd")
                    fig2.update_traces(marker_color=cores)
                    fig2.update_layout(xaxis_title="Cliente", yaxis_title="Qtd. Waybills")
                    st.markdown("**Waybills por Cliente**")
                    st.plotly_chart(fig2, use_container_width=True, key="fig_grandes_cliente")

                st.markdown("**Detalhe por Waybill**")
                df_tab_g = df_grandes.copy()
                df_tab_g["tempo_coleta"] = pd.to_datetime(df_tab_g["tempo_coleta"]).dt.strftime("%d/%m %H:%M")
                df_tab_g.columns = [
                    "Hora Coleta", "Cliente", "Waybill Anjun", "Waybill Escaneado",
                    "Coletador", "Estado", "Placa", "Motorista"
                ]
                tabela_padrao(df_tab_g)

    rodape_autoria()
