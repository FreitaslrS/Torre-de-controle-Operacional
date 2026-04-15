import logging
import streamlit as st
import os
from core.database import inicializar_banco

logger = logging.getLogger(__name__)

@st.cache_resource
def _init_banco():
    try:
        inicializar_banco()
    except Exception as e:
        logger.warning("Banco de dados indisponível na inicialização: %s", e)
        st.warning(f"⚠️ Banco de dados indisponível no momento: {e}")

_init_banco()

# Ping para acordar o Neon antes do usuário navegar (evita cold start)
@st.cache_data(ttl=300)
def _acordar_bancos():
    from core.database import consultar_backlog, consultar_operacional, consultar_historico, consultar_devolucoes, consultar_processamento, consultar_coletas
    for fn in [consultar_backlog, consultar_operacional, consultar_historico, consultar_devolucoes, consultar_processamento, consultar_coletas]:
        try:
            fn("SELECT 1")
        except Exception:
            pass

_acordar_bancos()

st.set_page_config(page_title="Control Tower", layout="wide")

st.markdown("""
<style>
section[data-testid="stSidebar"],
button[data-testid="baseButton-headerNoPadding"],
[data-testid="collapsedControl"] { display: none !important; }
.block-container { padding-left:3rem !important; padding-right:3rem !important; max-width:1400px !important; }
</style>
""", unsafe_allow_html=True)

import pages.home as _page_home
import pages.backlog as _page_backlog
import pages.backlog_historico as _page_historico
import pages.produtividade as _page_produtividade
import pages.tempo_processamento as _page_tempo
import pages.health_check as _page_health
import pages.devolucoes as _page_devolucoes
import pages.coletas as _page_coletas
import pages.importacao as _page_importacao

from utils.style import aplicar_css_global
aplicar_css_global()

if "page" not in st.session_state:
    st.session_state.page = "home"

page = st.session_state.page

if page != "home":
    col_back, col_mid, col_sair = st.columns([1, 7, 1])
    with col_back:
        if st.button("← Home", key="btn_voltar_home"):
            st.session_state.page = "home"
            st.rerun()
    if page == "importacao" and st.session_state.get("autenticado"):
        with col_sair:
            if st.button("Sair", key="btn_sair_importacao"):
                st.session_state.autenticado = False
                st.rerun()

if page == "home":
    _page_home.render()
elif page == "backlog":
    _page_backlog.render()
elif page == "historico":
    _page_historico.render()
elif page == "produtividade":
    _page_produtividade.render()
elif page == "tempo":
    _page_tempo.render()
elif page == "health_check":
    _page_health.render()
elif page == "devolucoes":
    _page_devolucoes.render()
elif page == "coletas":
    _page_coletas.render()
elif page == "importacao":
    _page_importacao.render()
