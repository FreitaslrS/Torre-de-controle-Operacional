import streamlit as st
import plotly.express as px
import pandas as pd

from core.repository import buscar_produtividade
from utils.theme import aplicar_layout_padrao
from utils.style import aplicar_css_global, tabela_padrao

# =========================
# 🎨 CORES
# =========================
COR_VERDE = "#16A34A"
COR_AZUL = "#0F172A"
COR_AZUL_GELO = "#CBD5E1"

cores_empresa = [COR_VERDE, COR_AZUL, COR_AZUL_GELO]

color_dispositivo = {
    "Sorter Oval": COR_VERDE,
    "Sorter Linear": COR_AZUL,
    "Cubometro": COR_AZUL_GELO
}

color_turno = {
    "T1": COR_VERDE,
    "T2": COR_AZUL,
    "T3": COR_AZUL_GELO
}

map_traducao = {
    "Sorter Oval": "Sorter Oval / 环形分拣机",
    "Sorter Linear": "Sorter Linear / 直线分拣机",
    "Cubometro": "Cubômetro / 体积测量设备"
}

# =========================
# ⚡ CACHE
# =========================
@st.cache_data(ttl=300)
def carregar_dados(data_inicio=None, data_fim=None):
    return buscar_produtividade(data_inicio, data_fim)

@st.cache_data(ttl=300)
def preparar_dados(df):
    df["hora"] = df["hora"].astype("int8")
    df["data"] = pd.to_datetime(df["data"]).dt.date

    # turno otimizado (rápido)
    df["turno_real"] = "T3"
    df.loc[(df["hora"] >= 6) & (df["hora"] < 14), "turno_real"] = "T1"
    df.loc[(df["hora"] >= 14) & (df["hora"] < 21), "turno_real"] = "T2"

    return df

@st.cache_data(ttl=300)
def agrupar(df):
    df_turno = df.groupby("turno_real")["volumes"].sum().reset_index()
    df_bar = df.groupby(["hora", "dispositivo"])["volumes"].sum().reset_index()
    df_tabela = df.groupby(["hora", "dispositivo"])["volumes"].sum().unstack(fill_value=0)
    return df_turno, df_bar, df_tabela

@st.cache_data(ttl=300)
def agrupar_cliente(df):
    df_cliente = (
        df.groupby("cliente")["volumes"]
        .sum()
        .reset_index()
        .sort_values(by="volumes", ascending=False)
    )

    df_top10 = df_cliente.head(10)

    return df_cliente, df_top10

# =========================
# 🚀 RENDER
# =========================
def render():
    aplicar_css_global()

    st.markdown("## ⚡ Produtividade / 生产效率")

    df = None

    # =========================
    # 🎛️ FILTROS
    # =========================
    col1, col2, col3 = st.columns(3)

    with col1:
        data_inicio = st.date_input(
            "📅 Data início / 开始日期",
            value=None
        )

    with col2:
        data_fim = st.date_input(
            "📅 Data fim / 结束日期",
            value=None
        )

    if data_inicio and data_fim and data_inicio > data_fim:
        st.error("Data início não pode ser maior que a data fim.")
        return

    if data_inicio and data_fim:
        df = carregar_dados(data_inicio, data_fim)
    else:
        df = carregar_dados()

    with col3:
        turno = st.selectbox(
            "🕒 Turno / 班次",
            ["Todos", "T1", "T2", "T3"]
        )

    if df.empty:
        st.warning("Sem dados / 暂无数据")
        return

    df = preparar_dados(df)

    if turno != "Todos":
        df = df[df["turno_real"] == turno]

    if df.empty:
        st.warning("Sem dados após filtros / 筛选后无数据")
        return

    st.divider()

    # =========================
    # 📊 KPIs
    # =========================
    total = int(df["volumes"].sum())

    t1 = int(df[df["turno_real"] == "T1"]["volumes"].sum())
    t2 = int(df[df["turno_real"] == "T2"]["volumes"].sum())
    t3 = int(df[df["turno_real"] == "T3"]["volumes"].sum())

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("📦 Total / 总量", total)
    col2.metric("🟢 T1", t1, f"{(t1/total*100):.1f}%" if total else "0.0%")
    col3.metric("🔵 T2", t2, f"{(t2/total*100):.1f}%" if total else "0.0%")
    col4.metric("⚪ T3", t3, f"{(t3/total*100):.1f}%" if total else "0.0%")

    st.divider()

    # =========================
    # ⚡ AGRUPAMENTO
    # =========================
    df_turno, df_bar, df_tabela = agrupar(df)

    # =========================
    # 🥧 PIZZA
    # =========================
    st.subheader("🥧 Produtividade por Turno / 按班次效率")

    fig_pizza = px.pie(
        df_turno,
        names="turno_real",
        values="volumes",
        color="turno_real",
        color_discrete_map=color_turno
    )

    fig_pizza = aplicar_layout_padrao(fig_pizza)

    st.plotly_chart(fig_pizza, use_container_width=True)

    st.divider()

    # =========================
    # 📊 BARRA
    # =========================
    st.subheader("📊 Produtividade por Hora (Dispositivos) / 按小时设备效率")

    horas = pd.DataFrame({"hora": range(24)})
    dispositivos = ["Sorter Oval", "Sorter Linear", "Cubometro"]

    base = horas.assign(key=1).merge(
        pd.DataFrame({"dispositivo": dispositivos, "key": 1}),
        on="key"
    ).drop("key", axis=1)

    df_bar = base.merge(df_bar, on=["hora", "dispositivo"], how="left").fillna(0)

    fig_bar = px.bar(
        df_bar,
        x="hora",
        y="volumes",
        color="dispositivo",
        barmode="stack",
        color_discrete_map=color_dispositivo,
        labels={
            "hora": "Hora / 时间",
            "volumes": "Volumes / 数量",
            "dispositivo": "Dispositivo / 设备"
        }
    )

    fig_bar.for_each_trace(
        lambda t: t.update(name=map_traducao.get(t.name, t.name))
    )

    fig_bar.update_xaxes(dtick=1)

    fig_bar = aplicar_layout_padrao(fig_bar)

    st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    # =========================
    # 📋 TABELA
    # =========================
    st.subheader("📋 Resumo por Hora / 每小时汇总")

    df_tabela["Total"] = df_tabela.sum(axis=1)
    df_tabela.index = df_tabela.index.map(lambda x: f"{x:02d}:00")
    df_tabela.columns = df_tabela.columns.map(lambda x: map_traducao.get(x, x))

    df_tabela = df_tabela.reset_index().rename(columns={"hora": "Hora / 时间"})
    tabela_padrao(df_tabela)

    st.divider()

    # =========================
    # 🧑‍💼 PRODUTIVIDADE POR CLIENTE
    # =========================
    st.subheader("🧑‍💼 Top 10 Clientes / 前10客户")

    df_cliente, df_top10 = agrupar_cliente(df)

    fig_cliente = px.bar(
        df_top10,
        x="volumes",
        y="cliente",
        orientation="h",
        text="volumes"
    )

    # 🔥 aplica cores da empresa (cíclico)
    cores = ["#0F172A"] + ["#16A34A"] * (len(df_top10) - 1)

    fig_cliente.update_traces(marker_color=cores)

    fig_cliente.update_layout(
        xaxis_title="Volumes / 数量",
        yaxis_title="Cliente / 客户"
    )

    fig_cliente.update_traces(textposition="outside")

    fig_cliente = aplicar_layout_padrao(fig_cliente)

    st.plotly_chart(fig_cliente, use_container_width=True)

    st.divider()

    # =========================
    # 📋 TABELA CLIENTES
    # =========================
    st.subheader("📋 Produção por Cliente (Completo) / 客户完整列表")

    df_cliente_formatado = df_cliente.copy()
    df_cliente_formatado.columns = ["Cliente / 客户", "Volumes / 数量"]

    tabela_padrao(df_cliente_formatado)

