import streamlit as st
import os
from core.database import inicializar_banco

try:
    inicializar_banco()
except Exception as e:
    import streamlit as st
    st.warning(f"⚠️ Banco de dados indisponível no momento: {e}")

import pages.home as home
import pages.backlog as backlog
import pages.backlog_historico as backlog_historico
import pages.produtividade as produtividade
import pages.devolucoes as devolucoes
import pages.importacao as importacao
import pages.tempo_processamento as tempo_processamento
import pages.health_check as health_check

st.markdown("""
<style>
/* ── Esconde sidebar e botões de expand/collapse ── */
section[data-testid="stSidebar"],
button[data-testid="baseButton-headerNoPadding"],
[data-testid="collapsedControl"] {
    display: none !important;
}
/* ── Ajusta padding do conteúdo principal (sem sidebar) ── */
.block-container {
    padding-left: 3rem !important;
    padding-right: 3rem !important;
    max-width: 1400px !important;
}
</style>
""", unsafe_allow_html=True)

# 🔥 BASE DIR (pra não dar erro de caminho)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ===== CSS DARK =====
def load_css_dark():
    path = os.path.join(BASE_DIR, "assets", "style_dark.css")
    with open(path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ===== CSS LIGHT =====
def load_css_light():
    path = os.path.join(BASE_DIR, "assets", "style_light.css")
    with open(path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ===== CONFIG =====
st.set_page_config(page_title="Control Tower", layout="wide")

if "page" not in st.session_state:
    st.session_state.page = "home"

# 🔥 DARK MODE (toggle)
if "tema" not in st.session_state:
    st.session_state.tema = False

col_tema, _ = st.columns([1, 8])
with col_tema:
    tema = st.toggle("🌙 Dark", value=st.session_state.tema, key="toggle_tema")
    st.session_state.tema = tema

if tema:
    st.markdown('<body data-theme="dark">', unsafe_allow_html=True)
else:
    st.markdown('<body data-theme="light">', unsafe_allow_html=True)

if tema:
    load_css_dark()
else:
    load_css_light()

# 🔥 FORÇA CSS POR ÚLTIMO (GANHA DE TUDO)
from utils.style import aplicar_css_global
aplicar_css_global()

# ===== ROTEAMENTO =====
page = st.session_state.page

# Botão ← Home em todas as páginas (exceto home)
if page != "home":
    st.markdown("""
    <style>
    div[data-testid="stButton"][id="btn_voltar_home"] > button,
    div[data-testid="stButton"]:has(button[kind="secondary"]) > button {
        background: transparent !important;
    }
    </style>
    """, unsafe_allow_html=True)
    col_back, _ = st.columns([1, 8])
    with col_back:
        if st.button("← Home", key="btn_voltar_home"):
            st.session_state.page = "home"

if page == "home":
    home.render()

elif page == "backlog":
    backlog.render()

elif page == "historico":
    backlog_historico.render()

elif page == "produtividade":
    produtividade.render()

elif page == "tempo":
    tempo_processamento.render()

elif page == "health_check":
    health_check.render()

elif page == "devolucoes":
    devolucoes.render()

elif page == "importacao":
    importacao.render()