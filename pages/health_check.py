import streamlit as st
import pandas as pd
import plotly.express as px

from core.repository import (
    buscar_semanas_health_check,
    buscar_sla_hub,
    buscar_backlog_faixas_hc,
    buscar_produtividade_turno_hc,
)
from utils.theme import grafico_barra, aplicar_layout_padrao
from utils.style import tabela_padrao, aplicar_css_global, rodape_autoria, fmt_numero
from utils.semana import semana_para_datas, datas_para_label
from utils.i18n import t

# ── Paleta Health Check ───────────────────────────────────────────────
COR_PRINCIPAL  = "#DE121C"   # Vermelho Anjun — cor dominante desta página
COR_SECUNDARIA = "#009640"   # Verde Anjun — complementar (positivo)
COR_APOIO      = "#2B2D42"   # Navy — neutro
PALETA_PAGINA  = [COR_PRINCIPAL, COR_SECUNDARIA, COR_APOIO]

# Aliases mantidos para compatibilidade
COR_VERDE = COR_SECUNDARIA
COR_AZUL  = "#053B31"
COR_GELO  = COR_APOIO


def render():
    aplicar_css_global()

    st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:0.5rem;">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
         stroke="#DE121C" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
    </svg>
    <div>
        <h2 style="margin:0;font-size:20px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("hc.titulo")}</h2>
        <p style="margin:0;font-size:12px;color:#6b7280;font-family:'Montserrat',sans-serif;">{t("hc.subtitulo")}</p>
    </div>
</div>
""", unsafe_allow_html=True)

    # ── Seletor de semana ────────────────────────────────────────
    df_sems = buscar_semanas_health_check()
    if df_sems.empty:
        st.warning(t("hc.sem_dados"))
        return

    opcoes = [f"{r['semana']}/{int(r['ano'])}" for _, r in df_sems.iterrows()]
    sem_sel = st.selectbox(t("comum.semana_referencia"), opcoes, key="hc_semana")
    sem_str, ano_hc = sem_sel.split("/")
    ano_hc = int(ano_hc)

    data_inicio, data_fim = semana_para_datas(sem_str, ano_hc)
    label_periodo = datas_para_label(data_inicio, data_fim)

    st.caption(f"{t('comum.periodo')}: **{label_periodo}** (semana ISO {sem_str.upper()})")

    with st.expander(t("hc.comparar"), expanded=False):
        opcoes_comp = [o for o in opcoes if o != sem_sel]
        sem_comp = st.selectbox(t("hc.semana_comparacao"), [t("comum.nenhuma")] + opcoes_comp, key="hc_semana_comp")

    _nenhuma = t("comum.nenhuma")
    comp_ativo = sem_comp != _nenhuma
    if comp_ativo:
        sem_str_c, ano_hc_c = sem_comp.split("/")
        ano_hc_c = int(ano_hc_c)
        data_inicio_c, data_fim_c = semana_para_datas(sem_str_c, ano_hc_c)

    st.divider()

    # ════════════════════════════════════════════════════════
    # SLIDE 2 — Performance de Saídas e Lead Time
    # ════════════════════════════════════════════════════════
    st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#DE121C" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("hc.performance_saidas")}</span>
</div>""", unsafe_allow_html=True)

    df_sla = buscar_sla_hub(data_inicio, data_fim)

    if df_sla.empty or df_sla["total"].iloc[0] is None:
        st.warning(t("comum.sem_dados_periodo"))
    else:
        total_a  = int(df_sla["total"].iloc[0]  or 0)
        dentro_a = int(df_sla["dentro"].iloc[0] or 0)
        fora_a   = int(df_sla["fora"].iloc[0]   or 0)
        sem_info = int(df_sla["sem_info"].iloc[0] or 0)
        lead_a   = float(df_sla["lead_medio_h"].iloc[0] or 0)

        perc_sla_a   = round(dentro_a / total_a * 100, 1) if total_a else 0
        pct_fora     = fora_a   / total_a * 100 if total_a else 0
        pct_sem_info = sem_info / total_a * 100 if total_a else 0

        hh = int(lead_a)
        mm = int((lead_a - hh) * 60)
        lead_fmt = f"{hh:02d}:{mm:02d}h"

        if comp_ativo:
            df_sla_c   = buscar_sla_hub(data_inicio_c, data_fim_c)
            total_c    = int(df_sla_c["total"].iloc[0]  or 0) if not df_sla_c.empty else 0
            dentro_c   = int(df_sla_c["dentro"].iloc[0] or 0) if not df_sla_c.empty else 0
            lead_c     = float(df_sla_c["lead_medio_h"].iloc[0] or 0) if not df_sla_c.empty else 0
            perc_sla_c = round(dentro_c / total_c * 100, 1) if total_c else 0
        else:
            total_c = dentro_c = lead_c = perc_sla_c = None

        col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
        col_s1.metric(t("hc.total_processado"), fmt_numero(total_a),
                      delta=int(total_a - total_c) if comp_ativo else None)
        col_s2.metric(t("hc.dentro_sla"), fmt_numero(dentro_a),
                      delta=int(dentro_a - dentro_c) if comp_ativo else None)
        col_s3.metric(t("hc.perc_sla"), f"{perc_sla_a}%",
                      delta=f"{round(perc_sla_a - perc_sla_c, 1)}%" if comp_ativo else None)
        col_s4.metric(t("hc.lead_time_medio"), lead_fmt,
                      delta=f"{round(lead_a - lead_c, 1)}h" if comp_ativo else None,
                      delta_color="inverse")
        col_s5.metric(t("hc.fora_sla"), fmt_numero(fora_a), f"{pct_fora:.1f}%")

        total    = total_a
        dentro   = dentro_a
        fora     = fora_a
        lead_h   = lead_a
        pct_dentro = perc_sla_a

        if pct_dentro < 70:
            st.error(t("hc.sla_critico_msg").format(p=pct_dentro))
        elif pct_dentro < 85:
            st.warning(t("hc.sla_atencao_msg").format(p=pct_dentro))
        else:
            st.success(t("hc.sla_saudavel_msg").format(p=pct_dentro))

        df_pizza_sla = pd.DataFrame([
            {"status": t("hc.status_dentro_prazo").format(p=pct_dentro),  "qtd": dentro},
            {"status": t("hc.status_fora_prazo"),                          "qtd": fora},
            {"status": t("hc.status_sem_saida"),                           "qtd": sem_info},
        ])
        fig_sla = px.pie(
            df_pizza_sla, names="status", values="qtd",
            color_discrete_sequence=[COR_SECUNDARIA, COR_PRINCIPAL, COR_APOIO]
        )
        fig_sla = aplicar_layout_padrao(fig_sla)
        st.plotly_chart(fig_sla, use_container_width=True, key="fig_sla_hc")

    st.divider()

    # ════════════════════════════════════════════════════════
    # SLIDE 3 — Backlog 24h
    # ════════════════════════════════════════════════════════
    st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#DE121C" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("hc.backlog_24h")}</span>
</div>""", unsafe_allow_html=True)
    st.caption(t("hc.backlog_24h_caption"))

    df_faixas = buscar_backlog_faixas_hc()
    df_24 = df_faixas[["estado", "pre_entrega", "total_24"]].rename(columns={"total_24": "total"})
    df_24 = df_24[df_24["total"] > 0]

    if df_24.empty:
        st.info(t("hc.sem_dados_backlog"))
    else:
        col_b1, col_b2 = st.columns(2)

        with col_b1:
            st.markdown(f"**{t('hc.top5_estados')}**")
            df_est_24 = df_24.groupby("estado")["total"].sum().reset_index()
            df_est_24 = df_est_24.sort_values("total", ascending=False).head(5)
            cores_24 = [COR_PRINCIPAL] + [COR_APOIO] * 4
            fig_est_24 = grafico_barra(df_est_24, x="estado", y="total", text="total")
            fig_est_24.update_traces(marker_color=cores_24)
            st.plotly_chart(fig_est_24, use_container_width=True, key="fig_est24_hc")

        with col_b2:
            st.markdown(f"**{t('hc.top5_pre')}**")
            df_pre_24 = df_24.groupby("pre_entrega")["total"].sum().reset_index()
            df_pre_24 = df_pre_24.sort_values("total", ascending=False).head(5)
            cores_pre24 = [COR_PRINCIPAL] + [COR_APOIO] * 4
            fig_pre_24 = grafico_barra(df_pre_24, x="total", y="pre_entrega", text="total")
            fig_pre_24.update_traces(marker_color=cores_pre24)
            fig_pre_24.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_pre_24, use_container_width=True, key="fig_pre24_hc")

    st.divider()

    # ════════════════════════════════════════════════════════
    # SLIDE 4 — Backlog 48h
    # ════════════════════════════════════════════════════════
    st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#DE121C" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("hc.backlog_48h")}</span>
</div>""", unsafe_allow_html=True)
    st.caption(t("hc.backlog_48h_caption"))

    df_48 = df_faixas[["estado", "pre_entrega", "total_48"]].rename(columns={"total_48": "total"})
    df_48 = df_48[df_48["total"] > 0]

    if df_48.empty:
        st.info(t("hc.sem_dados_backlog_48h"))
    else:
        col_b3, col_b4 = st.columns(2)

        with col_b3:
            st.markdown(f"**{t('hc.top5_estados')}**")
            df_est_48 = df_48.groupby("estado")["total"].sum().reset_index()
            df_est_48 = df_est_48.sort_values("total", ascending=False).head(5)
            cores_48 = [COR_PRINCIPAL] + [COR_APOIO] * 4
            fig_est_48 = grafico_barra(df_est_48, x="estado", y="total", text="total")
            fig_est_48.update_traces(marker_color=cores_48)
            st.plotly_chart(fig_est_48, use_container_width=True, key="fig_est48_hc")

        with col_b4:
            st.markdown(f"**{t('hc.top5_pre')}**")
            df_pre_48 = df_48.groupby("pre_entrega")["total"].sum().reset_index()
            df_pre_48 = df_pre_48.sort_values("total", ascending=False).head(5)
            cores_pre48 = [COR_PRINCIPAL] + [COR_APOIO] * 4
            fig_pre_48 = grafico_barra(df_pre_48, x="total", y="pre_entrega", text="total")
            fig_pre_48.update_traces(marker_color=cores_pre48)
            fig_pre_48.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_pre_48, use_container_width=True, key="fig_pre48_hc")

    st.divider()

    # ════════════════════════════════════════════════════════
    # SLIDE 5 — Produtividade por Turno
    # ════════════════════════════════════════════════════════
    st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#DE121C" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("hc.prod_turno")}</span>
</div>""", unsafe_allow_html=True)

    df_turno = buscar_produtividade_turno_hc(data_inicio, data_fim)

    if df_turno.empty:
        st.info(t("hc.sem_dados_prod"))
    else:
        total_prod = int(df_turno["volumes"].sum())
        st.metric(t("hc.vol_total_processado"), fmt_numero(total_prod))

        turno_map = {r["turno"]: int(r["volumes"]) for _, r in df_turno.iterrows()}
        t1 = turno_map.get("T1", 0)
        t2 = turno_map.get("T2", 0)
        t3 = turno_map.get("T3", 0)

        col_t1, col_t2, col_t3 = st.columns(3)
        col_t1.metric(t("hc.turno1"), fmt_numero(t1), f"{t1/total_prod*100:.1f}%" if total_prod else "")
        col_t2.metric(t("hc.turno2"), fmt_numero(t2), f"{t2/total_prod*100:.1f}%" if total_prod else "")
        col_t3.metric(t("hc.turno3"), fmt_numero(t3), f"{t3/total_prod*100:.1f}%" if total_prod else "")

        color_map = {"T1": COR_SECUNDARIA, "T2": COR_APOIO, "T3": COR_PRINCIPAL}
        fig_turno = px.pie(
            df_turno, names="turno", values="volumes",
            color="turno", color_discrete_map=color_map
        )
        fig_turno = aplicar_layout_padrao(fig_turno)
        st.plotly_chart(fig_turno, use_container_width=True, key="fig_turno_hc")

    rodape_autoria()
