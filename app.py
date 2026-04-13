import streamlit as st
import os
from core.database import inicializar_banco

@st.cache_resource
def _init_banco():
    try:
        inicializar_banco()
    except Exception as e:
        st.warning(f"⚠️ Banco de dados indisponível no momento: {e}")

_init_banco()

st.set_page_config(page_title="Control Tower", layout="wide")

st.markdown("""
<style>
section[data-testid="stSidebar"],
button[data-testid="baseButton-headerNoPadding"],
[data-testid="collapsedControl"] { display: none !important; }
.block-container { padding-left:3rem !important; padding-right:3rem !important; max-width:1400px !important; }
</style>
""", unsafe_allow_html=True)

from utils.style import aplicar_css_global
aplicar_css_global()

if "page" not in st.session_state:
    st.session_state.page = "home"

page = st.session_state.page

if page != "home":
    col_back, _ = st.columns([1, 8])
    with col_back:
        if st.button("← Home", key="btn_voltar_home"):
            st.session_state.page = "home"
            st.rerun()

if page == "home":
    import pages.home as _m; _m.render()
elif page == "backlog":
    import pages.backlog as _m; _m.render()
elif page == "historico":
    import pages.backlog_historico as _m; _m.render()
elif page == "produtividade":
    import pages.produtividade as _m; _m.render()
elif page == "tempo":
    import pages.tempo_processamento as _m; _m.render()
elif page == "health_check":
    import pages.health_check as _m; _m.render()
elif page == "devolucoes":
    import pages.devolucoes as _m; _m.render()
elif page == "coletas":
    import pages.coletas as _m; _m.render()
elif page == "importacao":
    import pages.importacao as _m; _m.render()
