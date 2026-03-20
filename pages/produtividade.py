import streamlit as st
from core.repository import buscar_pedidos

def render():
    st.title("⚡ Produtividade")

    df = buscar_pedidos()

    if df.empty:
        st.warning("Sem dados")
        return

    total = len(df)

    st.metric("Total processado", total)

    st.dataframe(df)