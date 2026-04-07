import streamlit as st
from core.repository import buscar_devolucoes
from utils.style import aplicar_css_global, tabela_padrao


def render():
    aplicar_css_global()

    st.title("🔁 Devoluções / 退货")

    df = buscar_devolucoes(2000)

    if df.empty:
        st.warning("Sem dados carregados.")
        return

    tabela_padrao(df)
