import streamlit as st
import pandas as pd
import plotly.express as px

from core.database import consultar_backlog, consultar_processamento, consultar_operacional
from utils.theme import grafico_barra, aplicar_layout_padrao
from utils.style import tabela_padrao, aplicar_css_global

COR_VERDE = "#16A34A"
COR_AZUL  = "#0F172A"
COR_GELO  = "#CBD5E1"


@st.cache_data(ttl=600)
def _semanas_disponiveis_hc():
    return consultar_processamento("""
        SELECT DISTINCT
            TO_CHAR(data, '"w"IW')            AS semana,
            EXTRACT(YEAR FROM data)::INTEGER   AS ano
        FROM tempo_processamento
        ORDER BY ano DESC, semana DESC
    """)


@st.cache_data(ttl=600)
def _sla_hub(data_inicio, data_fim):
    return consultar_processamento("""
        SELECT
            SUM(qtd_total)      AS total,
            SUM(qtd_dentro_sla) AS dentro,
            SUM(qtd_fora_sla)   AS fora,
            SUM(qtd_sem_saida)  AS sem_info,
            ROUND(
                (SUM(qtd_dentro_sla * tempo_medio_h) /
                 NULLIF(SUM(qtd_dentro_sla), 0))::numeric, 2
            )                   AS lead_medio_h
        FROM tempo_processamento
        WHERE data BETWEEN %s AND %s
    """, [data_inicio, data_fim])


@st.cache_data(ttl=600)
def _backlog_faixa(horas):
    return consultar_backlog(f"""
        SELECT estado, COUNT(*) AS total, pre_entrega
        FROM backlog_atual
        WHERE horas_backlog_snapshot > {horas}
        GROUP BY estado, pre_entrega
        ORDER BY total DESC
    """)


@st.cache_data(ttl=600)
def _produtividade_turno(data_inicio, data_fim):
    return consultar_operacional("""
        SELECT turno, SUM(volumes) AS volumes
        FROM produtividade
        WHERE data BETWEEN %s AND %s
        GROUP BY turno
        ORDER BY turno
    """, [data_inicio, data_fim])


def render():
    from utils.semana import semana_para_datas, datas_para_label
    aplicar_css_global()

    st.markdown("""
    ## 🏥 Health Check Operacional / 运营健康检查
    <p style='opacity:0.7'>Visão consolidada semanal — Performance de SLAs, Backlog e Produtividade</p>
    """, unsafe_allow_html=True)

    # ── Seletor de semana ────────────────────────────────────────
    df_sems = _semanas_disponiveis_hc()
    if df_sems.empty:
        st.warning("Sem dados. Importe os arquivos de Tempo de Processamento e Produtividade.")
        return

    opcoes = [f"{r['semana']}/{int(r['ano'])}" for _, r in df_sems.iterrows()]
    sem_sel = st.selectbox("📅 Semana de referência", opcoes, key="hc_semana")
    sem_str, ano_hc = sem_sel.split("/")
    ano_hc = int(ano_hc)

    data_inicio, data_fim = semana_para_datas(sem_str, ano_hc)
    label_periodo = datas_para_label(data_inicio, data_fim)

    st.caption(f"Período: **{label_periodo}** (semana ISO {sem_str.upper()})")
    st.divider()

    # ════════════════════════════════════════════════════════
    # SLIDE 2 — Performance de Saídas e Lead Time
    # ════════════════════════════════════════════════════════
    st.subheader("📤 Performance de Saídas e Lead Time / 出库绩效与交付周期")

    df_sla = _sla_hub(data_inicio, data_fim)

    if df_sla.empty or df_sla["total"].iloc[0] is None:
        st.warning("Sem dados de tempo de processamento para esta semana.")
    else:
        total    = int(df_sla["total"].iloc[0])
        dentro   = int(df_sla["dentro"].iloc[0])
        fora     = int(df_sla["fora"].iloc[0])
        sem_info = int(df_sla["sem_info"].iloc[0])
        lead_h   = float(df_sla["lead_medio_h"].iloc[0] or 0)

        pct_dentro   = dentro   / total * 100 if total else 0
        pct_fora     = fora     / total * 100 if total else 0
        pct_sem_info = sem_info / total * 100 if total else 0

        hh = int(lead_h)
        mm = int((lead_h - hh) * 60)
        lead_fmt = f"{hh:02d}:{mm:02d}h"

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total / 总计",          f"{total:,}")
        col2.metric("✅ Dentro do Prazo",    f"{dentro:,}",   f"{pct_dentro:.1f}%")
        col3.metric("❌ Fora do Prazo",      f"{fora:,}",     f"{pct_fora:.1f}%")
        col4.metric("⚪ Sem Info Saída",     f"{sem_info:,}", f"{pct_sem_info:.1f}%")
        col5.metric("⏱️ Lead Time Médio",    lead_fmt)

        if pct_dentro < 70:
            st.error(f"🚨 SLA crítico: apenas {pct_dentro:.1f}% dentro do prazo")
        elif pct_dentro < 85:
            st.warning(f"⚠️ SLA em atenção: {pct_dentro:.1f}% dentro do prazo")
        else:
            st.success(f"✅ SLA saudável: {pct_dentro:.1f}% dentro do prazo")

        df_pizza_sla = pd.DataFrame([
            {"status": f"Dentro do Prazo ({pct_dentro:.1f}%)",  "qtd": dentro},
            {"status": f"Fora do Prazo ({pct_fora:.1f}%)",      "qtd": fora},
            {"status": f"Sem Info ({pct_sem_info:.1f}%)",       "qtd": sem_info},
        ])
        fig_sla = px.pie(
            df_pizza_sla, names="status", values="qtd",
            color_discrete_sequence=[COR_VERDE, COR_AZUL, COR_GELO]
        )
        fig_sla = aplicar_layout_padrao(fig_sla)
        st.plotly_chart(fig_sla, use_container_width=True, key="fig_sla_hc")

    st.divider()

    # ════════════════════════════════════════════════════════
    # SLIDE 3 — Backlog 24h
    # ════════════════════════════════════════════════════════
    st.subheader("📦 Backlog 24h / 24小时积压")
    st.caption("Snapshot atual — pacotes com mais de 24h no hub sem saída")

    df_24 = _backlog_faixa(24)

    if df_24.empty:
        st.info("Sem dados de backlog. Importe o arquivo de backlog.")
    else:
        col_b1, col_b2 = st.columns(2)

        with col_b1:
            st.markdown("**Top 5 Estados / 前5州**")
            df_est_24 = df_24.groupby("estado")["total"].sum().reset_index()
            df_est_24 = df_est_24.sort_values("total", ascending=False).head(5)
            cores_24 = [COR_AZUL] + [COR_VERDE] * 4
            fig_est_24 = grafico_barra(df_est_24, x="estado", y="total", text="total")
            fig_est_24.update_traces(marker_color=cores_24)
            st.plotly_chart(fig_est_24, use_container_width=True, key="fig_est24_hc")

        with col_b2:
            st.markdown("**Top 5 Pré-entregas / 前5预派送点**")
            df_pre_24 = df_24.groupby("pre_entrega")["total"].sum().reset_index()
            df_pre_24 = df_pre_24.sort_values("total", ascending=False).head(5)
            cores_pre24 = [COR_AZUL] + [COR_VERDE] * 4
            fig_pre_24 = grafico_barra(df_pre_24, x="total", y="pre_entrega", text="total")
            fig_pre_24.update_traces(marker_color=cores_pre24)
            fig_pre_24.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_pre_24, use_container_width=True, key="fig_pre24_hc")

    st.divider()

    # ════════════════════════════════════════════════════════
    # SLIDE 4 — Backlog 48h
    # ════════════════════════════════════════════════════════
    st.subheader("📦 Backlog 48h / 48小时积压")
    st.caption("Snapshot atual — pacotes com mais de 48h no hub sem saída")

    df_48 = _backlog_faixa(48)

    if df_48.empty:
        st.info("Sem dados de backlog 48h.")
    else:
        col_b3, col_b4 = st.columns(2)

        with col_b3:
            st.markdown("**Top 5 Estados / 前5州**")
            df_est_48 = df_48.groupby("estado")["total"].sum().reset_index()
            df_est_48 = df_est_48.sort_values("total", ascending=False).head(5)
            cores_48 = [COR_AZUL] + [COR_VERDE] * 4
            fig_est_48 = grafico_barra(df_est_48, x="estado", y="total", text="total")
            fig_est_48.update_traces(marker_color=cores_48)
            st.plotly_chart(fig_est_48, use_container_width=True, key="fig_est48_hc")

        with col_b4:
            st.markdown("**Top 5 Pré-entregas / 前5预派送点**")
            df_pre_48 = df_48.groupby("pre_entrega")["total"].sum().reset_index()
            df_pre_48 = df_pre_48.sort_values("total", ascending=False).head(5)
            cores_pre48 = [COR_AZUL] + [COR_VERDE] * 4
            fig_pre_48 = grafico_barra(df_pre_48, x="total", y="pre_entrega", text="total")
            fig_pre_48.update_traces(marker_color=cores_pre48)
            fig_pre_48.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_pre_48, use_container_width=True, key="fig_pre48_hc")

    st.divider()

    # ════════════════════════════════════════════════════════
    # SLIDE 5 — Produtividade por Turno
    # ════════════════════════════════════════════════════════
    st.subheader("⚡ Produtividade por Turno / 班次生产力")

    df_turno = _produtividade_turno(data_inicio, data_fim)

    if df_turno.empty:
        st.info("Sem dados de produtividade para esta semana.")
    else:
        total_prod = int(df_turno["volumes"].sum())
        st.metric("📦 Volume Total Processado / 处理总量", f"{total_prod:,}")

        turno_map = {r["turno"]: int(r["volumes"]) for _, r in df_turno.iterrows()}
        t1 = turno_map.get("T1", 0)
        t2 = turno_map.get("T2", 0)
        t3 = turno_map.get("T3", 0)

        col_t1, col_t2, col_t3 = st.columns(3)
        col_t1.metric("🟢 Turno 1", f"{t1:,}", f"{t1/total_prod*100:.1f}%" if total_prod else "")
        col_t2.metric("🔵 Turno 2", f"{t2:,}", f"{t2/total_prod*100:.1f}%" if total_prod else "")
        col_t3.metric("⚪ Turno 3", f"{t3:,}", f"{t3/total_prod*100:.1f}%" if total_prod else "")

        color_map = {"T1": COR_VERDE, "T2": COR_AZUL, "T3": COR_GELO}
        fig_turno = px.pie(
            df_turno, names="turno", values="volumes",
            color="turno", color_discrete_map=color_map
        )
        fig_turno = aplicar_layout_padrao(fig_turno)
        st.plotly_chart(fig_turno, use_container_width=True, key="fig_turno_hc")
