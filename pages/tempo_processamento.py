import streamlit as st
import pandas as pd

from core.repository import (
    buscar_tempo_processamento,
    buscar_hiata_por_dia,
    buscar_consolidado_por_dia
)

from utils.theme import grafico_barra, grafico_pizza
from utils.style import tabela_padrao, rodape_autoria, aplicar_css_global, fmt_numero
from utils.i18n import t

# ── Paleta Tempo de Processamento ────────────────────────────────────
COR_PRINCIPAL  = "#F0A202"   # Amarelo Anjun — cor dominante desta página
COR_SECUNDARIA = "#053B31"   # Verde escuro — complementar
COR_POSITIVO   = "#009640"   # Verde — dentro do SLA
COR_APOIO      = "#2B2D42"   # Navy — sem saída/neutro
PALETA_PAGINA  = [COR_PRINCIPAL, COR_SECUNDARIA, COR_POSITIVO, COR_APOIO]


def _cores_pizza():
    return {
        t("comum.ate_24h"): COR_POSITIVO,
        "> 24h":            COR_PRINCIPAL,
        t("comum.sem_info"): COR_APOIO,
    }


def _formatar_horas(h):
    if pd.isna(h): return "00:00"
    horas   = int(h)
    minutos = int((h - horas) * 60)
    return f"{horas:02d}:{minutos:02d}"


def render():
    aplicar_css_global()

    st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:0.5rem;">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
         stroke="#F0A202" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
    </svg>
    <div>
        <h2 style="margin:0;font-size:20px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("tempo.titulo")}</h2>
        <p style="margin:0;font-size:12px;color:#6b7280;font-family:'Montserrat',sans-serif;">{t("tempo.subtitulo")}</p>
    </div>
</div>
""", unsafe_allow_html=True)

    # =========================
    # 📅 FILTRO
    # =========================
    col1, col2 = st.columns(2)
    usar_filtro = st.checkbox(t("comum.filtrar_periodo"))

    if usar_filtro:
        data_inicio = col1.date_input(t("comum.data_inicio"))
        data_fim    = col2.date_input(t("comum.data_fim"))
    else:
        data_inicio = None
        data_fim    = None

    df = buscar_tempo_processamento(data_inicio, data_fim)

    if df.empty:
        st.warning(t("comum.sem_dados"))
        return

    tab1, tab2, tab3 = st.tabs([
        t("tempo.tab_sla"),
        t("tempo.tab_hiata"),
        t("tempo.tab_consolidado"),
    ])

    with tab1:
        # =========================
        # 🧠 TRATAMENTO
        # =========================
        total      = int(df["qtd_total"].sum())
        dentro_sla = int(df["qtd_dentro_sla"].sum())
        perc_sla   = (dentro_sla / total * 100) if total else 0
        tempo_medio = (
            (df["tempo_medio_h"] * df["qtd_total"]).sum() / df["qtd_total"].sum()
            if df["qtd_total"].sum() > 0 else 0
        )

        st.divider()

        # =========================
        # 📊 SLA
        # =========================
        col1, col2 = st.columns(2)

        with col1:
            st.metric(t("tempo.sla_24h"), f"{perc_sla:.1f}%")
            if perc_sla < 70:
                st.error(t("tempo.sla_critico"))
            elif perc_sla < 85:
                st.warning(t("tempo.sla_atencao"))
            else:
                st.success(t("tempo.sla_saudavel"))

        with col2:
            st.metric(t("tempo.tempo_medio"), f"{tempo_medio:.1f}h")
            if tempo_medio > 24:
                st.error(t("tempo.media_acima_24h"))
            else:
                st.success(t("tempo.media_dentro_sla"))

        st.divider()

        # =========================
        # 🥧 PIZZA + TABELA POR DIA
        # =========================
        col_s1, col_s2 = st.columns(2)

        with col_s1:
            st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#F0A202" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("tempo.distribuicao_status")}</span>
</div>""", unsafe_allow_html=True)
            cores_pizza = _cores_pizza()
            df_pizza = pd.DataFrame([
                {"status": t("comum.ate_24h"),   "qtd": int(df["qtd_dentro_sla"].sum())},
                {"status": "> 24h",              "qtd": int(df["qtd_fora_sla"].sum())},
                {"status": t("comum.sem_info"),  "qtd": int(df["qtd_sem_saida"].sum())},
            ])
            fig_pizza = grafico_pizza(
                df_pizza,
                names="status",
                values="qtd",
                color="status",
                color_map=cores_pizza
            )
            st.plotly_chart(fig_pizza, use_container_width=True)

        with col_s2:
            st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#F0A202" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18M15 3v18"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("tempo.evolucao_dia")}</span>
</div>""", unsafe_allow_html=True)
            df["_tempo_pond"] = df["tempo_medio_h"] * df["qtd_total"]
            tabela_dia = (
                df.groupby("data").agg(
                    dentro_sla  = ("qtd_dentro_sla", "sum"),
                    fora_sla    = ("qtd_fora_sla",   "sum"),
                    sem_saida   = ("qtd_sem_saida",  "sum"),
                    qtd_total   = ("qtd_total",      "sum"),
                    _pond_sum   = ("_tempo_pond",    "sum"),
                ).reset_index()
            )
            tabela_dia["tempo_medio"] = (
                tabela_dia["_pond_sum"] / tabela_dia["qtd_total"].replace(0, pd.NA)
            )
            tabela_dia.drop(columns=["_pond_sum"], inplace=True)
            df.drop(columns=["_tempo_pond"], inplace=True)
            tabela_dia.rename(columns={"dentro_sla": "0-24h", "fora_sla": ">24h"}, inplace=True)

            tabela_dia["Média (h)"] = tabela_dia["tempo_medio"].apply(_formatar_horas)
            tabela_dia["% SLA"] = (
                tabela_dia["0-24h"] / tabela_dia["qtd_total"].replace(0, 1) * 100
            ).round(1).astype(str) + "%"
            tabela_dia = tabela_dia.sort_values("data", ascending=False)
            tabela_padrao(tabela_dia[["data", "0-24h", ">24h", "sem_saida", "qtd_total", "Média (h)", "% SLA"]])

        st.divider()

        # =========================
        # 🏆 RANKING ESTADOS + TOP 10 PONTOS ENTRADA
        # =========================
        col_r1, col_r2 = st.columns(2)

        with col_r1:
            st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#F0A202" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/>
<path d="M4 22h16"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2z"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("tempo.top5_estados_atraso")}</span>
</div>""", unsafe_allow_html=True)
            ranking = (
                df.groupby("estado")["qtd_fora_sla"]
                .sum()
                .reset_index(name="qtd_atrasos")
                .sort_values("qtd_atrasos", ascending=False)
                .head(5)
            )
            if not ranking.empty:
                cores = [COR_SECUNDARIA] + [COR_PRINCIPAL] * (len(ranking) - 1)
                fig_rank = grafico_barra(ranking, x="estado", y="qtd_atrasos", text="qtd_atrasos")
                fig_rank.update_traces(marker_color=cores)
                st.plotly_chart(fig_rank, use_container_width=True)

        with col_r2:
            st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#F0A202" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("tempo.top10_pontos_atraso")}</span>
</div>""", unsafe_allow_html=True)
            ranking_pre = (
                df.groupby("ponto_entrada")["qtd_fora_sla"]
                .sum()
                .reset_index(name="qtd_atrasos")
                .sort_values("qtd_atrasos", ascending=False)
                .head(10)
            )
            if not ranking_pre.empty:
                cores_pre = [COR_SECUNDARIA] + [COR_PRINCIPAL] * (len(ranking_pre) - 1)
                fig_pre = grafico_barra(ranking_pre, x="ponto_entrada", y="qtd_atrasos", text="qtd_atrasos")
                fig_pre.update_traces(marker_color=cores_pre)
                st.plotly_chart(fig_pre, use_container_width=True)
            else:
                st.info(t("tempo.sem_atrasos"))

        st.divider()

        # =========================
        # 📊 TABELA POR ESTADO
        # =========================
        st.markdown(f"""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#F0A202" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("tempo.por_estado")}</span>
</div>""", unsafe_allow_html=True)

        tabela_estado = (
            df.groupby("estado").agg(
                **{
                    "0-24h":     ("qtd_dentro_sla", "sum"),
                    ">24h":      ("qtd_fora_sla",   "sum"),
                    "Sem saída": ("qtd_sem_saida",  "sum"),
                    "Total":     ("qtd_total",      "sum"),
                }
            ).reset_index()
        )

        total_linha = pd.DataFrame([{
            "estado":     "TOTAL",
            "0-24h":      tabela_estado["0-24h"].sum(),
            ">24h":       tabela_estado[">24h"].sum(),
            "Sem saída":  tabela_estado["Sem saída"].sum(),
            "Total":      tabela_estado["Total"].sum(),
        }])
        tabela_estado = pd.concat([tabela_estado, total_linha], ignore_index=True)
        tabela_padrao(tabela_estado)

    with tab2:
        # =========================
        # 📊 HIATA H001 POR DIA
        # =========================
        st.subheader(t("tempo.hiata_por_dia"))

        df_hiata = buscar_hiata_por_dia(data_inicio, data_fim)

        if not df_hiata.empty:
            tabela_hiata = (
                df_hiata
                .pivot(index="data", columns="hiata", values="qtd")
                .fillna(0)
                .reset_index()
            )
            colunas_hiata = [col for col in tabela_hiata.columns if col != "data"]
            tabela_hiata["Total"] = tabela_hiata[colunas_hiata].sum(axis=1)
            tabela_hiata = tabela_hiata.sort_values("data", ascending=False)
            tabela_padrao(tabela_hiata)
        else:
            st.warning(t("tempo.sem_dados_hiata"))

    with tab3:
        # =========================
        # 📊 CONSOLIDAÇÃO OPERACIONAL
        # =========================
        st.subheader(t("tempo.consolidacao_titulo"))

        df_cons = buscar_consolidado_por_dia(None, None)

        if not df_cons.empty:
            media_perus = df_cons["total_perus"].mean()
            media_tfk   = df_cons["total_tfk"].mean()
            media_total = df_cons["total_geral"].mean()

            col1, col2, col3 = st.columns(3)
            col1.metric("Perus", f"{media_perus:.0f}/dia")
            col2.metric("TFK Direto", f"{media_tfk:.0f}/dia")
            col3.metric(t("comum.total"), f"{media_total:.0f}/dia")

            for col in ["total_perus", "total_tfk", "total_geral"]:
                df_cons[col] = df_cons[col].fillna(0).astype(int)
            tabela_padrao(df_cons)
        else:
            st.warning(t("tempo.sem_dados_periodo"))

    rodape_autoria()
