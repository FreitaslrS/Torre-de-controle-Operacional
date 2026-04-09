import streamlit as st
import plotly.express as px
import pandas as pd

from core.repository import buscar_produtividade, buscar_pacotes_grandes, buscar_semanas_pacotes_grandes
from utils.theme import grafico_barra, aplicar_layout_padrao
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

    tab1, tab2 = st.tabs(["⚡ Produtividade", "📦 Pacotes Grandes"])

    with tab1:
        # =========================
        # 🎛️ FILTROS
        # =========================
        col1, col2, col3 = st.columns(3)

        data_inicio = col1.date_input("📅 Data início / 开始日期", value=None, key="prod_di")
        data_fim    = col2.date_input("📅 Data fim / 结束日期",    value=None, key="prod_df")

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

    with tab2:
        st.subheader("📦 Pacotes Grandes / 大件包裹")
        st.caption("Encomendas com prefixo AJG — itens de grande volume e peso")

        df_sem_pg = buscar_semanas_pacotes_grandes()
        if df_sem_pg.empty:
            st.warning("Sem dados. Importe um arquivo do tipo 'Pacotes Grandes'.")
        else:
            semanas_pg = [f"{r['semana']}/{r['ano']}" for _, r in df_sem_pg.iterrows()]
            sem_pg_sel = st.selectbox("Semana", semanas_pg, key="sem_pacotes_grandes")
            sem_pg, ano_pg = sem_pg_sel.split("/")
            ano_pg = int(ano_pg)

            df_pg = buscar_pacotes_grandes(semana=sem_pg, ano=ano_pg)

            if df_pg.empty:
                st.warning("Sem dados para a semana selecionada.")
            else:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("📦 Total Pacotes",  len(df_pg))
                col2.metric("🏋️ Peso Médio",     f"{df_pg['peso_kg'].mean():.1f} kg")
                col3.metric("📐 Volume Médio",   f"{df_pg['volume_m3'].mean():.2f} m³")
                col4.metric("✅ Entregues",
                    len(df_pg[df_pg["status"] == "Pedido entregue"])
                )

                st.divider()

                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    st.markdown("**Por Status**")
                    df_st_pg = df_pg.groupby("status").size().reset_index(name="qtd")
                    df_st_pg = df_st_pg.sort_values("qtd", ascending=False)
                    cores_pg = ["#0F172A"] + ["#16A34A"] * (len(df_st_pg) - 1)
                    fig_st = grafico_barra(df_st_pg, x="qtd", y="status", text="qtd")
                    fig_st.update_traces(marker_color=cores_pg)
                    fig_st.update_layout(yaxis=dict(autorange="reversed"))
                    st.plotly_chart(fig_st, use_container_width=True, key="pg_status")

                with col_g2:
                    st.markdown("**Por Estado**")
                    df_est_pg = df_pg.groupby("estado").size().reset_index(name="qtd")
                    df_est_pg = df_est_pg.sort_values("qtd", ascending=False)
                    cores_est = ["#0F172A"] + ["#16A34A"] * (len(df_est_pg) - 1)
                    fig_est_pg = grafico_barra(df_est_pg, x="estado", y="qtd", text="qtd")
                    fig_est_pg.update_traces(marker_color=cores_est)
                    st.plotly_chart(fig_est_pg, use_container_width=True, key="pg_estado")

                st.divider()
                st.markdown("**Tabela Detalhada**")
                tabela_padrao(df_pg[[
                    "waybill_mae", "cliente", "status",
                    "estado", "cidade", "produto", "peso_kg", "volume_m3"
                ]].rename(columns={
                    "waybill_mae": "Waybill",
                    "cliente":     "Cliente",
                    "status":      "Status",
                    "estado":      "Estado",
                    "cidade":      "Cidade",
                    "produto":     "Produto",
                    "peso_kg":     "Peso (kg)",
                    "volume_m3":   "Volume (m³)"
                }))
