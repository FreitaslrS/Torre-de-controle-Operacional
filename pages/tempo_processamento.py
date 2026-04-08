import streamlit as st
import pandas as pd

from core.repository import (
    buscar_tempo_processamento,
    buscar_hiata_por_dia,
    buscar_consolidado_por_dia
)

from utils.theme import grafico_barra, grafico_pizza
from utils.style import tabela_padrao

cores_pizza = {
    "Até 24h": "#16A34A",
    "> 24h": "#0F172A",
    "Sem saída": "#CBD5E1"
}

traducao_status = {
    "Até 24h": "Até 24h / 24小时内",
    "> 24h": "> 24h / 超过24小时",
    "Sem saída": "Sem saída / 无出库"
}

def render():
    from utils.style import aplicar_css_global
    aplicar_css_global()

    # =========================
    # 📅 FILTRO
    # =========================
    col1, col2 = st.columns(2)
    usar_filtro = st.checkbox("Filtrar por período")

    if usar_filtro:
        data_inicio = col1.date_input("Data início / 开始日期")
        data_fim    = col2.date_input("Data fim / 结束日期")
    else:
        data_inicio = None
        data_fim    = None

    df = buscar_tempo_processamento(data_inicio, data_fim)

    if df.empty:
        st.warning("Sem dados / 暂无数据")
        return

    # =========================
    # 🧠 TRATAMENTO
    # =========================
    # dados já chegam agregados do banco
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
        st.metric("📊 SLA 24h / 24小时达标率", f"{perc_sla:.1f}%")
        if perc_sla < 70:
            st.error("🚨 SLA crítico / SLA严重")
        elif perc_sla < 85:
            st.warning("⚠️ SLA em atenção / SLA需关注")
        else:
            st.success("✅ SLA saudável / SLA正常")

    with col2:
        st.metric("⏱️ Tempo médio / 平均处理时间", f"{tempo_medio:.1f}h")
        if tempo_medio > 24:
            st.error("🚨 Tempo médio acima de 24h / 超过24小时")
        else:
            st.success("✅ Tempo médio dentro do SLA / 时效正常")

    st.divider()

    # =========================
    # 🥧 PIZZA + TABELA POR DIA
    # =========================
    col_s1, col_s2 = st.columns(2)

    with col_s1:
        st.subheader("📊 Distribuição por Status / 各状态分布")
        df_pizza = pd.DataFrame([
            {"status": "Até 24h",   "qtd": int(df["qtd_dentro_sla"].sum())},
            {"status": "> 24h",     "qtd": int(df["qtd_fora_sla"].sum())},
            {"status": "Sem saída", "qtd": int(df["qtd_sem_saida"].sum())},
        ])
        df_pizza["status_label"] = df_pizza["status"].map(traducao_status)
        fig_pizza = grafico_pizza(
            df_pizza,
            names="status_label",
            values="qtd",
            color="status",
            color_map=cores_pizza
        )
        st.plotly_chart(fig_pizza, use_container_width=True)

    with col_s2:
        st.subheader("📊 Evolução por Dia / 每日时效分布")
        tabela_dia = (
            df.groupby("data").agg(
                dentro_sla  = ("qtd_dentro_sla", "sum"),
                fora_sla    = ("qtd_fora_sla",   "sum"),
                sem_saida   = ("qtd_sem_saida",  "sum"),
                qtd_total   = ("qtd_total",      "sum"),
                tempo_medio = ("tempo_medio_h",  lambda x:
                    (x * df.loc[x.index, "qtd_total"]).sum() /
                    df.loc[x.index, "qtd_total"].sum()
                )
            ).reset_index()
        )
        tabela_dia.rename(columns={"dentro_sla": "0-24h", "fora_sla": ">24h"}, inplace=True)

        def formatar_horas(h):
            if pd.isna(h): return "00:00"
            horas   = int(h)
            minutos = int((h - horas) * 60)
            return f"{horas:02d}:{minutos:02d}"

        tabela_dia["Média (h)"] = tabela_dia["tempo_medio"].apply(formatar_horas)
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
        st.subheader("🏆 Top 5 Estados com Maior Atraso / 延误最多的州")
        ranking = (
            df.groupby("estado")["qtd_fora_sla"]
            .sum()
            .reset_index(name="qtd_atrasos")
            .sort_values("qtd_atrasos", ascending=False)
            .head(5)
        )
        if not ranking.empty:
            cores = ["#0F172A"] + ["#16A34A"] * (len(ranking) - 1)
            fig_rank = grafico_barra(ranking, x="estado", y="qtd_atrasos", text="qtd_atrasos")
            fig_rank.update_traces(marker_color=cores)
            st.plotly_chart(fig_rank, use_container_width=True)

    with col_r2:
        st.subheader("📦 Top 10 Pontos de Entrada com Atraso / 入库点延误TOP10")
        ranking_pre = (
            df.groupby("ponto_entrada")["qtd_fora_sla"]
            .sum()
            .reset_index(name="qtd_atrasos")
            .sort_values("qtd_atrasos", ascending=False)
            .head(10)
        )
        if not ranking_pre.empty:
            cores_pre = ["#0F172A"] + ["#16A34A"] * (len(ranking_pre) - 1)
            fig_pre = grafico_barra(ranking_pre, x="ponto_entrada", y="qtd_atrasos", text="qtd_atrasos")
            fig_pre.update_traces(marker_color=cores_pre)
            st.plotly_chart(fig_pre, use_container_width=True)
        else:
            st.info("Sem atrasos nos pontos de entrada")

    st.divider()

    # =========================
    # 📊 TABELA POR ESTADO
    # =========================
    st.subheader("📊 Tempo por Estado / 各州时效")

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

    st.divider()

    # =========================
    # 📊 HIATA H001 POR DIA
    # =========================
    st.subheader("📊 Volume de Hiatas H001 por Dia - 每日 H001 批次量")

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
        st.warning("Sem dados de hiata")

    st.divider()

    # =========================
    # 📊 CONSOLIDAÇÃO OPERACIONAL
    # =========================
    st.subheader("📊 Consolidação Operacional (Perus + TFK) - 运营整合（Perus + TFK）")

    df_cons = buscar_consolidado_por_dia(None, None)

    if not df_cons.empty:
        media_perus = df_cons["total_perus"].mean()
        media_tfk   = df_cons["total_tfk"].mean()
        media_total = df_cons["total_geral"].mean()

        col1, col2, col3 = st.columns(3)
        col1.metric("📦 Perus", f"{media_perus:.0f}/dia")
        col2.metric("🚚 TFK Direto", f"{media_tfk:.0f}/dia")
        col3.metric("🔥 Total", f"{media_total:.0f}/dia")

        tabela_padrao(df_cons)
    else:
        st.warning("Sem dados para o período")