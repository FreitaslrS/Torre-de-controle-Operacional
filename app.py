import streamlit as st
from core.database import inicializar_banco

st.set_page_config(page_title="Control Tower", layout="wide")

inicializar_banco()

import pages.home as home
import pages.backlog as backlog
import pages.backlog_historico as backlog_historico
import pages.produtividade as produtividade
import pages.devolucoes as devolucoes
import pages.importacao as importacao
import pages.tempo_processamento as tempo_processamento

if "page" not in st.session_state:
    st.session_state.page = "home"

# 🔥 DARK MODE (toggle)
if "tema" not in st.session_state:
    st.session_state.tema = False

tema = st.sidebar.toggle("🌙 Dark Mode", value=st.session_state.tema)
st.session_state.tema = tema

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
