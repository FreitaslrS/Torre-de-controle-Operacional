import streamlit as st
import pandas as pd
import numpy as np

from core.repository import buscar_devolucoes, buscar_p90
from utils.style import tabela_padrao, aplicar_css_global

# Todos os estados do Brasil (tabela fixa)
TODOS_ESTADOS = [
    "AC", "AL", "AM", "AP", "BA", "CE", "DF", "ES", "GO",
    "MA", "MG", "MS", "MT", "PA", "PB", "PE", "PI", "PR",
    "RJ", "RN", "RO", "RR", "RS", "SC", "SE", "SP", "TO"
]


def render():
    aplicar_css_global()

    st.markdown("## 🔁 Devoluções / 退货")

    tab1, tab2 = st.tabs(["📋 Devoluções", "📊 P90"])

    # ========================
    # TAB 1 — DEVOLUÇÕES
    # ========================
    with tab1:
        df = buscar_devolucoes(2000)

        if df.empty:
            st.warning("Sem dados carregados.")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("Total", len(df))
            col2.metric("Clientes", df["cliente"].nunique())
            col3.metric("Estados", df["estado"].nunique())
            st.divider()
            tabela_padrao(df)

    # ========================
    # TAB 2 — P90
    # ========================
    with tab2:
        st.subheader("📊 P90 — Tempo de Devolução (Percentil 90)")
        st.caption("Dias corridos da criação do pedido até recebimento da devolução, para 90% dos casos")

        ano_atual = pd.Timestamp.now().year
        ano = st.selectbox("Ano / 年份", [ano_atual, ano_atual - 1], index=0)

        df_p90 = buscar_p90(ano=ano)

        if df_p90.empty:
            st.warning("Sem dados de P90. Importe um arquivo 'Devolução - P90'.")
            return

        # Semanas disponíveis ordenadas
        semanas = sorted(df_p90["semana"].unique())

        # Pivot: linhas = estados, colunas = semanas
        pivot = df_p90.pivot_table(
            index="estado",
            columns="semana",
            values="p90_dias",
            aggfunc="mean"
        ).round(1)

        # YTD — percentil 90 ponderado por qtd_pedidos por estado
        ytd_list = []
        for estado, grupo in df_p90.groupby("estado"):
            todos_dias = grupo["p90_dias"].repeat(grupo["qtd_pedidos"].astype(int))
            if len(todos_dias) > 0:
                ytd_val = round(float(np.percentile(todos_dias, 90)), 1)
            else:
                ytd_val = None
            ytd_list.append({"estado": estado, "YTD": ytd_val})

        df_ytd = pd.DataFrame(ytd_list).set_index("estado")

        # Monta tabela com todos os estados fixos
        df_tabela = pd.DataFrame(index=TODOS_ESTADOS)
        df_tabela.index.name = "Estado"
        df_tabela = df_tabela.join(df_ytd)
        df_tabela = df_tabela.join(pivot)
        # Formata colunas numéricas antes do fillna
        if "YTD" in df_tabela.columns:
            df_tabela["YTD"] = df_tabela["YTD"].apply(
                lambda x: f"{x:.1f}" if pd.notna(x) else "-"
            )
        for col in semanas:
            if col in df_tabela.columns:
                df_tabela[col] = df_tabela[col].apply(
                    lambda x: f"{x:.1f}" if pd.notna(x) else "-"
                )
        df_tabela = df_tabela.fillna("-")
        df_tabela = df_tabela.reset_index()

        st.divider()

        # KPIs gerais
        col1, col2, col3 = st.columns(3)
        total_pedidos  = int(df_p90["qtd_pedidos"].sum())
        estados_ativos = df_p90["estado"].nunique()
        ytd_geral = round(float(np.percentile(
            df_p90["p90_dias"].repeat(df_p90["qtd_pedidos"].astype(int)), 90
        )), 1)

        col1.metric("📦 Total pedidos", total_pedidos)
        col2.metric("🗺️ Estados com dados", estados_ativos)
        col3.metric("📊 P90 Geral (YTD)", f"{ytd_geral} dias")

        st.divider()
        tabela_padrao(df_tabela)
