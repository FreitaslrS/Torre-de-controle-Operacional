import streamlit as st
import os

import requests

from core.repository import (
    buscar_backlog_resumo,
    buscar_backlog_paginado,
    buscar_backlog_por_estado,
    buscar_backlog_por_cliente,
    buscar_top10_pre_entrega,
    buscar_backlog_por_proximo_ponto
)
from utils.theme import grafico_barra
from utils.style import aplicar_css_global, tabela_padrao

def render():
    aplicar_css_global()

    st.markdown("""
    ## <i class='fas fa-box'></i> Backlog Atual / 当前积压
    <p style='opacity:0.7'>Monitoramento em tempo real da operação / 实时运营监控</p>
    """, unsafe_allow_html=True)

    df_resumo = buscar_backlog_resumo()

    if df_resumo.empty:
        st.warning("Sem dados")
        return

    # =========================
    # 📊 KPIs
    # =========================
    total = df_resumo["qtd"].sum()
    b24 = df_resumo["b24"].sum()
    b48 = df_resumo["b48"].sum()
    b72 = df_resumo["b72"].sum()
    perc = (b72 / total * 100) if total else 0

    def cor_kpi(valor, total):
        perc_local = valor / total if total else 0
        if perc_local > 0.3:
            return "🔴"
        elif perc_local > 0.15:
            return "🟡"
        else:
            return "🟢"

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Total / 总计", total)
    col2.metric(">24h / 超过24小时", f"{cor_kpi(b24, total)} {b24}")
    col3.metric(">48h / 超过48小时", f"{cor_kpi(b48, total)} {b48}")
    col4.metric(">72h / 超过72小时", f"{cor_kpi(b72, total)} {b72}")
    col5.metric("% crítico / 关键比例", f"{perc:.1f}%")

    if perc > 30:
        st.error("🚨 Backlog crítico! / 积压严重！")
    elif perc > 15:
        st.warning("⚠️ Backlog em atenção / 积压需关注")
    else:
        st.success("✅ Operação controlada / 运营正常")

    st.divider()

    # =========================
    # 🎛️ FILTROS GLOBAIS
    # =========================
    st.subheader("🎛️ Filtros Globais / 全局筛选")

    col_f1, col_f2 = st.columns(2)

    remover_estados = col_f1.multiselect(
        "Remover Estados",
        options=sorted(df_resumo["estado"].unique())
    )

    remover_clientes = col_f2.multiselect(
        "Remover Clientes",
        options=sorted(df_resumo["cliente"].unique())
    )

    faixa = st.selectbox(
        "Filtro de Backlog",
        ["Todos", "0-24h", "24-48h", "48-72h", "72h+"]
    )

    # =========================
    # 📊 DADOS
    # =========================
    df_estado = buscar_backlog_por_estado(
        remover_estados=remover_estados,
        remover_clientes=remover_clientes,
        faixa=faixa
    )

    df_cliente = buscar_backlog_por_cliente(
        remover_clientes=remover_clientes,
        remover_estados=remover_estados,
        faixa=faixa
    )

    df_pre = buscar_top10_pre_entrega(faixa=faixa)
    df_proximo = buscar_backlog_por_proximo_ponto(faixa=faixa)

    # =========================
    # 📊 GRÁFICOS
    # =========================
    df_estado_sorted = df_estado.sort_values("qtd", ascending=False)

    cores = ["#0F172A"] + ["#16A34A"] * (len(df_estado_sorted) - 1)

    fig_estado = grafico_barra(
        df_estado_sorted,
        x="estado",
        y="qtd",
        text="qtd"
    )

    fig_estado.update_traces(
        marker_color=cores,
        hovertemplate="<b>%{x}</b><br>Volume: %{y}<extra></extra>"
    )

    df_cliente_sorted = df_cliente.sort_values("qtd", ascending=False)

    cores = ["#0F172A"] + ["#16A34A"] * (len(df_cliente_sorted) - 1)

    fig_cliente = grafico_barra(
        df_cliente_sorted,
        x="cliente",
        y="qtd",
        text="qtd"
    )

    fig_cliente.update_traces(marker_color=cores)

    df_proximo_sorted = df_proximo.sort_values("qtd", ascending=False)

    cores = ["#0F172A"] + ["#16A34A"] * (len(df_proximo_sorted) - 1)

    fig_proximo = grafico_barra(
        df_proximo_sorted,
        x="proximo_ponto",
        y="qtd",
        text="qtd"
    )

    fig_proximo.update_traces(marker_color=cores)

    # =========================
    # 📊 EXIBE
    # =========================
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("📊 Estado / 州")
        st.plotly_chart(fig_estado, use_container_width=True)

        if df_estado.empty:
            st.warning("Sem dados para o filtro selecionado.")
            return

        estado_select = st.selectbox(
            "Ver detalhe por estado",
            options=df_estado["estado"].tolist()
        )

    with col_g2:
        st.subheader("📊 Cliente / 客户")
        st.plotly_chart(fig_cliente, use_container_width=True)

    st.divider()

    st.subheader("📊 Próximo Ponto / 下一站")
    st.plotly_chart(fig_proximo, use_container_width=True)

    # =========================
    # 📦 DETALHE
    # =========================
    st.divider()

    st.subheader(f"📦 Detalhamento / 详细数据 - {estado_select}")

    df_detalhe = buscar_backlog_paginado(
        estados=[estado_select],
        faixa=faixa if faixa != "Todos" else None
    )

    tabela_padrao(df_detalhe)

    st.divider()

    # =========================
    # 🚚 PRÉ ENTREGA
    # =========================
    st.subheader("📊 Top 10 Pré-entrega / 预交付前10")

    fig_pre = grafico_barra(
        df_pre,
        x="qtd",
        y="pre_entrega",
        text="qtd",
        cor="#CBD5E1"
    )

    fig_pre.update_layout(yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_pre, use_container_width=True)

    st.divider()

    # ===========================
    # 📊 BACKLOG POR ESTADO (SLA)
    # ===========================

    st.subheader("📊 Backlog Atual por Estado (SLA)")

    df_detalhe_full = buscar_backlog_paginado(limit=100000)

    df_detalhe_full["faixa"] = df_detalhe_full["horas_backlog_snapshot"].apply(
        lambda x: (
            "0-24h" if x <= 24 else
            "24-48h" if x <= 48 else
            "48-72h" if x <= 72 else
            ">72h"
        )
    )

    tabela_estado = (
        df_detalhe_full.groupby(["estado", "faixa"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    for col in ["0-24h", "24-48h", "48-72h", ">72h"]:
        if col not in tabela_estado.columns:
            tabela_estado[col] = 0

    tabela_estado["Total"] = tabela_estado[
        ["0-24h", "24-48h", "48-72h", ">72h"]
    ].sum(axis=1)

    tabela_padrao(tabela_estado)

    st.divider()

    # =========================
    # 📦 TABELA
    # =========================
    if st.button("📦 Carregar pedidos / 加载订单 (modo pesado)"):
        df = buscar_backlog_paginado(limit=100)
        tabela_padrao(df)

    # ✅ BOTÃO CORRIGIDO
    if st.button("🚀 Enviar relatório no Telegram"):
        st.write("🚀 Enviando relatório...")
        gerar_e_enviar_relatorio(
            df_estado,
            df_cliente,
            fig_estado,
            fig_cliente,
            fig_proximo
        )


# =========================
# 🔥 TELEGRAM
# =========================

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def enviar_telegram(texto):
    if not TOKEN or not CHAT_ID:
        st.error("Configure TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID no .env.")
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": texto
    })

    print(requests.get(url).json())


def enviar_imagem(caminho):
    if not TOKEN or not CHAT_ID:
        st.error("Configure TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID no .env.")
        return

    url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"

    with open(caminho, "rb") as img:
        requests.post(url, files={"photo": img}, data={
            "chat_id": CHAT_ID
        })


def calcular_resumo(df_estado, df_cliente):
    total = df_cliente["qtd"].sum()

    top_clientes = df_cliente.sort_values("qtd", ascending=False).head(2)

    return {
        "total": int(total),
        "top1": f"{top_clientes.iloc[0]['cliente']}: {top_clientes.iloc[0]['qtd']}",
        "top2": f"{top_clientes.iloc[1]['cliente']}: {top_clientes.iloc[1]['qtd']}",
    }


def gerar_texto(df_cliente):
    from datetime import datetime

    data = datetime.now().strftime("%d/%m/%Y")

    total = df_cliente["qtd"].sum()

    top = df_cliente.sort_values("qtd", ascending=False).head(4)

    linhas = []
    for i, row in top.iterrows():
        perc = (row["qtd"] / total) * 100 if total else 0
        emoji = "🔴" if perc > 30 else "🟡" if perc > 15 else "🟢"

        linhas.append(f"{row['cliente']}: {int(row['qtd'])} (~{perc:.0f}%) {emoji}")

    concentracao = ((top.iloc[0]["qtd"] + top.iloc[1]["qtd"]) / total * 100) if total else 0

    analise = "🔴 MUITO concentrado" if concentracao > 70 else "🟡 moderado" if concentracao > 40 else "🟢 distribuído"

    texto = f"""
📊 BACKLOG AUTOMÁTICO
📅 {data}

📦 GERAL
Total: ≈{int(total)}

{chr(10).join(linhas)}

➡️ Top 2 = ~{concentracao:.0f}% do backlog
➡️ {analise}
"""

    return texto

def gerar_b2c(df_cliente):

    excluir = ["Kwai", "Shein", "Shein D2D", "Szanjun", "Temu D2D", "Temu W2D"]

    df_b2c = df_cliente[~df_cliente["cliente"].isin(excluir)]

    top_b2c = df_b2c.sort_values("qtd", ascending=False).head(5)

    linhas = []
    for _, row in top_b2c.iterrows():
        linhas.append(f"{row['cliente']}: {int(row['qtd'])}")

    return "\n".join(linhas)

def gerar_texto_completo(df_cliente):
    base = gerar_texto(df_cliente)
    b2c = gerar_b2c(df_cliente)

    return base + f"""

📦 B2C
{b2c}
"""

def enviar_excel(df):
    if not TOKEN or not CHAT_ID:
        st.error("Configure TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID no .env.")
        return


    caminho = "temp/waybills.xlsx"
    df.to_excel(caminho, index=False)

    url = f"https://api.telegram.org/bot{TOKEN}/sendDocument"

    with open(caminho, "rb") as file:
        requests.post(url, files={"document": file}, data={
            "chat_id": CHAT_ID
        })

def salvar_graficos(fig_estado, fig_cliente, fig_proximo):
    os.makedirs("temp", exist_ok=True)

    fig_estado.write_image("temp/estado.png")
    fig_cliente.write_image("temp/cliente.png")
    fig_proximo.write_image("temp/proximo.png")


def gerar_e_enviar_relatorio(df_estado, df_cliente, fig_estado, fig_cliente, fig_proximo):

    texto = gerar_texto_completo(df_cliente)

    salvar_graficos(fig_estado, fig_cliente, fig_proximo)

    enviar_telegram(texto)

    enviar_imagem("temp/estado.png")
    enviar_imagem("temp/cliente.png")
    enviar_imagem("temp/proximo.png")

    enviar_excel(df_cliente)
