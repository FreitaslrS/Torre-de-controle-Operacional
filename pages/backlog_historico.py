import streamlit as st
import plotly.express as px
import io
import pandas as pd

from core.repository import (
    buscar_backlog_historico,
    buscar_waybills_por_faixa_dias,
    consultar_backlog as consultar
)

from utils.theme import grafico_barra, grafico_linha, aplicar_layout_padrao

def gerar_download(df, key_prefix):

    col1, col2 = st.columns(2)

    # CSV
    csv = df.to_csv(index=False).encode("utf-8")
    col1.download_button(
        "⬇️ CSV",
        csv,
        f"{key_prefix}.csv",
        "text/csv",
        key=f"{key_prefix}_csv"
    )

    # Excel
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    col2.download_button(
        "⬇️ Excel",
        buffer.getvalue(),
        f"{key_prefix}.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=f"{key_prefix}_excel"
    )


def render():
    from utils.style import aplicar_css_global

    aplicar_css_global()

    st.markdown("""
    ## Backlog Histórico / 历史积压
    <p style='opacity:0.7'>Visão completa histórica da operação</p>
    """, unsafe_allow_html=True)

    # =========================
    # 📅 DATA
    # =========================
    col1, col2 = st.columns(2)

    data_inicio = col1.date_input("Data início")
    data_fim = col2.date_input("Data fim")

    if not data_inicio or not data_fim:
        return

    df = buscar_backlog_historico(data_inicio, data_fim)

    if df.empty:
        st.warning("Sem dados")
        return
    
    st.divider()

    # =========================
    # 🎛️ FILTROS IGUAL BACKLOG
    # =========================
    st.subheader("🎛️ Filtros")

    col_f1, col_f2 = st.columns(2)

    remover_estados = col_f1.multiselect(
        "Remover Estados",
        options=sorted(df["estado"].unique())
    )

    remover_clientes = col_f2.multiselect(
        "Remover Clientes",
        options=sorted(df["cliente"].unique())
    )

    faixa = st.selectbox(
        "Filtro de Backlog",
        ["Todos", "24h+", "48h+", "72h+"]
    )

    # aplicar filtros
    if remover_estados:
        df = df[~df["estado"].isin(remover_estados)]

    if remover_clientes:
        df = df[~df["cliente"].isin(remover_clientes)]

    if faixa == "24h+":
        df = df[df["horas_backlog_snapshot"] > 24]
    elif faixa == "48h+":
        df = df[df["horas_backlog_snapshot"] > 48]
    elif faixa == "72h+":
        df = df[df["horas_backlog_snapshot"] > 72]

    st.divider()  

    # =========================
    # 📊 KPI
    # =========================
    df["dias"] = df["horas_backlog_snapshot"] / 24

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("1 dia", df[df["dias"] <= 1].shape[0])
    col2.metric("1-5 dias", df[(df["dias"] > 1) & (df["dias"] <= 5)].shape[0])
    col3.metric("5-10 dias", df[(df["dias"] > 5) & (df["dias"] <= 10)].shape[0])
    col4.metric("10-20 dias", df[(df["dias"] > 10) & (df["dias"] <= 20)].shape[0])
    col5.metric("30+ dias", df[df["dias"] > 30].shape[0])

    st.divider()

    # =========================
    # 📈 EVOLUÇÃO
    # =========================
    df_tempo = df.groupby("data_referencia").size().reset_index(name="qtd")

    if not df_tempo.empty:
        df_tempo = df_tempo.sort_values("data_referencia")

        # 🔥 cálculo de variação %
        df_tempo["pct_change"] = df_tempo["qtd"].pct_change() * 100
        df_tempo["pct_label"] = df_tempo["pct_change"].apply(
            lambda x: f"{x:+.1f}%" if pd.notna(x) and x != float("inf") else ""
        )

        # 🔥 gráfico combinado
        import plotly.graph_objects as go

        fig = go.Figure()

        # 📊 barras
        fig.add_bar(
            x=df_tempo["data_referencia"],
            y=df_tempo["qtd"],
            name="Volume",
            marker_color="#CBD5E1"
        )

        # 📈 linha
        fig.add_trace(go.Scatter(
            x=df_tempo["data_referencia"],
            y=df_tempo["qtd"],
            mode="lines+markers+text",
            name="Tendência",
            line=dict(color="#16A34A", width=3),
            text=df_tempo["pct_label"],
            textposition="top center"
        ))

        from utils.theme import aplicar_layout_padrao
        fig = aplicar_layout_padrao(fig)

        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # =========================
    # 📊 AGRUPAMENTOS
    # =========================
    df_estado = df.groupby("estado").size().reset_index(name="qtd")
    df_cliente = df.groupby("cliente").size().reset_index(name="qtd")
    df_pre = df.groupby("pre_entrega").size().reset_index(name="qtd")

    if "proximo_ponto" in df.columns:
        df_proximo = df.groupby("proximo_ponto").size().reset_index(name="qtd")
    else:
        df_proximo = None

    # =========================
    # 📊 GRÁFICOS
    # =========================
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("📊 Estado")

        df_estado_sorted = df_estado.sort_values("qtd", ascending=False)

        cores = ["#0F172A"] + ["#16A34A"] * (len(df_estado_sorted) - 1)

        fig_estado = grafico_barra(
            df_estado_sorted,
            x="estado",
            y="qtd",
            text="qtd"
        )

        fig_estado.update_traces(marker_color=cores)

        st.plotly_chart(fig_estado, use_container_width=True)

    with col_g2:
        st.subheader("📊 Cliente")

        df_cliente_sorted = df_cliente.sort_values("qtd", ascending=False)

        cores = ["#0F172A"] + ["#16A34A"] * (len(df_cliente_sorted) - 1)

        fig_cliente = grafico_barra(
            df_cliente_sorted,
            x="cliente",
            y="qtd",
            text="qtd"
        )

        fig_cliente.update_traces(marker_color=cores)

        st.plotly_chart(fig_cliente, use_container_width=True)

    st.divider()

    # =========================
    # 📊 PRÓXIMO PONTO
    # =========================
    if df_proximo is not None and not df_proximo.empty:

        df_proximo_sorted = df_proximo.sort_values("qtd", ascending=False)

        cores = ["#0F172A"] + ["#16A34A"] * (len(df_proximo_sorted) - 1)

        fig_proximo = grafico_barra(
            df_proximo_sorted,
            x="proximo_ponto",
            y="qtd",
            text="qtd"
        )

        fig_proximo.update_traces(marker_color=cores)

        st.subheader("📊 Próximo Ponto / 下一站")
        st.plotly_chart(fig_proximo, use_container_width=True)

    st.divider()

    # =========================
    # 📊 TOP 10 PRÉ-ENTREGA 🔥
    # =========================
    st.subheader("📊 Top 10 Pré-entrega")

    df_pre_top10 = df_pre.sort_values("qtd", ascending=False).head(10)

    fig_pre = grafico_barra(
        df_pre_top10,
        x="qtd",
        y="pre_entrega",
        text="qtd",
        cor="#CBD5E1"
    )

    st.plotly_chart(fig_pre, use_container_width=True)

    st.divider()

    # =========================
    # 🔎 DRILL DOWN
    # =========================
    st.subheader("🔎 Drill Down")

    faixa_dias = st.selectbox(
        "Faixa de dias",
        ["1 dia", "1-5 dias", "5-10 dias", "10-20 dias", "30+ dias"]
    )

    df_drill = buscar_waybills_por_faixa_dias(data_inicio, data_fim, faixa_dias)

    st.dataframe(df_drill, use_container_width=True)
    gerar_download(df_drill, "drill_dias")

    st.divider()

    # =========================
    # ⏱️ DRILL SLA
    # =========================
    st.subheader("⏱️ Drill SLA")

    faixa_tempo = st.selectbox("Tempo backlog", ["24h+", "48h+", "72h+"])

    if faixa_tempo == "24h+":
        condicao = "horas_backlog_snapshot > 24 AND horas_backlog_snapshot <= 48"

    elif faixa_tempo == "48h+":
        condicao = "horas_backlog_snapshot > 48 AND horas_backlog_snapshot <= 72"

    elif faixa_tempo == "72h+":
        condicao = "horas_backlog_snapshot > 72"

    df_sla = consultar(f"""
        SELECT *
        FROM backlog_atual
        WHERE {condicao}
    """)

    st.dataframe(df_sla, use_container_width=True)
    gerar_download(df_sla, "drill_sla")

    st.divider()

    st.subheader("📊 Backlog por Estado (Faixa de Tempo)")

    df["faixa"] = df["horas_backlog_snapshot"].apply(
        lambda x: (
            "0-24h" if x <= 24 else
            "24-48h" if x <= 48 else
            "48-72h" if x <= 72 else
            ">72h"
        )
    )

    tabela_estado = (
        df.groupby(["estado", "faixa"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    # garantir colunas
    for col in ["0-24h", "24-48h", "48-72h", ">72h"]:
        if col not in tabela_estado.columns:
            tabela_estado[col] = 0

    tabela_estado["Total"] = tabela_estado[
        ["0-24h", "24-48h", "48-72h", ">72h"]
    ].sum(axis=1)

    st.dataframe(tabela_estado, use_container_width=True)