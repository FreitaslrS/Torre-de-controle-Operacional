import streamlit as st
import plotly.graph_objects as go
import io
import pandas as pd

from core.repository import (
    buscar_backlog_historico,
    consultar_backlog as consultar
)

from utils.theme import grafico_barra, aplicar_layout_padrao
from utils.style import tabela_padrao, rodape_autoria, aplicar_css_global, fmt_numero
from utils.semana import semana_para_datas, datas_para_label

# ── Paleta Backlog Histórico ──────────────────────────────────────────
COR_PRINCIPAL  = "#053B31"   # Verde escuro — cor dominante desta página
COR_SECUNDARIA = "#009640"   # Verde Anjun — complementar
COR_APOIO      = "#2B2D42"   # Navy — elementos neutros
PALETA_PAGINA  = [COR_PRINCIPAL, COR_SECUNDARIA, COR_APOIO]

FAIXAS_ORDEM = ["1 dia", "1-5 dias", "5-10 dias", "10-20 dias", "20-30 dias", "30+ dias"]

def gerar_download(df, key_prefix):
    col1, col2 = st.columns(2)

    csv = df.to_csv(index=False).encode("utf-8")
    col1.download_button("CSV", csv, f"{key_prefix}.csv", "text/csv", key=f"{key_prefix}_csv")

    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    col2.download_button(
        "Excel", buffer.getvalue(), f"{key_prefix}.xlsx",
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
    # 📅 DATA
    # =========================
    col1, col2 = st.columns(2)
    data_inicio = col1.date_input("Data início")
    data_fim    = col2.date_input("Data fim")

    if not data_inicio or not data_fim:
        return

    df = buscar_backlog_historico(data_inicio, data_fim)

    if df.empty:
        st.warning("Sem dados")
        return

    st.divider()

    tab1, tab2 = st.tabs(["Evolução e Gráficos", "Drill SLA"])

    with tab1:
        # =========================
        # 🎛️ FILTROS
        # =========================
        st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#053B31" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Filtros</span>
</div>""", unsafe_allow_html=True)
        col_f1, col_f2, col_f3 = st.columns(3)

        remover_estados  = col_f1.multiselect("Remover Estados",  options=sorted(df["estado"].unique()),  key="hist_rem_est")
        remover_clientes = col_f2.multiselect("Remover Clientes", options=sorted(df["cliente"].unique()), key="hist_rem_cli")
        faixa_filtro     = col_f3.selectbox("Faixa de backlog", ["Todos", "1-5 dias+", "5-10 dias+", "10+ dias"], key="hist_faixa")

        df_t1 = df.copy()

        if remover_estados:
            df_t1 = df_t1[~df_t1["estado"].isin(remover_estados)]

        if remover_clientes:
            df_t1 = df_t1[~df_t1["cliente"].isin(remover_clientes)]

        faixa_map = {
            "1-5 dias+": ["1-5 dias", "5-10 dias", "10-20 dias", "20-30 dias", "30+ dias"],
            "5-10 dias+": ["5-10 dias", "10-20 dias", "20-30 dias", "30+ dias"],
            "10+ dias":   ["10-20 dias", "20-30 dias", "30+ dias"],
        }
        if faixa_filtro in faixa_map:
            df_t1 = df_t1[df_t1["faixa_backlog_snapshot"].isin(faixa_map[faixa_filtro])]

        if df_t1.empty:
            st.warning("Sem dados para o filtro selecionado")
        else:
            st.divider()

            # =========================
            # 📊 KPI POR FAIXA
            # =========================
            def qtd_faixa(faixa):
                return int(df_t1.loc[df_t1["faixa_backlog_snapshot"] == faixa, "qtd"].sum())

            col1, col2, col3, col4, col5, col6 = st.columns(6)
            col1.metric("1 dia",      qtd_faixa("1 dia"))
            col2.metric("1-5 dias",   qtd_faixa("1-5 dias"))
            col3.metric("5-10 dias",  qtd_faixa("5-10 dias"))
            col4.metric("10-20 dias", qtd_faixa("10-20 dias"))
            col5.metric("20-30 dias", qtd_faixa("20-30 dias"))
            col6.metric("30+ dias",   qtd_faixa("30+ dias"))

            st.divider()

            # =========================
            # 📈 EVOLUÇÃO POR DIA
            # =========================
            df_tempo = df_t1.groupby("data_referencia")["qtd"].sum().reset_index()

            if not df_tempo.empty:
                df_tempo = df_tempo.sort_values("data_referencia")
                df_tempo["pct_change"] = df_tempo["qtd"].pct_change() * 100
                df_tempo["pct_label"] = df_tempo["pct_change"].apply(
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
            # 📊 GRÁFICOS AGRUPADOS
            # =========================
            df_estado  = df_t1.groupby("estado")["qtd"].sum().reset_index()
            df_cliente = df_t1.groupby("cliente")["qtd"].sum().reset_index()
            df_pre     = df_t1.groupby("pre_entrega")["qtd"].sum().reset_index()

            col_g1, col_g2 = st.columns(2)

            with col_g1:
                st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#053B31" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/><line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Estado</span>
</div>""", unsafe_allow_html=True)
                df_e = df_estado.sort_values("qtd", ascending=False)
                cores = [COR_PRINCIPAL] + [COR_SECUNDARIA] * (len(df_e) - 1)
                fig_e = grafico_barra(df_e, x="estado", y="qtd", text="qtd")
                fig_e.update_traces(marker_color=cores)
                st.plotly_chart(fig_e, use_container_width=True)

            with col_g2:
                st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#053B31" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Cliente</span>
</div>""", unsafe_allow_html=True)
                df_c = df_cliente.sort_values("qtd", ascending=False)
                cores = [COR_PRINCIPAL] + [COR_SECUNDARIA] * (len(df_c) - 1)
                fig_c = grafico_barra(df_c, x="cliente", y="qtd", text="qtd")
                fig_c.update_traces(marker_color=cores)
                st.plotly_chart(fig_c, use_container_width=True)

            st.divider()

            # =========================
            # 📋 PRÓXIMO PONTO + PRÉ-ENTREGA
            # =========================
            col_pp1, col_pp2 = st.columns(2)

            with col_pp1:
                if "proximo_ponto" in df_t1.columns:
                    st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#053B31" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18M15 3v18"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Próximo Ponto</span>
</div>""", unsafe_allow_html=True)
                    df_proximo = df_t1.groupby("proximo_ponto")["qtd"].sum().reset_index()
                    df_proximo = df_proximo.sort_values("qtd", ascending=False).reset_index(drop=True)
                    df_proximo.columns = ["Próximo Ponto / 下一站", "Qtd / 数量"]
                    tabela_padrao(df_proximo)

            with col_pp2:
                st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#053B31" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/>
<path d="M4 22h16"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2z"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Top 10 Pré-entrega</span>
</div>""", unsafe_allow_html=True)
                df_pre_top10 = df_pre.sort_values("qtd", ascending=False).head(10)
                fig_pre = grafico_barra(df_pre_top10, x="qtd", y="pre_entrega", text="qtd", cor=COR_SECUNDARIA)
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
                df_t1.groupby(["estado", "faixa_backlog_snapshot"])["qtd"]
                .sum()
                .unstack(fill_value=0)
                .reset_index()
            )
            for col in FAIXAS_ORDEM:
                if col not in tabela_estado.columns:
                    tabela_estado[col] = 0
            tabela_estado["Total"] = tabela_estado[[c for c in FAIXAS_ORDEM if c in tabela_estado.columns]].sum(axis=1)
            tabela_padrao(tabela_estado, use_container_width=True)

    with tab2:
        # =========================
        # ⏱️ DRILL SLA (backlog_atual)
        # =========================
        st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#053B31" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Drill SLA</span>
</div>""", unsafe_allow_html=True)

        faixa_tempo = st.selectbox("Tempo backlog", ["24h+", "48h+", "72h+"], key="drill_faixa")

        condicao_map = {
            "24h+": "horas_backlog_snapshot > 24 AND horas_backlog_snapshot <= 48",
            "48h+": "horas_backlog_snapshot > 48 AND horas_backlog_snapshot <= 72",
            "72h+": "horas_backlog_snapshot > 72",
        }
        condicao = condicao_map[faixa_tempo]

        df_count = consultar(f"SELECT COUNT(*) as total FROM backlog_atual WHERE {condicao}")
        total_registros = int(df_count["total"].iloc[0]) if not df_count.empty else 0

        df_sla = consultar(f"""
            SELECT waybill, cliente, estado, pre_entrega, proximo_ponto, horas_backlog_snapshot
            FROM backlog_atual
            WHERE {condicao}
            LIMIT 500
        """)

        if total_registros > 500:
            st.info(f"Exibindo 500 de {total_registros} registros.")

        tabela_padrao(df_sla, use_container_width=True)
        gerar_download(df_sla, "drill_sla")

    rodape_autoria()
