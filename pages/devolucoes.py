import streamlit as st
from core.repository import buscar_pedidos
from utils.style import tabela_padrao


def render():
    from utils.style import aplicar_css_global

    aplicar_css_global()

    st.markdown("## <i class='fas fa-undo'></i> Devoluções / 退货", unsafe_allow_html=True)

    from core.repository import buscar_devolucoes

    df = buscar_devolucoes(2000)

    if df.empty:
        st.warning("Sem dados carregados.")
        return

    tabela_padrao(df)