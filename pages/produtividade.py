import streamlit as st
import plotly.express as px
import pandas as pd

from core.repository import buscar_produtividade
from utils.theme import aplicar_layout_padrao
from utils.style import tabela_padrao

COR_VERDE     = "#16A34A"
COR_AZUL      = "#0F172A"
COR_AZUL_GELO = "#CBD5E1"

color_dispositivo = {
    "Sorter Oval":   COR_VERDE,
    "Sorter Linear": COR_AZUL,
    "Cubometro":     COR_AZUL_GELO
}

color_turno = {
    "T1": COR_VERDE,
    "T2": COR_AZUL,
    "T3": COR_AZUL_GELO
}

map_traducao = {
    "Sorter Oval":   "Sorter Oval / 环形分拣机",
    "Sorter Linear": "Sorter Linear / 直线分拣机",
    "Cubometro":     "Cubômetro / 体积测量设备"
}


@st.cache_data(ttl=300)
def carregar_dados(data_inicio=None, data_fim=None):
    return buscar_produtividade(data_inicio, data_fim)


def render():
    from utils.style import aplicar_css_global
    aplicar_css_global()

    st.markdown("## ⚡ Produtividade / 生产效率")

    # =========================
    # 🎛️ FILTROS
    # =========================
    col1, col2, col3 = st.columns(3)

    data_inicio = col1.date_input("📅 Data início / 开始日期", value=None)
    data_fim    = col2.date_input("📅 Data fim / 结束日期",    value=None)

    if data_inicio and data_fim:
        df = carregar_dados(data_inicio, data_fim)
    else:
        df = carregar_dados()

    if df.empty:
        st.warning("Sem dados / 暂无数据")
        return

    df["data"] = pd.to_datetime(df["data"]).dt.date

    turno = col3.selectbox("🕒 Turno / 班次", ["Todos", "T1", "T2", "T3"])
    if turno != "Todos":
        df = df[df["turno"] == turno]

    if df.empty:
        st.warning("Sem dados após filtros / 筛选后无数据")
        return

    st.divider()

    # =========================
    # 📊 KPIs
    # =========================
    total = int(df["volumes"].sum())
    t1    = int(df[df["turno"] == "T1"]["volumes"].sum())
    t2    = int(df[df["turno"] == "T2"]["volumes"].sum())
    t3    = int(df[df["turno"] == "T3"]["volumes"].sum())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📦 Total / 总量", total)
    col2.metric("🟢 T1", t1, f"{(t1/total*100):.1f}%" if total else "0%")
    col3.metric("🔵 T2", t2, f"{(t2/total*100):.1f}%" if total else "0%")
    col4.metric("⚪ T3", t3, f"{(t3/total*100):.1f}%" if total else "0%")

    st.divider()

    # =========================
    # 🥧 PIZZA — TURNO + DISPOSITIVO
    # =========================
    col_p1, col_p2 = st.columns(2)

    with col_p1:
        st.subheader("🥧 Por Turno / 按班次")
        df_turno = df.groupby("turno")["volumes"].sum().reset_index()
        fig_pizza_turno = px.pie(
            df_turno, names="turno", values="volumes",
            color="turno", color_discrete_map=color_turno
        )
        fig_pizza_turno = aplicar_layout_padrao(fig_pizza_turno)
        st.plotly_chart(fig_pizza_turno, use_container_width=True)

    with col_p2:
        st.subheader("🥧 Por Dispositivo / 按设备")
        df_disp = df.groupby("dispositivo")["volumes"].sum().reset_index()
        df_disp["nome"] = df_disp["dispositivo"].map(map_traducao).fillna(df_disp["dispositivo"])
        fig_pizza_disp = px.pie(
            df_disp, names="nome", values="volumes",
            color="dispositivo", color_discrete_map=color_dispositivo
        )
        fig_pizza_disp = aplicar_layout_padrao(fig_pizza_disp)
        st.plotly_chart(fig_pizza_disp, use_container_width=True)

    st.divider()

    # =========================
    # 📊 BARRA — HORA × DISPOSITIVO
    # =========================
    st.subheader("📊 Produtividade por Hora (Dispositivos) / 按小时设备效率")

    dispositivos = ["Sorter Oval", "Sorter Linear", "Cubometro"]

    df_bar = (
        df.groupby(["hora", "dispositivo"])["volumes"]
        .sum()
        .reset_index()
    )

    # garante todas as 24 horas × todos os dispositivos
    horas = pd.DataFrame({"hora": range(24)})
    base = horas.assign(key=1).merge(
        pd.DataFrame({"dispositivo": dispositivos, "key": 1}), on="key"
    ).drop("key", axis=1)
    df_bar = base.merge(df_bar, on=["hora", "dispositivo"], how="left").fillna(0)

    fig_bar = px.bar(
        df_bar, x="hora", y="volumes",
        color="dispositivo", barmode="stack",
        color_discrete_map=color_dispositivo,
        labels={"hora": "Hora / 时间", "volumes": "Volumes / 数量", "dispositivo": "Dispositivo / 设备"}
    )
    fig_bar.for_each_trace(lambda t: t.update(name=map_traducao.get(t.name, t.name)))
    fig_bar.update_xaxes(dtick=1)
    fig_bar = aplicar_layout_padrao(fig_bar)
    st.plotly_chart(fig_bar, use_container_width=True)


    st.divider()

    # =========================
    # 📋 TABELA HORA × DISPOSITIVO
    # =========================
    st.subheader("📋 Resumo por Hora / 每小时汇总")

    df_tabela = (
        df.groupby(["hora", "dispositivo"])["volumes"]
        .sum()
        .unstack(fill_value=0)
        .reset_index()
    )
    for col in dispositivos:
        if col not in df_tabela.columns:
            df_tabela[col] = 0
    df_tabela.rename(columns=map_traducao, inplace=True)
    cols_disp = [map_traducao[d] for d in dispositivos if map_traducao[d] in df_tabela.columns]
    df_tabela["Total"] = df_tabela[cols_disp].sum(axis=1)
    df_tabela["hora"] = df_tabela["hora"].apply(lambda x: f"{int(x):02d}:00")
    df_tabela.rename(columns={"hora": "Hora / 时间"}, inplace=True)
    tabela_padrao(df_tabela)

    st.divider()

    # =========================
    # 🧑‍💼 TOP 10 CLIENTES
    # =========================
    df_cliente = (
        df.groupby("cliente")["volumes"]
        .sum()
        .reset_index()
        .sort_values("volumes", ascending=False)
    )
    df_top10 = df_cliente.head(10)

    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.subheader("🧑‍💼 Top 10 Clientes / 前10客户")
        cores = ["#0F172A"] + ["#16A34A"] * (len(df_top10) - 1)
        fig_cliente = px.bar(
            df_top10, x="volumes", y="cliente", orientation="h", text="volumes",
            labels={"volumes": "Volumes / 数量", "cliente": "Cliente / 客户"}
        )
        fig_cliente.update_traces(marker_color=cores, textposition="outside")
        fig_cliente = aplicar_layout_padrao(fig_cliente)
        st.plotly_chart(fig_cliente, use_container_width=True)

    with col_c2:
        st.subheader("📋 Produção por Cliente (Completo) / 客户完整列表")
        df_cliente_fmt = df_cliente.copy()
        df_cliente_fmt.columns = ["Cliente / 客户", "Volumes / 数量"]
        tabela_padrao(df_cliente_fmt)
