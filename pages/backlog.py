import streamlit as st
import plotly.express as px
import pandas as pd
import io
from core.repository import (
    buscar_backlog_resumo,
    buscar_backlog_paginado,
    buscar_backlog_por_estado,
    buscar_backlog_por_cliente,
    buscar_top10_pre_entrega,
    buscar_backlog_por_proximo_ponto
)
from utils.theme import grafico_barra, aplicar_layout_padrao
from utils.style import tabela_padrao

# ── Paleta Backlog Atual ──────────────────────────────────────────────
COR_PRINCIPAL  = "#009640"   # Verde Anjun — cor dominante desta página
COR_SECUNDARIA = "#053B31"   # Verde escuro — destaque (1ª barra)
COR_APOIO      = "#2B2D42"   # Navy — elementos neutros
PALETA_PAGINA  = [COR_PRINCIPAL, COR_SECUNDARIA, COR_APOIO]

def render():
    from utils.style import aplicar_css_global

    aplicar_css_global()

    st.markdown("""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:0.5rem;">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
         stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
    </svg>
    <div>
        <h2 style="margin:0;font-size:20px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Backlog Atual</h2>
        <p style="margin:0;font-size:12px;color:#6b7280;font-family:'Montserrat',sans-serif;">Monitoramento em tempo real da operação</p>
    </div>
</div>
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
    st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Filtros</span>
</div>""", unsafe_allow_html=True)

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
    from utils.theme import grafico_barra

    df_estado_sorted = df_estado.sort_values("qtd", ascending=False)

    cores = [COR_SECUNDARIA] + [COR_PRINCIPAL] * (len(df_estado_sorted) - 1)

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

    cores = [COR_SECUNDARIA] + [COR_PRINCIPAL] * (len(df_cliente_sorted) - 1)

    fig_cliente = grafico_barra(
        df_cliente_sorted,
        x="cliente",
        y="qtd",
        text="qtd"
    )

    fig_cliente.update_traces(marker_color=cores)

    # =========================
    # 📊 EXIBE
    # =========================
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/><line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Estado</span>
</div>""", unsafe_allow_html=True)
        st.plotly_chart(fig_estado, use_container_width=True)

    with col_g2:
        st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
<path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Cliente</span>
</div>""", unsafe_allow_html=True)
        st.plotly_chart(fig_cliente, use_container_width=True)

    st.divider()

    # =========================
    # 📊 PRÓXIMO PONTO + PRÉ-ENTREGA
    # =========================
    col_pp1, col_pp2 = st.columns(2)

    with col_pp1:
        st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18M15 3v18"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Próximo Ponto</span>
</div>""", unsafe_allow_html=True)
        df_proximo_sorted = df_proximo.sort_values("qtd", ascending=False).reset_index(drop=True)
        df_proximo_fmt = df_proximo_sorted.copy()
        df_proximo_fmt.columns = ["Próximo Ponto / 下一站", "Qtd / 数量"]
        tabela_padrao(df_proximo_fmt)

    with col_pp2:
        st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6"/><path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18"/>
<path d="M4 22h16"/><path d="M18 2H6v7a6 6 0 0 0 12 0V2z"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Top 10 Pré-entrega</span>
</div>""", unsafe_allow_html=True)
        fig_pre = grafico_barra(df_pre, x="qtd", y="pre_entrega", text="qtd", cor=COR_PRINCIPAL)
        fig_pre.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_pre, use_container_width=True)

    st.divider()

    # ===========================
    # 📊 BACKLOG POR ESTADO (SLA)
    # ===========================
    st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Backlog por Estado (SLA)</span>
</div>""", unsafe_allow_html=True)

    from core.repository import buscar_sla_por_estado
    tabela_estado = buscar_sla_por_estado()
    tabela_padrao(tabela_estado)

    st.divider()

    # =========================
    # ⬇️ DOWNLOAD WAYBILLS
    # =========================
    st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
<polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Download Waybills em Backlog</span>
</div>""", unsafe_allow_html=True)

    df_detalhe_full = buscar_backlog_paginado(limit=100000)

    def formatar_tempo(h):
        if pd.isna(h):
            return "—"
        elif h <= 72:
            return f"{int(h)}h"
        else:
            dias = h / 24
            return f"{dias:.1f} dias"

    df_export = df_detalhe_full[[
        "waybill", "estado", "cliente", "cidade",
        "pre_entrega", "proximo_ponto", "horas_backlog_snapshot"
    ]].copy()
    df_export["tempo_backlog"] = df_export["horas_backlog_snapshot"].apply(formatar_tempo)
    df_export = df_export.drop(columns=["horas_backlog_snapshot"])
    df_export.columns = [
        "Waybill", "Estado", "Cliente", "Cidade",
        "Pré-entrega", "Próximo Ponto", "Tempo em Backlog"
    ]
    df_export = df_export.sort_values("Waybill")

    buffer = io.BytesIO()
    df_export.to_excel(buffer, index=False)
    st.download_button(
        label=f"⬇️ Baixar Excel ({len(df_export)} waybills)",
        data=buffer.getvalue(),
        file_name="backlog_waybills.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


# =========================
# 🔥 TELEGRAM
# =========================

import pandas as pd
import requests
import os

TOKEN = "8632831814:AAHU8LIDCP2iI6ZZ03j_F3i7y21XVunbTIM"
CHAT_ID = 8752000601


def enviar_telegram(texto):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": texto
    })

    print(requests.get(url).json())


def enviar_imagem(caminho):
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