import streamlit as st
from core.database import consultar

@st.cache_data(ttl=600)
def carregar():
    return consultar("""
        SELECT COUNT(*) as total
        FROM backlog_atual
    """)


def render():
    st.title("🚀 Torre de Controle Logística")

    df = carregar()

    if df.empty:
        st.warning("Sem dados carregados.")
        return

    total = int(df["total"].iloc[0]) if not df.empty else 0

    col1 = st.columns(1)[0]
    col1.metric("📦 Total Pedidos", total)