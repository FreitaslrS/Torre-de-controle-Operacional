import streamlit as st
import pandas as pd
import plotly.express as px

from core.repository import (
    buscar_datas_disponiveis_mon,
    buscar_dev_status_semanal,
    buscar_dev_iatas_semanal,
    buscar_dev_sla_semanal,
    buscar_dev_motivos,
    buscar_dev_interceptados,
    buscar_dev_dsp_sem3tent,
    buscar_clientes_fantasia,
    buscar_p90_por_estado_detalhado,
    buscar_semanas_dev_detalhado,
    buscar_shein_datas,
    buscar_shein_sla,
    buscar_shein_motivos,
    buscar_shein_aging,
    buscar_shein_backlog,
)
from utils.theme import grafico_barra, grafico_pizza, aplicar_layout_padrao
from utils.style import tabela_padrao, aplicar_css_global, rodape_autoria
from utils.semana import semana_para_datas, datas_para_label
from utils.i18n import t

TODOS_ESTADOS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO",
    "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
    "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"
]

# ── Paleta Devoluções ─────────────────────────────────────────────────
COR_PRINCIPAL  = "#2B2D42"   # Navy — cor dominante desta página
COR_SECUNDARIA = "#DE121C"   # Vermelho Anjun — complementar (alerta)
COR_POSITIVO   = "#009640"   # Verde — elementos positivos
COR_APOIO      = "#053B31"   # Verde escuro — terciário
PALETA_PAGINA  = [COR_PRINCIPAL, COR_SECUNDARIA, COR_POSITIVO, COR_APOIO]

# Aliases mantidos para compatibilidade
COR_VERDE = COR_POSITIVO
COR_AZUL  = COR_PRINCIPAL
COR_GELO  = "#e2e8f0"


def _opcoes_semana(df_semanas):
    """Converte DataFrame de semana/ano em lista de strings para selectbox."""
    if df_semanas.empty:
        return []
    return [
        f"{row['semana']}/{int(row['ano'])}"
        for _, row in df_semanas.iterrows()
        if pd.notna(row['semana']) and pd.notna(row['ano'])
    ]


def _parse_semana(opcao):
    """'w15/2025' -> ('w15', 2025). Retorna (None, None) se formato inválido."""
    try:
        partes = opcao.split("/")
        return partes[0], int(partes[1])
    except (ValueError, AttributeError, IndexError):
        return None, None


def _cliente_multiselect(key, clientes_df):
    """
    Exibe multiselect com nomes fantasia.
    Retorna lista de cliente_cod selecionados — [] significa Todos.
    """
    if clientes_df.empty:
        st.caption(f"💡 {t('dev.importar_mon')}")
        return []

    fantasia_opts = sorted(clientes_df["cliente_fantasia"].dropna().unique().tolist())
    selecionados  = st.multiselect(t("comum.cliente"), fantasia_opts, key=key)

    if not selecionados:
        return []

    return clientes_df[clientes_df["cliente_fantasia"].isin(selecionados)]["cliente_cod"].tolist()


def render():
    aplicar_css_global()
    st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:0.5rem;">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
         stroke="#2B2D42" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="1 4 1 10 7 10"/>
        <path d="M3.51 15a9 9 0 1 0 .49-3.13"/>
    </svg>
    <div>
        <h2 style="margin:0;font-size:20px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("dev.titulo")}</h2>
        <p style="margin:0;font-size:12px;color:#6b7280;font-family:'Montserrat',sans-serif;">{t("dev.subtitulo")}</p>
    </div>
</div>
""", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        t("dev.tab_resumo"),
        t("dev.tab_wbr_cliente"),
        t("dev.tab_semanal_interno"),
        t("dev.tab_p90"),
        t("dev.tab_shein"),
    ])

    df_clientes    = buscar_clientes_fantasia()
    df_semanas_all  = buscar_semanas_dev_detalhado()
    df_datas_mon    = buscar_datas_disponiveis_mon()  # chamada única reutilizada nas tabs 2 e 3

    # ════════════════════════════════════════
    # TAB 1 — RESUMO
    # ════════════════════════════════════════
    with tab1:
        df_semanas = df_semanas_all

        if df_semanas.empty:
            st.warning(t("dev.sem_dados_import"))
        else:
            opcoes = _opcoes_semana(df_semanas)
            sel = st.selectbox(t("dev.semana_label"), opcoes, key="semana_resumo")
            semana_sel, ano_sel = _parse_semana(sel)
            if semana_sel is None:
                st.warning(t("comum.sem_dados"))
            else:
                df_res = buscar_dev_status_semanal(semana=semana_sel, ano=ano_sel)

            if semana_sel and df_res.empty:
                st.warning(t("dev.sem_dados_semana"))
            else:
                col1, col2, col3 = st.columns(3)
                col1.metric(t("comum.total"), int(df_res["qtd"].sum()))
                col2.metric(t("dev.col_clientes"), df_res["cliente"].nunique())
                col3.metric(t("dev.col_estados"), df_res["estado"].nunique())

                st.divider()

                df_status_res = df_res.groupby("status")["qtd"].sum().reset_index()
                df_status_res = df_status_res.sort_values("qtd", ascending=False)
                df_status_res.columns = [t("dev.col_status"), t("col.qtd")]
                tabela_padrao(df_status_res)

    # ════════════════════════════════════════
    # TAB 2 — WBR CLIENTE
    # ════════════════════════════════════════
    with tab2:
        st.subheader(t("dev.wbr_relatorio"))

        # ── Filtro de cliente ─────────────────────────────────────
        clientes_wbr = _cliente_multiselect("cliente_wbr", df_clientes)
        cliente_cod_wbr = clientes_wbr if clientes_wbr else None

        # ── SLA (Monitoramento — diário) ──────────────────────────
        st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2B2D42" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("dev.sla_entregas")}</span>
</div>""", unsafe_allow_html=True)
        df_sla = buscar_dev_sla_semanal(cliente=cliente_cod_wbr)

        if not df_sla.empty:
            df_sla["data_referencia"] = pd.to_datetime(df_sla["data_referencia"]).dt.date
            df_sla_dia = df_sla.groupby("data_referencia").agg(
                qtd_total    = ("qtd_total",    "sum"),
                qtd_no_prazo = ("qtd_no_prazo", "sum")
            ).reset_index()
            df_sla_dia["pct_sla"] = (
                df_sla_dia["qtd_no_prazo"] / df_sla_dia["qtd_total"].replace(0, 1) * 100
            ).round(1)

            fig_sla = px.line(
                df_sla_dia.sort_values("data_referencia"),
                x="data_referencia", y="pct_sla",
                markers=True,
                labels={"data_referencia": t("col.data"), "pct_sla": "SLA (%)"},
                color_discrete_sequence=[COR_POSITIVO]
            )
            fig_sla = aplicar_layout_padrao(fig_sla)
            st.plotly_chart(fig_sla, use_container_width=True, key="fig_sla_wbr")
        else:
            st.info(t("dev.sem_dados_mon"))

        st.divider()

        # ── Backlog e Estados (Devolução — semanal) ───────────────
        df_semanas_wbr = df_semanas_all

        if df_semanas_wbr.empty:
            st.info(t("dev.sem_dados_import"))
        else:
            opcoes_wbr = _opcoes_semana(df_semanas_wbr)
            sel_wbr = st.selectbox(t("dev.semana_dev"), opcoes_wbr, key="semana_wbr")
            semana_wbr, ano_wbr = _parse_semana(sel_wbr)
            if semana_wbr is None:
                st.warning(t("comum.sem_dados"))
                semana_wbr, ano_wbr = None, None

            data_ini_wbr, data_fim_wbr = semana_para_datas(semana_wbr, ano_wbr) if semana_wbr else (None, None)
            st.caption(f"Período: **{datas_para_label(data_ini_wbr, data_fim_wbr)}**")

            df_status = buscar_dev_status_semanal(semana=semana_wbr, ano=ano_wbr, cliente=cliente_cod_wbr)

            if not df_status.empty:
                st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2B2D42" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("dev.backlog_status")}</span>
</div>""", unsafe_allow_html=True)
                df_backlog = df_status.groupby("status")["qtd"].sum().reset_index()
                df_backlog = df_backlog.sort_values("qtd", ascending=False)

                col1, col2 = st.columns(2)
                with col1:
                    st.metric(t("dev.total_semana"), int(df_backlog["qtd"].sum()))
                    tabela_padrao(df_backlog.rename(columns={"status": t("dev.col_status"), "qtd": t("col.qtd")}))
                with col2:
                    fig_status = grafico_pizza(df_backlog, names="status", values="qtd")
                    st.plotly_chart(fig_status, use_container_width=True, key="fig_status_wbr")

                st.divider()

                st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2B2D42" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/><line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("dev.por_estado")}</span>
</div>""", unsafe_allow_html=True)
                df_por_estado = df_status.groupby("estado")["qtd"].sum().reset_index()
                df_por_estado = df_por_estado.sort_values("qtd", ascending=False)
                cores_est = [COR_PRINCIPAL] + [COR_SECUNDARIA] * (len(df_por_estado) - 1)
                fig_est = grafico_barra(df_por_estado, x="estado", y="qtd", text="qtd")
                fig_est.update_traces(marker_color=cores_est)
                st.plotly_chart(fig_est, use_container_width=True, key="fig_est_wbr")

        st.divider()

        # ── Motivos (Monitoramento — diário) ─────────────────────
        st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#DE121C" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("dev.motivos_falha")}</span>
</div>""", unsafe_allow_html=True)
        df_datas_mon_wbr = df_datas_mon

        if df_datas_mon_wbr.empty:
            st.info(t("dev.sem_dados_mon"))
        else:
            datas_mon_wbr = pd.to_datetime(df_datas_mon_wbr["data_referencia"]).dt.date.tolist()
            data_mon_wbr = st.selectbox(t("dev.data_mon"), datas_mon_wbr, key="data_mon_wbr")

            df_motivos = buscar_dev_motivos(data_ref=data_mon_wbr, cliente=cliente_cod_wbr)
            if not df_motivos.empty:
                cores = [COR_PRINCIPAL] + [COR_SECUNDARIA] * (len(df_motivos) - 1)
                fig_mot = grafico_barra(df_motivos, x="qtd", y="motivo", text="qtd")
                fig_mot.update_traces(marker_color=cores)
                fig_mot.update_layout(yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig_mot, use_container_width=True, key="fig_mot_wbr")
            else:
                st.info(t("dev.sem_dados_data"))

    # ════════════════════════════════════════
    # TAB 3 — SEMANAL INTERNO
    # ════════════════════════════════════════
    with tab3:
        st.subheader(t("dev.rel_semanal_interno"))

        # ── Filtro de cliente ─────────────────────────────────────
        clientes_int = _cliente_multiselect("cliente_int", df_clientes)
        cliente_cod_int = clientes_int if clientes_int else None

        # ── Seletor Devolução (semanal) ───────────────────────────
        df_semanas_int = df_semanas_all

        if df_semanas_int.empty:
            st.warning(t("dev.sem_dados_import"))
            semana_int = None
            ano_int    = None
            df_st_int  = pd.DataFrame()
        else:
            opcoes_int = _opcoes_semana(df_semanas_int)
            sel_int = st.selectbox(t("dev.semana_dev"), opcoes_int, key="semana_int")
            semana_int, ano_int = _parse_semana(sel_int)
            if semana_int is None:
                semana_int, ano_int = None, None

            data_ini_int, data_fim_int = semana_para_datas(semana_int, ano_int) if semana_int else (None, None)
            st.caption(f"Período: **{datas_para_label(data_ini_int, data_fim_int)}**")

            df_st_int = buscar_dev_status_semanal(semana=semana_int, ano=ano_int, cliente=cliente_cod_int)

        # ── Seletor Monitoramento (diário) ────────────────────────
        df_datas_mon_int = df_datas_mon

        if df_datas_mon_int.empty:
            data_mon_int = None
        else:
            datas_mon_int = pd.to_datetime(df_datas_mon_int["data_referencia"]).dt.date.tolist()
            data_mon_int = st.selectbox(t("dev.data_mon"), datas_mon_int, key="data_mon_int")

        st.divider()

        # ── Pizza — Total processado (Devolução) ──────────────────
        st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2B2D42" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("dev.total_proc")}</span>
</div>""", unsafe_allow_html=True)

        if not df_st_int.empty:
            STATUS_DEVOLVIDOS  = ["Recebido de devolução", "Devolvido e armazenado", "Devolvido pelo Ponto"]
            STATUS_EM_PROCESSO = ["Em processo de devolução", "Expedido no Centro de Distribuição",
                                  "Em rota de entrega", "Recebido no Centro de Distribuição",
                                  "Recebido na base de last mile"]
            STATUS_AGUARDANDO  = ["Aguardando tratativa"]

            total_dev  = int(df_st_int[df_st_int["status"].isin(STATUS_DEVOLVIDOS)]["qtd"].sum())
            total_proc = int(df_st_int[df_st_int["status"].isin(STATUS_EM_PROCESSO)]["qtd"].sum())
            total_agu  = int(df_st_int[df_st_int["status"].isin(STATUS_AGUARDANDO)]["qtd"].sum())
            total_geral = total_dev + total_proc + total_agu

            col1, col2, col3, col4 = st.columns(4)
            col1.metric(t("comum.total"), total_geral)
            col2.metric(t("dev.devolvidos"), total_dev)
            col3.metric(t("dev.retornou_processo"), total_proc)
            col4.metric(t("dev.aguardando"), total_agu)

            df_pizza_int = pd.DataFrame([
                {"categoria": t("dev.devolvidos"),          "qtd": total_dev},
                {"categoria": t("dev.retornou_processo"),   "qtd": total_proc},
                {"categoria": t("dev.aguardando"),          "qtd": total_agu},
            ])
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                fig_pizza_int = grafico_pizza(df_pizza_int, names="categoria", values="qtd")
                st.plotly_chart(fig_pizza_int, use_container_width=True, key="fig_pizza_int")
            with col_p2:
                tabela_padrao(df_pizza_int.rename(columns={"categoria": t("dev.categoria"), "qtd": t("col.qtd")}))
        else:
            st.info(t("dev.sem_dados_import"))

        st.divider()

        # ── Motivos (Monitoramento — diário) ─────────────────────
        st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#DE121C" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
<line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("dev.principais_motivos")}</span>
</div>""", unsafe_allow_html=True)
        if data_mon_int:
            df_mot_int = buscar_dev_motivos(data_ref=data_mon_int, cliente=cliente_cod_int)
            if not df_mot_int.empty:
                cores_mot = [COR_PRINCIPAL] + [COR_SECUNDARIA] * (len(df_mot_int) - 1)
                fig_mot_int = grafico_barra(df_mot_int, x="qtd", y="motivo", text="qtd")
                fig_mot_int.update_traces(marker_color=cores_mot)
                fig_mot_int.update_layout(yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig_mot_int, use_container_width=True, key="fig_mot_int")
            else:
                st.info(t("dev.sem_dados_data"))
        else:
            st.info(t("dev.sem_dados_mon"))

        st.divider()

        # ── Interceptados (Monitoramento — diário) ────────────────
        st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#DE121C" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
<line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("dev.interceptados_iata")}</span>
</div>""", unsafe_allow_html=True)
        if data_mon_int:
            df_inter = buscar_dev_interceptados(data_ref=data_mon_int, cliente=cliente_cod_int)
            if not df_inter.empty:
                tabela_padrao(df_inter.rename(columns={
                    "ponto_entrada": t("dev.iata"),
                    "estado": t("col.estado"),
                    "qtd": t("col.qtd"),
                }))
            else:
                st.info(t("dev.sem_dados_data"))
        else:
            st.info(t("dev.sem_dados_mon"))

        st.divider()

        # ── Principais Estados (Devolução — semanal) ──────────────
        st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2B2D42" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/><line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("dev.principais_estados")}</span>
</div>""", unsafe_allow_html=True)
        if not df_st_int.empty:
            df_est_int = df_st_int.groupby("estado")["qtd"].sum().reset_index()
            df_est_int = df_est_int.sort_values("qtd", ascending=False)
            tabela_padrao(df_est_int.rename(columns={"estado": t("col.estado"), "qtd": t("col.qtd")}))

        st.divider()

        # ── Top 5 Pré-entregas por Estado (DINÂMICO) ─────────────
        st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2B2D42" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("dev.top5_pre_estado")}</span>
</div>""", unsafe_allow_html=True)
        st.caption("Estados e pré-entregas calculados a partir do monitoramento de pontualidade")

        df_iatas_todos = buscar_dev_iatas_semanal(semana=semana_int, ano=ano_int)

        if df_iatas_todos.empty:
            st.info(t("dev.sem_dados_semana"))
        else:
            top_estados_semana = (
                df_iatas_todos.groupby("estado")["qtd"]
                .sum()
                .sort_values(ascending=False)
                .head(4)
                .index.tolist()
            )

            cols_iata = st.columns(2)
            for idx, estado_sel in enumerate(top_estados_semana):
                df_iata_est = df_iatas_todos[
                    df_iatas_todos["estado"] == estado_sel
                ].sort_values("qtd", ascending=False).head(5)

                with cols_iata[idx % 2]:
                    total_est = int(df_iata_est["qtd"].sum())
                    st.markdown(f"**{estado_sel}** — {total_est:,} devoluções")
                    if not df_iata_est.empty:
                        cores_i = [COR_PRINCIPAL] + [COR_SECUNDARIA] * (len(df_iata_est) - 1)
                        fig_i = grafico_barra(
                            df_iata_est, x="qtd", y="ponto_operacao", text="qtd"
                        )
                        fig_i.update_traces(marker_color=cores_i)
                        fig_i.update_layout(
                            yaxis=dict(autorange="reversed"),
                            height=260,
                            margin=dict(l=0, r=0, t=20, b=0)
                        )
                        st.plotly_chart(fig_i, use_container_width=True, key=f"fig_iata_{estado_sel}")

        st.divider()

        # ── DSPs sem 3 tentativas (Monitoramento — diário) ────────
        st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#DE121C" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
<line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("dev.dsps_sem3tent")}</span>
</div>""", unsafe_allow_html=True)
        if data_mon_int:
            df_dsp = buscar_dev_dsp_sem3tent(data_ref=data_mon_int, cliente=cliente_cod_int)
            if not df_dsp.empty:
                col1, col2 = st.columns(2)
                with col1:
                    df_top_dsp = df_dsp.head(20)
                    cores_dsp = [COR_PRINCIPAL] + [COR_SECUNDARIA] * (len(df_top_dsp) - 1)
                    fig_dsp = grafico_barra(df_top_dsp, x="qtd", y="ponto_entrada", text="qtd")
                    fig_dsp.update_traces(marker_color=cores_dsp)
                    fig_dsp.update_layout(yaxis=dict(autorange="reversed"))
                    st.plotly_chart(fig_dsp, use_container_width=True, key="fig_dsp_int")
                with col2:
                    tabela_padrao(df_dsp.rename(columns={
                        "ponto_entrada": t("dev.iata"),
                        "estado": t("col.estado"),
                        "qtd": t("col.qtd"),
                    }))
            else:
                st.info(t("dev.sem_dados_data"))
        else:
            st.info(t("dev.sem_dados_mon"))

    # ════════════════════════════════════════
    # TAB 4 — P90 POR ESTADO DETALHADO
    # ════════════════════════════════════════
    with tab4:
        st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2B2D42" stroke-width="2.2">
<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/>
<path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("dev.p90_real")}</span>
</div>""", unsafe_allow_html=True)
        st.caption("Calculado com cruzamento Folha de Devolução + Monitoramento. Estado = destino real do pedido.")

        df_sem_det = df_semanas_all

        if df_sem_det.empty:
            st.warning(t("dev.sem_dados_import"))
        else:
            col_f1, col_f2 = st.columns(2)
            opcoes_det = [
                f"{r['semana']}/{int(r['ano'])}"
                for _, r in df_sem_det.iterrows()
                if pd.notna(r['semana']) and pd.notna(r['ano'])
            ]
            sel_det    = col_f1.selectbox(t("dev.semana_label"), opcoes_det, key="sem_det")
            sem_det, ano_det = _parse_semana(sel_det)
            if sem_det is None:
                st.warning(t("comum.sem_dados"))
                return

            clientes_det = _cliente_multiselect("cliente_det", df_clientes)

            df_det = buscar_p90_por_estado_detalhado(
                semana=sem_det, ano=ano_det,
                clientes=clientes_det if clientes_det else None
            )

            if df_det.empty:
                st.warning(t("dev.sem_dados_periodo"))
            else:
                df_por_estado = (
                    df_det.groupby("estado")
                    .agg(
                        p50_dias    = ("p50_dias", "mean"),
                        p80_dias    = ("p80_dias", "mean"),
                        p90_dias    = ("p90_dias", "mean"),
                        qtd_pedidos = ("qtd_pedidos", "sum"),
                    )
                    .reset_index()
                )
                for col in ["p50_dias", "p80_dias", "p90_dias"]:
                    df_por_estado[col] = df_por_estado[col].round(1)

                total_ped         = int(df_por_estado["qtd_pedidos"].sum())
                estados_com_dados = df_por_estado["estado"].nunique()
                p50_medio = round(float(df_por_estado["p50_dias"].mean()), 1)
                p80_medio = round(float(df_por_estado["p80_dias"].mean()), 1)
                p90_medio = round(float(df_por_estado["p90_dias"].mean()), 1)

                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric(t("dev.total_dev_count"), total_ped)
                col2.metric(t("dev.estados_dados"), estados_com_dados)
                col3.metric(t("dev.p50_medio"), f"{p50_medio} dias")
                col4.metric(t("dev.p80_medio"), f"{p80_medio} dias")
                col5.metric(t("dev.p90_medio"), f"{p90_medio} dias")

                st.divider()

                def _cores_percentil(serie, limites=(30, 60)):
                    cores = []
                    for v in serie:
                        if v > limites[1]:   cores.append(COR_SECUNDARIA)
                        elif v > limites[0]: cores.append(COR_PRINCIPAL)
                        else:                cores.append(COR_POSITIVO)
                    return cores

                df_p50 = df_por_estado.sort_values("p50_dias", ascending=False)
                df_p80 = df_por_estado.sort_values("p80_dias", ascending=False)
                df_p90 = df_por_estado.sort_values("p90_dias", ascending=False)

                col_c1, col_c2, col_c3 = st.columns(3)

                with col_c1:
                    st.markdown(f"**P50 — {t('dev.col_p50')}**")
                    fig50 = grafico_barra(df_p50, x="estado", y="p50_dias", text="p50_dias")
                    fig50.update_traces(
                        marker_color=_cores_percentil(df_p50["p50_dias"], (15, 30)),
                        hovertemplate="<b>%{x}</b><br>P50: %{y} dias<extra></extra>"
                    )
                    fig50.update_layout(yaxis_title="dias", showlegend=False)
                    st.plotly_chart(fig50, use_container_width=True, key="fig_p50_det")

                with col_c2:
                    st.markdown(f"**P80 — {t('dev.col_p80')}**")
                    fig80 = grafico_barra(df_p80, x="estado", y="p80_dias", text="p80_dias")
                    fig80.update_traces(
                        marker_color=_cores_percentil(df_p80["p80_dias"], (20, 45)),
                        hovertemplate="<b>%{x}</b><br>P80: %{y} dias<extra></extra>"
                    )
                    fig80.update_layout(yaxis_title="dias", showlegend=False)
                    st.plotly_chart(fig80, use_container_width=True, key="fig_p80_det")

                with col_c3:
                    st.markdown(f"**P90 — {t('dev.col_p90')}**")
                    fig90 = grafico_barra(df_p90, x="estado", y="p90_dias", text="p90_dias")
                    fig90.update_traces(
                        marker_color=_cores_percentil(df_p90["p90_dias"], (30, 60)),
                        hovertemplate="<b>%{x}</b><br>P90: %{y} dias<extra></extra>"
                    )
                    fig90.update_layout(yaxis_title="dias", showlegend=False)
                    st.plotly_chart(fig90, use_container_width=True, key="fig_p90_det")

                st.divider()

                col_m1, col_m2 = st.columns(2)

                with col_m1:
                    st.markdown(f"**{t('dev.top_motivos')}**")
                    df_mot = (df_det.groupby("motivo")["qtd_pedidos"].sum()
                              .reset_index().sort_values("qtd_pedidos", ascending=False).head(8))
                    if not df_mot.empty:
                        fig_mot = grafico_barra(df_mot, x="qtd_pedidos", y="motivo", text="qtd_pedidos")
                        fig_mot.update_traces(marker_color=COR_SECUNDARIA)
                        fig_mot.update_layout(yaxis=dict(autorange="reversed"))
                        st.plotly_chart(fig_mot, use_container_width=True, key="fig_mot_det")

                with col_m2:
                    st.markdown(f"**{t('dev.top_pre_dev')}**")
                    df_pre = (df_det.groupby("pre_entrega")["qtd_pedidos"].sum()
                              .reset_index().sort_values("qtd_pedidos", ascending=False).head(8))
                    if not df_pre.empty:
                        fig_pre = grafico_barra(df_pre, x="qtd_pedidos", y="pre_entrega", text="qtd_pedidos")
                        fig_pre.update_traces(marker_color=COR_PRINCIPAL)
                        fig_pre.update_layout(yaxis=dict(autorange="reversed"))
                        st.plotly_chart(fig_pre, use_container_width=True, key="fig_pre_det")

                st.divider()
                st.markdown(f"**{t('dev.tabela_detalhada')}**")
                tabela_padrao(df_por_estado.rename(columns={
                    "estado":      t("col.estado"),
                    "p50_dias":    t("dev.col_p50"),
                    "p80_dias":    t("dev.col_p80"),
                    "p90_dias":    t("dev.col_p90"),
                    "qtd_pedidos": t("dev.total_dev_count"),
                }))

    # ════════════════════════════════════════
    # TAB 5 — SHEIN BACKLOG
    # ════════════════════════════════════════
    with tab5:
        st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2B2D42" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Shein — Backlog Completo</span>
</div>""", unsafe_allow_html=True)

        df_shein_datas = buscar_shein_datas()

        if df_shein_datas.empty:
            st.warning(t("dev.shein_sem_dados"))
        else:
            datas_shein = pd.to_datetime(df_shein_datas["data_referencia"]).dt.date.tolist()

            col_f1, col_f2 = st.columns([2, 2])
            with col_f1:
                data_shein = st.selectbox(t("dev.shein_data_ref"), datas_shein, key="data_shein")
            with col_f2:
                segmentos_opts = [t("dev.shein_todos_seg"), "D2D", "Internacional", "Nacional"]
                seg_sel = st.selectbox(t("dev.shein_filtro_seg"), segmentos_opts, key="seg_shein")
            segmento_filtro = None if seg_sel == t("dev.shein_todos_seg") else seg_sel

            # ── KPIs ─────────────────────────────────────────────────
            df_sla_sh = buscar_shein_sla(data_ref=data_shein)

            if not df_sla_sh.empty:
                total_bk   = int(df_sla_sh["qtd_total"].sum())
                total_conc = int(df_sla_sh["qtd_concluido"].sum())
                total_pend = int(df_sla_sh["qtd_pendente"].sum())
                pct_geral  = round(total_conc / total_bk * 100, 1) if total_bk > 0 else 0

                c1, c2, c3, c4 = st.columns(4)
                c1.metric(t("dev.shein_backlog_ativo"), f"{total_bk:,}")
                c2.metric(t("dev.shein_concluido"),     f"{total_conc:,}")
                c3.metric(t("dev.shein_pendente"),      f"{total_pend:,}")
                c4.metric(t("dev.shein_sla_pct"),       f"{pct_geral}%")

                st.divider()

                # ── SLA por segmento ──────────────────────────────────
                st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:0.5rem 0 0.3rem;">
<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
</svg>
<span style="font-size:14px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("dev.shein_sla_pct")} {t("dev.shein_segmento")}</span>
</div>""", unsafe_allow_html=True)

                df_sla_plot = df_sla_sh.copy()
                if segmento_filtro:
                    df_sla_plot = df_sla_plot[df_sla_plot["segmento"] == segmento_filtro]

                col_sla1, col_sla2 = st.columns(2)
                with col_sla1:
                    cores_sla = []
                    for v in df_sla_plot["pct_sla"]:
                        if v >= 90:   cores_sla.append(COR_POSITIVO)
                        elif v >= 70: cores_sla.append(COR_PRINCIPAL)
                        else:         cores_sla.append(COR_SECUNDARIA)
                    fig_sla_sh = grafico_barra(df_sla_plot, x="segmento", y="pct_sla", text="pct_sla")
                    fig_sla_sh.update_traces(marker_color=cores_sla,
                                             hovertemplate="<b>%{x}</b><br>SLA: %{y}%<extra></extra>")
                    fig_sla_sh.update_layout(yaxis_title="SLA (%)", yaxis_range=[0, 105])
                    st.plotly_chart(fig_sla_sh, use_container_width=True, key="fig_sla_shein")
                with col_sla2:
                    tabela_padrao(df_sla_plot.rename(columns={
                        "segmento":      t("dev.shein_segmento"),
                        "qtd_total":     t("comum.total"),
                        "qtd_concluido": t("dev.shein_concluido"),
                        "qtd_pendente":  t("dev.shein_pendente"),
                        "pct_sla":       t("dev.shein_sla_pct"),
                    }))

            st.divider()

            # ── Motivos ───────────────────────────────────────────────
            st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:0.5rem 0 0.3rem;">
<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#DE121C" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
</svg>
<span style="font-size:14px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("dev.shein_motivos")}</span>
</div>""", unsafe_allow_html=True)

            df_mot_sh = buscar_shein_motivos(data_ref=data_shein, segmento=segmento_filtro)

            if not df_mot_sh.empty:
                df_mot_top = df_mot_sh.head(15)
                cores_mot_sh = [COR_PRINCIPAL] + [COR_SECUNDARIA] * (len(df_mot_top) - 1)
                fig_mot_sh = grafico_barra(df_mot_top, x="qtd", y="motivo", text="qtd")
                fig_mot_sh.update_traces(marker_color=cores_mot_sh)
                fig_mot_sh.update_layout(yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig_mot_sh, use_container_width=True, key="fig_mot_shein")
            else:
                st.info(t("dev.sem_dados_data"))

            st.divider()

            # ── Aging ─────────────────────────────────────────────────
            st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:0.5rem 0 0.3rem;">
<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2B2D42" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
</svg>
<span style="font-size:14px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("dev.shein_aging")}</span>
</div>""", unsafe_allow_html=True)

            df_aging_sh = buscar_shein_aging(data_ref=data_shein, segmento=segmento_filtro)

            if not df_aging_sh.empty:
                fig_aging_sh = px.bar(
                    df_aging_sh,
                    x="aging_range", y="qtd", color="segmento",
                    barmode="group",
                    text="qtd",
                    labels={
                        "aging_range": t("dev.shein_col_aging"),
                        "qtd": t("col.qtd"),
                        "segmento": t("dev.shein_segmento"),
                    },
                    color_discrete_sequence=PALETA_PAGINA,
                )
                fig_aging_sh = aplicar_layout_padrao(fig_aging_sh)
                fig_aging_sh.update_traces(textposition="outside")
                st.plotly_chart(fig_aging_sh, use_container_width=True, key="fig_aging_shein")
            else:
                st.info(t("dev.sem_dados_data"))

            st.divider()

            # ── Backlog detalhado (download) ──────────────────────────
            with st.expander("📥 Backlog detalhado (download)"):
                df_bk_sh = buscar_shein_backlog(data_ref=data_shein, segmento=segmento_filtro)
                if df_bk_sh.empty:
                    st.info(t("dev.sem_dados_data"))
                else:
                    st.caption(f"{len(df_bk_sh):,} registros")
                    tabela_padrao(df_bk_sh.rename(columns={
                        "waybill":               "Waybill",
                        "segmento":              t("dev.shein_segmento"),
                        "is_d2d":                "D2D",
                        "aging_day":             "Aging (dias)",
                        "aging_range":           t("dev.shein_col_aging"),
                        "return_initiaded_data": "Início Devolução",
                        "status_folha":          t("dev.shein_col_status"),
                    }))
                    csv = df_bk_sh.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="⬇️ Download CSV",
                        data=csv,
                        file_name=f"shein_backlog_{data_shein}.csv",
                        mime="text/csv",
                        key="dl_shein_backlog",
                    )

    rodape_autoria()
