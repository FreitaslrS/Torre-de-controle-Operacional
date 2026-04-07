import streamlit as st
import pandas as pd

from core.repository import (
    buscar_tempo_processamento,
    buscar_hiata_por_dia,
    buscar_consolidado_por_dia
)

from utils.theme import grafico_barra, grafico_pizza
from utils.style import aplicar_css_global, tabela_padrao

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
    aplicar_css_global()

    # =========================
    # 📅 FILTRO (CORRIGIDO)
    # =========================
    col1, col2 = st.columns(2)

    usar_filtro = st.checkbox("Filtrar por período")

    if usar_filtro:
        data_inicio = col1.date_input("Data início / 开始日期")
        data_fim = col2.date_input("Data fim / 结束日期")
        if data_inicio and data_fim and data_inicio > data_fim:
            st.error("Data início não pode ser maior que a data fim.")
            return
    else:
        data_inicio = None
        data_fim = None

    df = buscar_tempo_processamento(data_inicio, data_fim)

    if df.empty:
        st.warning("Sem dados / 暂无数据")
        return

    # =========================
    # 🧠 TRATAMENTO
    # =========================
    df["entrada_hub1"] = pd.to_datetime(df["entrada_hub1"], errors="coerce")
    df["saida_hub1"] = pd.to_datetime(df["saida_hub1"], errors="coerce")

    # 🔥 remove lixo (melhoria)
    df = df.dropna(subset=["entrada_hub1"])

    if df.empty:
        st.warning("Sem dados no período / 当前时间段无数据")
        return

    # =========================
    # ⏱️ TEMPO
    # =========================
    df["tempo_horas"] = (
        (df["saida_hub1"] - df["entrada_hub1"])
        .dt.total_seconds() / 3600
    )

    # mantém tudo (inclusive sem saída)
    # só evita valores negativos ou absurdos
    df = df[
        (df["tempo_horas"].isna()) |
        ((df["tempo_horas"] >= 0) & (df["tempo_horas"] <= 240))
    ]

    # 🔥 FILTRO TFK + H01
    df_h01 = df.copy() if not df.empty else pd.DataFrame()

    st.divider()

    # =========================
    # 📊 CÁLCULOS
    # =========================
    total = len(df)
    dentro_sla = len(df[df["tempo_horas"] <= 24])

    perc_sla = (dentro_sla / total) * 100 if total else 0

    df_valido = df[
        (df["tempo_horas"] >= 0) &
        (df["tempo_horas"] <= 240)
    ]

    tempo_medio_limpo = df_valido["tempo_horas"].mean() or 0

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
        st.metric("⏱️ Tempo médio / 平均处理时间", f"{tempo_medio_limpo:.1f}h")

        if tempo_medio_limpo > 24:
            st.error("🚨 Tempo médio acima de 24h / 超过24小时")
        else:
            st.success("✅ Tempo médio dentro do SLA / 时效正常")

    # =========================
    # 🧩 CLASSIFICAÇÃO
    # =========================
    def classificar(row):
        if pd.isna(row["saida_hub1"]):
            return "Sem saída"
        elif row["tempo_horas"] <= 24:
            return "Até 24h"
        else:
            return "> 24h"

    df["status"] = df.apply(classificar, axis=1)
    df["status_label"] = df["status"].map(traducao_status)

    st.divider()

    # =========================
    # 📊 TABELA
    # =========================
    def faixa(h):
        if pd.isna(h):
            return "Sem saída"
        elif h <= 24:
            return "0-24h"
        elif h <= 48:
            return "24-48h"
        elif h <= 72:
            return "48-72h"
        else:
            return ">72h"

    df["faixa"] = df["tempo_horas"].apply(faixa)

    # =========================
    # 🥧 PIZZA
    # =========================
    st.subheader("📊 Distribuição por Status / 各状态分布")
    df_pizza = df["status"].value_counts().reset_index()
    df_pizza.columns = ["status", "qtd"]
    df_pizza["status_label"] = df_pizza["status"].map(traducao_status)

    from utils.theme import grafico_pizza

    fig_pizza = grafico_pizza(
        df_pizza,
        names="status_label",
        values="qtd",
        color="status",
        color_map=cores_pizza
    )

    st.plotly_chart(fig_pizza, use_container_width=True)

    st.divider()

    # =========================
    # 📊 TABELA POR DIA (STATUS)
    # =========================
    st.subheader("📊 Evolução por Dia / 每日时效分布")

    # 🔥 GARANTE QUE FAIXA EXISTE (ANTI BUG STREAMLIT)
    if "faixa" not in df.columns:
        def faixa(h):
            if pd.isna(h):
                return "Sem saída"
            elif h <= 24:
                return "0-24h"
            elif h <= 48:
                return "24-48h"
            elif h <= 72:
                return "48-72h"
            else:
                return ">72h"

        df["faixa"] = df["tempo_horas"].apply(faixa)

    df["data"] = df["entrada_hub1"].dt.date

    # agrupamento por dia e faixa
    tabela_dia = (
        df.groupby(["data", "faixa"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    # garante colunas
    for col in ["0-24h", "24-48h", "48-72h", ">72h", "Sem saída"]:
        if col not in tabela_dia.columns:
            tabela_dia[col] = 0

    # total do dia
    tabela_dia["Total"] = tabela_dia[
        ["0-24h", "24-48h", "48-72h", ">72h", "Sem saída"]
    ].sum(axis=1)

    # média (tempo médio real do dia)
    media_dia = (
        df.groupby("data")["tempo_horas"]
        .mean()
        .reset_index(name="Média (h)")
    )

    def formatar_horas(h):
        if pd.isna(h):
            return "00:00"
        horas = int(h)
        minutos = int((h - horas) * 60)
        return f"{horas:02d}:{minutos:02d}"

    media_dia["Média (h)"] = media_dia["Média (h)"].apply(formatar_horas)

    # merge
    tabela_dia = tabela_dia.merge(media_dia, on="data", how="left")

    # percentual SLA (até 24h)
    tabela_dia["% SLA"] = (
        (tabela_dia["0-24h"] / tabela_dia["Total"].replace(0, 1)) * 100
    ).round(1)

    tabela_dia["% SLA"] = tabela_dia["% SLA"].astype(str) + "%"

    # ordena
    tabela_dia = tabela_dia.sort_values("data", ascending=False)

    tabela_padrao(tabela_dia)

    st.divider()

    

    tabela = (
        df.groupby(["estado", "faixa"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    for col in ["0-24h", "24-48h", "48-72h", ">72h", "Sem saída"]:
        if col not in tabela.columns:
            tabela[col] = 0

    tabela["Total / 总计"] = tabela[
        ["0-24h", "24-48h", "48-72h", ">72h", "Sem saída"]
    ].sum(axis=1)

    # =========================
    # 🏆 RANKING
    # =========================
    st.subheader("🏆 Top 5 Estados com Maior Atraso / 延误最多的州")

    df_atraso = df[df["tempo_horas"] > 24]

    ranking = (
        df_atraso.groupby("estado")
        .size()
        .reset_index(name="qtd_atrasos")
        .sort_values("qtd_atrasos", ascending=False)
        .head(5)
    )

    from utils.theme import grafico_barra

    ranking_sorted = ranking.sort_values("qtd_atrasos", ascending=False)

    cores = ["#0F172A"] + ["#16A34A"] * (len(ranking_sorted) - 1)

    fig_rank = grafico_barra(
        ranking_sorted,
        x="estado",
        y="qtd_atrasos",
        text="qtd_atrasos"
    )

    fig_rank.update_traces(marker_color=cores)

    st.plotly_chart(fig_rank, use_container_width=True)

    st.divider()

    # =========================
    # 📊 TOTAL
    # =========================
    total_geral = tabela[
        ["0-24h", "24-48h", "48-72h", ">72h", "Sem saída"]
    ].sum()

    total_linha = pd.DataFrame([{
        "estado": "TOTAL",
        "0-24h": total_geral["0-24h"],
        "24-48h": total_geral["24-48h"],
        "48-72h": total_geral["48-72h"],
        ">72h": total_geral[">72h"],
        "Sem saída": total_geral["Sem saída"],
        "Total / 总计": total_geral.sum()
    }])

    tabela = pd.concat([tabela, total_linha], ignore_index=True)

    # =========================
    # 📊 PRÉ-ENTREGA (ATRASO)
    # =========================
    st.subheader("📦 Top 10 Pontos de Entrada com Atraso / 入库点延误TOP10")

    df_atraso_pre = df[df["tempo_horas"] > 24]

    if not df_atraso_pre.empty:

        ranking_pre = (
            df_atraso_pre.groupby("ponto_entrada")
            .size()
            .reset_index(name="qtd_atrasos")
            .sort_values("qtd_atrasos", ascending=False)
            .head(10)
        )

        ranking_pre_sorted = ranking_pre.sort_values("qtd_atrasos", ascending=False)

        cores = ["#0F172A"] + ["#16A34A"] * (len(ranking_pre_sorted) - 1)

        fig_pre = grafico_barra(
            ranking_pre_sorted,
            x="ponto_entrada",
            y="qtd_atrasos",
            text="qtd_atrasos"
        )

        fig_pre.update_traces(marker_color=cores)

        st.plotly_chart(fig_pre, use_container_width=True)

    else:
        st.info("Sem atrasos nos pontos de entrada")

    st.divider()

    # =========================
    # 📋 EXIBIÇÃO
    # =========================
    st.subheader("📊 Tempo por Estado / 各州时效")

    tabela_padrao(tabela)

    # ======================================
    # 🥧 TABELA DESTINO DIRETO AOS ESTADOS
    # ======================================

    tabela_h01 = (
        df_h01.groupby("estado")
        .agg(
            total=("estado", "count"),
            dentro_sla=("tempo_horas", lambda x: (x <= 24).sum()),
            fora_sla=("tempo_horas", lambda x: (x > 24).sum())
        )
        .reset_index()
    )

    st.divider()

    # ======================================
    # 🥧 TABELA DESTINOS H01 (ENVIO DIRETO)
    # ======================================

    st.subheader("📊 Volume de Hiatas H001 por Dia - 每日 H001 批次量")

    df_hiata = buscar_hiata_por_dia(data_inicio, data_fim)

    if not df_hiata.empty:

        tabela_hiata = (
            df_hiata
            .pivot(index="data", columns="hiata", values="qtd")
            .fillna(0)
            .reset_index()
        )

        # 🔥 TOTAL POR DIA
        colunas_hiata = [col for col in tabela_hiata.columns if col != "data"]

        tabela_hiata["Total"] = tabela_hiata[colunas_hiata].sum(axis=1)

        # ordenar opcional
        tabela_hiata = tabela_hiata.sort_values("data", ascending=False)

        tabela_padrao(tabela_hiata)

    else:
        st.warning("Sem dados de hiata")


    st.divider()

    # ============================
    # 📊 CONSOLIDAÇÃO OPERACIONAL
    # ============================
    st.subheader("📊 Consolidação Operacional (Perus + TFK) - 运营整合（Perus + TFK）")

    df_cons = buscar_consolidado_por_dia(data_inicio, data_fim)

    if not df_cons.empty:

        # 📊 MÉDIAS
        media_perus = df_cons["total_perus"].mean()
        media_tfk = df_cons["total_tfk"].mean()
        media_total = df_cons["total_geral"].mean()

        col1, col2, col3 = st.columns(3)

        col1.metric("📦 Perus", f"{media_perus:.0f}/dia")
        col2.metric("🚚 TFK Direto", f"{media_tfk:.0f}/dia")
        col3.metric("🔥 Total", f"{media_total:.0f}/dia")

        # 📋 TABELA
        tabela_padrao(df_cons)

    else:
        st.warning("Sem dados para o período")
