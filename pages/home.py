import streamlit as st
from utils.style import aplicar_css_global
from core.database import consultar_backlog as consultar

@st.cache_data(ttl=600)
def carregar():
    return consultar("SELECT COUNT(*) as total FROM backlog_atual")

def render():
    aplicar_css_global()

    # =========================
    # 🎨 CSS GLOBAL
    # =========================
    st.markdown("""
    <style>

    .card {
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        transition: 0.3s;
        cursor: pointer;
    }

    /* 🌙 DARK MODE */
    body[data-theme="dark"] .card {
        background: linear-gradient(145deg, #111827, #1f2937);
        border: 1px solid #374151;
        color: #e5e7eb;
    }

    /* ☀️ LIGHT MODE */
    body[data-theme="light"] .card {
        background: #ffffff;
        border: 1px solid rgba(0,0,0,0.05);
        color: #111827;
    }

    .card:hover {
        transform: scale(1.05);
        border: 1px solid #16A34A;
        box-shadow: 0 0 15px rgba(22,163,74,0.4);
    }

    .icon {
        font-size: 40px;
        margin-bottom: 10px;
        color: #16A34A;
    }

    .title {
        font-size: 18px;
        font-weight: 600;
    }

    .subtitle {
        font-size: 14px;
        opacity: 0.7;
    }

    </style>
    """, unsafe_allow_html=True)

    # =========================
    # 🧠 HEADER
    # =========================
    st.markdown("""
    <h2 style='text-align:center;'>Anjun Express - BI de Operações</h2>
    <p style='text-align:center; opacity:0.7;'>运营BI</p>
    """, unsafe_allow_html=True)

    st.divider()

    # =========================
    # 🔥 FUNÇÃO CARD
    # =========================
    def card(icon, titulo, subtitulo, pagina):

        if st.button(
            f"{titulo}\n{subtitulo}",
            key=pagina,
            use_container_width=True
        ):
            st.session_state.page = pagina
            st.rerun()

        st.markdown(f"""
        <style>
        div[data-testid="stButton"][key="{pagina}"] button {{
            height: 160px;
            border-radius: 15px;
            border: none;
            font-size: 0px;
            position: relative;
        }}

        div[data-testid="stButton"][key="{pagina}"] button::before {{
            content: "{titulo}";
            display: block;
            font-size: 18px;
            font-weight: 600;
            margin-top: 20px;
            color: inherit;
        }}

        div[data-testid="stButton"][key="{pagina}"] button::after {{
            content: "{subtitulo}";
            display: block;
            font-size: 13px;
            opacity: 0.7;
        }}
        </style>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="position: relative; top: -130px; text-align:center;">
            <i class="{icon}" style="font-size:40px; color:#16A34A;"></i>
        </div>
        """, unsafe_allow_html=True)

    # =========================
    # 🧱 GRID
    # =========================
    col1, col2, col3 = st.columns(3)

    with col1:
        card("fas fa-box",
            "Backlog Atual / 当前积压",
            "Visão operacional atual",
            "backlog")

    with col2:
        card("fas fa-chart-line",
            "Backlog Histórico / 历史积压",
            "Análise histórica",
            "historico")

    with col3:
        card("fas fa-bolt",
            "Produtividade / 生产效率",
            "Volume por turno e cliente",
            "produtividade")

    col4, col5, col6 = st.columns(3)

    with col4:
        card("fas fa-clock",
            "Tempo de Processamento / 处理时效",
            "Tempo entre entrada e saída",
            "tempo")

    with col5:
        card("fas fa-undo",
            "Devoluções / 退货",
            "Pedidos devolvidos",
            "devolucoes")

    with col6:
        card("fas fa-file-upload",
            "Importação / 数据导入",
            "Upload de planilhas",
            "importacao")
