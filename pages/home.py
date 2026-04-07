import streamlit as st
from utils.style import aplicar_css_global
from core.database import consultar_backlog as consultar

@st.cache_data(ttl=600)
def carregar():
    return consultar("SELECT COUNT(*) as total FROM backlog_atual")

def render():
    aplicar_css_global()

    # =========================
    # 🧠 HEADER
    # =========================
    st.title("Anjun Express - BI de Operações")
    st.caption("运营BI")

    st.divider()

    # =========================
    # 🔥 FUNÇÃO CARD
    # =========================
    def card(icon, titulo, subtitulo, pagina):

        if st.button(
            f"{icon} {titulo}\n\n{subtitulo}",
            key=pagina,
            use_container_width=True
        ):
            st.session_state.page = pagina
            st.rerun()

    # =========================
    # 🧱 GRID
    # =========================
    col1, col2, col3 = st.columns(3)

    with col1:
        card("📦",
            "Backlog Atual / 当前积压",
            "Visão operacional atual",
            "backlog")

    with col2:
        card("📊",
            "Backlog Histórico / 历史积压",
            "Análise histórica",
            "historico")

    with col3:
        card("⚡",
            "Produtividade / 生产效率",
            "Volume por turno e cliente",
            "produtividade")

    col4, col5, col6 = st.columns(3)

    with col4:
        card("⏱️",
            "Tempo de Processamento / 处理时效",
            "Tempo entre entrada e saída",
            "tempo")

    with col5:
        card("🔁",
            "Devoluções / 退货",
            "Pedidos devolvidos",
            "devolucoes")

    with col6:
        card("📥",
            "Importação / 数据导入",
            "Upload de planilhas",
            "importacao")
