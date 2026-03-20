import streamlit as st
from core.repository import buscar_pedidos


def render():
    st.title("🔁 Devoluções")

    df = buscar_pedidos()

    if df.empty:
        st.warning("Sem dados carregados.")
        return

    st.dataframe(df)