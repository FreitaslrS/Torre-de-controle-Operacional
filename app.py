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
/* ── Botão de recolher sidebar ── */
button[data-testid="baseButton-headerNoPadding"] span[data-testid="stIconMaterial"] {
    font-size: 0 !important;
    color: transparent !important;
    display: none !important;
}
button[data-testid="baseButton-headerNoPadding"]::after {
    content: "‹";
    font-size: 22px;
    font-weight: 700;
    color: rgba(255,255,255,0.75);
    line-height: 1;
}

/* ── Botão de expandir sidebar (quando recolhida) ── */
[data-testid="collapsedControl"] span[data-testid="stIconMaterial"] {
    font-size: 0 !important;
    color: transparent !important;
    display: none !important;
}
[data-testid="collapsedControl"] button::after {
    content: "›";
    font-size: 22px;
    font-weight: 700;
    color: #053B31;
    line-height: 1;
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

# ===== ÍCONES SVG ANJUN =====
ICONS = {
    "home":        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
    "backlog":     '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>',
    "historico":   '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "produtiv":    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    "tempo":       '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    "health":      '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>',
    "devolucoes":  '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.13"/></svg>',
    "importacao":  '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
}

def nav(nome, pagina, icon_key):
    is_active = st.session_state.page == pagina
    if st.sidebar.button(nome, key=pagina, use_container_width=True):
        st.session_state.page = pagina
        st.rerun()

# ===== SIDEBAR — CABEÇALHO =====
st.sidebar.markdown("""
<div style="padding:16px 12px 8px;">
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
        <div style="width:30px;height:30px;background:#009640;border-radius:7px;
                    display:flex;align-items:center;justify-content:center;
                    font-weight:700;font-size:15px;color:white;position:relative;">
            A
            <div style="position:absolute;top:3px;right:5px;width:5px;height:5px;
                        background:#DE121C;border-radius:50%;"></div>
        </div>
        <div>
            <div style="font-weight:700;font-size:13px;color:white;line-height:1.2;">Anjun Express</div>
            <div style="font-size:9px;color:rgba(255,255,255,0.45);letter-spacing:1.2px;
                        text-transform:uppercase;">Torre de Controle</div>
        </div>
    </div>
</div>
<div style="border-top:1px solid rgba(255,255,255,0.08);margin:0 12px 12px;"></div>
""", unsafe_allow_html=True)

nav("Home",              "home",          "home")
nav("Backlog Atual",     "backlog",       "backlog")
nav("Backlog Histórico", "historico",     "historico")
nav("Produtividade",     "produtividade", "produtiv")
nav("Tempo",             "tempo",         "tempo")
nav("Health Check",      "health_check",  "health")
nav("Devoluções",        "devolucoes",    "devolucoes")
nav("Importação",        "importacao",    "importacao")

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
            st.rerun()

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