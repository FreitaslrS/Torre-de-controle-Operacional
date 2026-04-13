import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from core.repository import (
    buscar_p90,
    buscar_semanas_disponiveis_dev,
    buscar_datas_disponiveis_mon,
    buscar_dev_status_semanal,
    buscar_dev_iatas_semanal,
    buscar_dev_sla_semanal,
    buscar_dev_motivos,
    buscar_dev_interceptados,
    buscar_dev_dsp_sem3tent,
    buscar_clientes_fantasia,
)
from utils.theme import grafico_barra, grafico_pizza, aplicar_layout_padrao
from utils.style import tabela_padrao, aplicar_css_global, rodape_autoria

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
    return [f"{row['semana']}/{row['ano']}" for _, row in df_semanas.iterrows()]


def _parse_semana(opcao):
    """'w15/2025' -> ('w15', 2025)"""
    partes = opcao.split("/")
    return partes[0], int(partes[1])


def _cliente_selectbox(key, clientes_df):
    """
    Exibe selectbox com nomes fantasia.
    Retorna (cliente_cod, cliente_fantasia_label) — cod None se 'Todos'.
    """
    if clientes_df.empty:
        st.caption("💡 Importe 'Devolução - Monitoramento' para filtrar por cliente")
        return None, None

    fantasia_opts = ["Todos"] + sorted(
        clientes_df["cliente_fantasia"].dropna().unique().tolist()
    )
    sel = st.selectbox("Cliente / 客户", fantasia_opts, key=key)

    if sel == "Todos":
        return None, None

    cod_match = clientes_df[clientes_df["cliente_fantasia"] == sel]["cliente_cod"].tolist()
    return (cod_match[0] if cod_match else None), sel


def render():
    aplicar_css_global()
    st.markdown("""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:0.5rem;">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
         stroke="#2B2D42" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="1 4 1 10 7 10"/>
        <path d="M3.51 15a9 9 0 1 0 .49-3.13"/>
    </svg>
    <div>
        <h2 style="margin:0;font-size:20px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Devoluções</h2>
        <p style="margin:0;font-size:12px;color:#6b7280;font-family:'Montserrat',sans-serif;">Pedidos devolvidos, P90 e relatórios</p>
    </div>
</div>
""", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Resumo",
        "📊 P90",
        "📊 WBR — Cliente",
        "📊 Semanal — Interno"
    ])

    df_clientes = buscar_clientes_fantasia()

    # ════════════════════════════════════════
    # TAB 1 — RESUMO
    # ════════════════════════════════════════
    with tab1:
        df_semanas = buscar_semanas_disponiveis_dev()

        if df_semanas.empty:
            st.warning("Sem dados. Importe os arquivos 'Devolução'.")
        else:
            opcoes = _opcoes_semana(df_semanas)
            sel = st.selectbox("Semana / 周", opcoes, key="semana_resumo")
            semana_sel, ano_sel = _parse_semana(sel)

            df_res = buscar_dev_status_semanal(semana=semana_sel, ano=ano_sel)

            if df_res.empty:
                st.warning("Sem dados para a semana selecionada.")
            else:
                col1, col2, col3 = st.columns(3)
                col1.metric("Total", int(df_res["qtd"].sum()))
                col2.metric("Clientes", df_res["cliente"].nunique())
                col3.metric("Estados", df_res["estado"].nunique())

                st.divider()

                df_status_res = df_res.groupby("status")["qtd"].sum().reset_index()
                df_status_res = df_status_res.sort_values("qtd", ascending=False)
                df_status_res.columns = ["Status", "Qtd"]
                tabela_padrao(df_status_res)

    # ════════════════════════════════════════
    # TAB 2 — P90
    # ════════════════════════════════════════
    with tab2:
        st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2B2D42" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">P90 — Tempo de Devolução (Percentil 90)</span>
</div>""", unsafe_allow_html=True)
        st.caption("Dias corridos da criação do pedido até recebimento da devolução, para 90% dos casos")

        col_f1, col_f2 = st.columns(2)
        ano_atual = pd.Timestamp.now().year
        ano_p90 = col_f1.selectbox("Ano / 年份", [ano_atual, ano_atual - 1], index=0, key="ano_p90")

        cliente_cod_p90, _ = _cliente_selectbox("cliente_p90", df_clientes)

        df_p90 = buscar_p90(ano=ano_p90, cliente=cliente_cod_p90)

        if df_p90.empty:
            st.warning("Sem dados de P90. Importe um arquivo 'Devolução - P90'.")
        else:
            semanas = sorted(df_p90["semana"].unique())
            pivot = df_p90.pivot_table(
                index="estado", columns="semana", values="p90_dias", aggfunc="mean"
            ).round(1)

            ytd_list = []
            for estado, grupo in df_p90.groupby("estado"):
                todos_dias = grupo["p90_dias"].repeat(grupo["qtd_pedidos"].astype(int))
                ytd_val = round(float(np.percentile(todos_dias, 90)), 1) if len(todos_dias) > 0 else None
                ytd_list.append({"estado": estado, "YTD": ytd_val})

            df_ytd = pd.DataFrame(ytd_list).set_index("estado")
            df_tabela = pd.DataFrame(index=TODOS_ESTADOS)
            df_tabela.index.name = "Estado"
            df_tabela = df_tabela.join(df_ytd).join(pivot).fillna("-").reset_index()

            col1, col2, col3 = st.columns(3)
            col1.metric("📦 Total pedidos", int(df_p90["qtd_pedidos"].sum()))
            col2.metric("🗺️ Estados com dados", df_p90["estado"].nunique())
            col3.metric("📊 P90 Geral (YTD)", f"{round(float(np.percentile(df_p90['p90_dias'].repeat(df_p90['qtd_pedidos'].astype(int)), 90)), 1)} dias")

            st.divider()
            tabela_padrao(df_tabela, altura_linhas=27)

    # ════════════════════════════════════════
    # TAB 3 — WBR CLIENTE
    # ════════════════════════════════════════
    with tab3:
        st.subheader("📊 WBR — Relatório ao Cliente")

        # ── Filtro de cliente ─────────────────────────────────────
        cliente_cod_wbr, _ = _cliente_selectbox("cliente_wbr", df_clientes)

        # ── SLA (Monitoramento — diário) ──────────────────────────
        st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2B2D42" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">SLA — Entregas no Prazo</span>
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
                labels={"data_referencia": "Data", "pct_sla": "SLA (%)"},
                color_discrete_sequence=[COR_POSITIVO]
            )
            fig_sla = aplicar_layout_padrao(fig_sla)
            st.plotly_chart(fig_sla, use_container_width=True, key="fig_sla_wbr")
        else:
            st.info("Sem dados de SLA. Importe 'Devolução - Monitoramento'.")

        st.divider()

        # ── Backlog e Estados (Devolução — semanal) ───────────────
        df_semanas_wbr = buscar_semanas_disponiveis_dev()

        if df_semanas_wbr.empty:
            st.info("Sem dados de status. Importe 'Devolução'.")
        else:
            opcoes_wbr = _opcoes_semana(df_semanas_wbr)
            sel_wbr = st.selectbox("Semana (Devolução) / 周", opcoes_wbr, key="semana_wbr")
            semana_wbr, ano_wbr = _parse_semana(sel_wbr)

            from utils.semana import semana_para_datas, datas_para_label
            data_ini_wbr, data_fim_wbr = semana_para_datas(semana_wbr, ano_wbr)
            st.caption(f"Período: **{datas_para_label(data_ini_wbr, data_fim_wbr)}**")

            df_status = buscar_dev_status_semanal(semana=semana_wbr, ano=ano_wbr, cliente=cliente_cod_wbr)

            if not df_status.empty:
                st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2B2D42" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Backlog — Status Atual</span>
</div>""", unsafe_allow_html=True)
                df_backlog = df_status.groupby("status")["qtd"].sum().reset_index()
                df_backlog = df_backlog.sort_values("qtd", ascending=False)

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total na semana", int(df_backlog["qtd"].sum()))
                    tabela_padrao(df_backlog.rename(columns={"status": "Status", "qtd": "Qtd"}))
                with col2:
                    fig_status = grafico_pizza(df_backlog, names="status", values="qtd")
                    st.plotly_chart(fig_status, use_container_width=True, key="fig_status_wbr")

                st.divider()

                st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2B2D42" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/><line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Devoluções por Estado</span>
</div>""", unsafe_allow_html=True)
                df_por_estado = df_status.groupby("estado")["qtd"].sum().reset_index()
                df_por_estado = df_por_estado.sort_values("qtd", ascending=False)
                cores_est = [COR_PRINCIPAL] + [COR_SECUNDARIA] * (len(df_por_estado) - 1)
                fig_est = grafico_barra(df_por_estado, x="estado", y="qtd", text="qtd")
                fig_est.update_traces(marker_color=cores_est)
                st.plotly_chart(fig_est, use_container_width=True, key="fig_est_wbr")

        st.divider()

        # ── Motivos (Monitoramento — diário) ─────────────────────
        st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#DE121C" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Motivos de Falha de Entrega</span>
</div>""", unsafe_allow_html=True)
        df_datas_mon_wbr = buscar_datas_disponiveis_mon()

        if df_datas_mon_wbr.empty:
            st.info("Sem dados de motivos. Importe 'Devolução - Monitoramento'.")
        else:
            datas_mon_wbr = pd.to_datetime(df_datas_mon_wbr["data_referencia"]).dt.date.tolist()
            data_mon_wbr = st.selectbox("Data (Monitoramento) / 日期", datas_mon_wbr, key="data_mon_wbr")

            df_motivos = buscar_dev_motivos(data_ref=data_mon_wbr, cliente=cliente_cod_wbr)
            if not df_motivos.empty:
                cores = [COR_PRINCIPAL] + [COR_SECUNDARIA] * (len(df_motivos) - 1)
                fig_mot = grafico_barra(df_motivos, x="qtd", y="motivo", text="qtd")
                fig_mot.update_traces(marker_color=cores)
                fig_mot.update_layout(yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig_mot, use_container_width=True, key="fig_mot_wbr")
            else:
                st.info("Sem dados de motivos para esta data.")

    # ════════════════════════════════════════
    # TAB 4 — SEMANAL INTERNO
    # ════════════════════════════════════════
    with tab4:
        st.subheader("📊 Relatório Semanal — Interno")

        # ── Filtro de cliente ─────────────────────────────────────
        cliente_cod_int, _ = _cliente_selectbox("cliente_int", df_clientes)

        # ── Seletor Devolução (semanal) ───────────────────────────
        df_semanas_int = buscar_semanas_disponiveis_dev()

        if df_semanas_int.empty:
            st.warning("Sem dados. Importe os arquivos 'Devolução'.")
            semana_int = None
            ano_int    = None
            df_st_int  = pd.DataFrame()
        else:
            opcoes_int = _opcoes_semana(df_semanas_int)
            sel_int = st.selectbox("Semana (Devolução) / 周", opcoes_int, key="semana_int")
            semana_int, ano_int = _parse_semana(sel_int)

            from utils.semana import semana_para_datas, datas_para_label
            data_ini_int, data_fim_int = semana_para_datas(semana_int, ano_int)
            st.caption(f"Período: **{datas_para_label(data_ini_int, data_fim_int)}**")

            df_st_int = buscar_dev_status_semanal(semana=semana_int, ano=ano_int, cliente=cliente_cod_int)

        # ── Seletor Monitoramento (diário) ────────────────────────
        df_datas_mon_int = buscar_datas_disponiveis_mon()

        if df_datas_mon_int.empty:
            data_mon_int = None
        else:
            datas_mon_int = pd.to_datetime(df_datas_mon_int["data_referencia"]).dt.date.tolist()
            data_mon_int = st.selectbox("Data (Monitoramento) / 日期", datas_mon_int, key="data_mon_int")

        st.divider()

        # ── Pizza — Total processado (Devolução) ──────────────────
        st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2B2D42" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Total Processado</span>
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
            col1.metric("Total", total_geral)
            col2.metric("Devolvidos", total_dev)
            col3.metric("Retornou ao Processo", total_proc)
            col4.metric("Aguardando", total_agu)

            df_pizza_int = pd.DataFrame([
                {"categoria": "Devolvidos",           "qtd": total_dev},
                {"categoria": "Retornou ao Processo", "qtd": total_proc},
                {"categoria": "Aguardando tratativa", "qtd": total_agu},
            ])
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                fig_pizza_int = grafico_pizza(df_pizza_int, names="categoria", values="qtd")
                st.plotly_chart(fig_pizza_int, use_container_width=True, key="fig_pizza_int")
            with col_p2:
                tabela_padrao(df_pizza_int.rename(columns={"categoria": "Categoria", "qtd": "Qtd"}))
        else:
            st.info("Sem dados de status. Importe 'Devolução'.")

        st.divider()

        # ── Motivos (Monitoramento — diário) ─────────────────────
        st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#DE121C" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
<line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Principais Motivos</span>
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
                st.info("Sem dados de motivos para esta data.")
        else:
            st.info("Sem dados de motivos. Importe 'Devolução - Monitoramento'.")

        st.divider()

        # ── Interceptados (Monitoramento — diário) ────────────────
        st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#DE121C" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
<line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Interceptados por Iata</span>
</div>""", unsafe_allow_html=True)
        if data_mon_int:
            df_inter = buscar_dev_interceptados(data_ref=data_mon_int, cliente=cliente_cod_int)
            if not df_inter.empty:
                tabela_padrao(df_inter.rename(columns={
                    "ponto_entrada": "Iata",
                    "estado": "Estado",
                    "qtd": "Qtd"
                }))
            else:
                st.info("Sem dados de interceptados para esta data.")
        else:
            st.info("Sem dados de interceptados. Importe 'Devolução - Monitoramento'.")

        st.divider()

        # ── Principais Estados (Devolução — semanal) ──────────────
        st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2B2D42" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/><line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Principais Estados com Devoluções</span>
</div>""", unsafe_allow_html=True)
        if not df_st_int.empty:
            df_est_int = df_st_int.groupby("estado")["qtd"].sum().reset_index()
            df_est_int = df_est_int.sort_values("qtd", ascending=False)
            tabela_padrao(df_est_int.rename(columns={"estado": "Estado", "qtd": "Qtd"}))

        st.divider()

        # ── Top 5 Iatas por Estado (DINÂMICO) ────────────────────
        st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#2B2D42" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Top 5 Iatas por Estado</span>
</div>""", unsafe_allow_html=True)
        st.caption("Estados calculados dinamicamente com base no volume da semana")

        df_iatas_todos = buscar_dev_iatas_semanal(semana=semana_int, ano=ano_int)

        if df_iatas_todos.empty:
            st.info("Sem dados de iatas para a semana selecionada.")
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
        st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#DE121C" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
<line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">DSPs que Devolvem sem 3 Tentativas</span>
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
                        "ponto_entrada": "Iata",
                        "estado": "Estado",
                        "qtd": "Qtd"
                    }))
            else:
                st.info("Sem dados de DSPs para esta data.")
        else:
            st.info("Sem dados de DSPs. Importe 'Devolução - Monitoramento'.")

    rodape_autoria()
