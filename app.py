import streamlit as st
from core.database import inicializar_banco

inicializar_banco()

# IMPORTS DAS PÁGINAS
import pages.home as home
import pages.backlog as backlog
import pages.backlog_historico as backlog_historico
import pages.produtividade as produtividade
import pages.devolucoes as devolucoes
import pages.importacao as importacao

def load_css():
    with open("assets/style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

COR_PRIMARIA = "#16A34A"   # verde
COR_ALERTA = "#DC2626"     # vermelho
COR_NEUTRA = "#6B7280"     # cinza
COR_BACKGROUND = "#0F172A" # fundo escuro

# =========================
# ⚙️ CONFIG
# =========================
st.set_page_config(
    page_title="Control Tower",
    page_icon="📦",
    layout="wide"
)

# =========================
# 🎨 SIDEBAR PROFISSIONAL
# =========================
st.sidebar.markdown("## 📊 Control Tower")
st.sidebar.markdown("---")

menu = st.sidebar.radio(
    "Navegação",
    [
        "🏠 Home",
        "📦 Backlog Atual",
        "📊 Backlog Histórico",
        "⚡ Produtividade",
        "🔁 Devoluções",
        "📥 Importação"
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption("© Samuel Freitas Analytics ")

# =========================
# 🎯 ROTEAMENTO
# =========================
if menu == "🏠 Home":
    home.render()

elif menu == "📦 Backlog Atual":
    backlog.render()

elif menu == "📊 Backlog Histórico":
    backlog_historico.render()

elif menu == "⚡ Produtividade":
    produtividade.render()

elif menu == "🔁 Devoluções":
    devolucoes.render()

elif menu == "📥 Importação":
    importacao.render()