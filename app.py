import streamlit as st
import os
from core.database import inicializar_banco

inicializar_banco()

import pages.home as home
import pages.backlog as backlog
import pages.backlog_historico as backlog_historico
import pages.produtividade as produtividade
import pages.devolucoes as devolucoes
import pages.importacao as importacao
import pages.tempo_processamento as tempo_processamento

st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
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

# 🔥 FONT AWESOME (ícones)
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
""", unsafe_allow_html=True)

# 🔥 DARK MODE (toggle)
if "tema" not in st.session_state:
    st.session_state.tema = False

tema = st.sidebar.toggle("🌙 Dark Mode", value=st.session_state.tema)
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

# ===== SIDEBAR =====
def nav(nome, pagina, icon):
    is_active = st.session_state.page == pagina

    label = f"{icon}  {nome}"
    if is_active:
        label = f"👉 {icon} {nome}"

    if st.sidebar.button(label, use_container_width=True):
        st.session_state.page = pagina
        st.rerun()

st.sidebar.markdown("## 📊 Control Tower")
st.sidebar.markdown("---")

nav("Home / 首页", "home", "🏠")
nav("Backlog Atual / 当前积压", "backlog", "📦")
nav("Backlog Histórico / 历史积压", "historico", "📊")
nav("Produtividade / 生产效率", "produtividade", "⚡")
nav("Tempo / 处理时效", "tempo", "⏱️")
nav("Devoluções / 退货", "devolucoes", "🔁")
nav("Importação / 数据导入", "importacao", "📥")

# ===== ROTEAMENTO =====
page = st.session_state.page

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

elif page == "devolucoes":
    devolucoes.render()

elif page == "importacao":
    importacao.render()