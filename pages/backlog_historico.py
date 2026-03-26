import streamlit as st
import plotly.express as px
import io

from core.repository import (
    buscar_backlog_historico,
    buscar_waybills_por_faixa_dias,
    consultar
)

COR_VERDE = "#16A34A"
COR_CINZA = "#6B7280"


def gerar_download(df):

    col1, col2 = st.columns(2)

    csv = df.to_csv(index=False).encode("utf-8")
    col1.download_button("⬇️ CSV", csv, "backlog.csv", "text/csv")

    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    col2.download_button(
        "⬇️ Excel",
        buffer.getvalue(),
        "backlog.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def render():

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
        st.plotly_chart(
            px.line(df_tempo, x="data_referencia", y="qtd", markers=True),
            use_container_width=True
        )

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
        st.plotly_chart(
            px.bar(df_estado.sort_values("qtd", ascending=False),
                   x="estado", y="qtd", text="qtd",
                   color_discrete_sequence=[COR_VERDE]),
            use_container_width=True
        )

    with col_g2:
        st.subheader("📊 Cliente")
        st.plotly_chart(
            px.bar(df_cliente.sort_values("qtd", ascending=False),
                   x="cliente", y="qtd", text="qtd",
                   color_discrete_sequence=[COR_VERDE]),
            use_container_width=True
        )

    # =========================
    # 📊 PRÓXIMO PONTO
    # =========================
    if df_proximo is not None:
        st.subheader("📊 Próximo Ponto / 下一站")
        st.plotly_chart(
            px.bar(df_proximo.sort_values("qtd", ascending=False),
                   x="proximo_ponto", y="qtd", text="qtd",
                   color_discrete_sequence=[COR_VERDE]),
            use_container_width=True
        )

    # =========================
    # 📊 TOP 10 PRÉ-ENTREGA 🔥
    # =========================
    st.subheader("📊 Top 10 Pré-entrega")

    df_pre_top10 = df_pre.sort_values("qtd", ascending=False).head(10)

    st.plotly_chart(
        px.bar(
            df_pre_top10,
            x="qtd",
            y="pre_entrega",
            orientation="h",
            text="qtd",
            color_discrete_sequence=[COR_CINZA]
        ),
        use_container_width=True
    )

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
    gerar_download(df_drill)

    st.divider()

    # =========================
    # ⏱️ DRILL SLA
    # =========================
    st.subheader("⏱️ Drill SLA")

    faixa_tempo = st.selectbox("Tempo backlog", ["24h+", "48h+", "72h+"])

    limite = 24 if faixa_tempo == "24h+" else 48 if faixa_tempo == "48h+" else 72

    df_sla = consultar(f"""
        SELECT *
        FROM backlog_atual
        WHERE horas_backlog_snapshot > {limite}
    """)

    st.dataframe(df_sla, use_container_width=True)
    gerar_download(df_sla)