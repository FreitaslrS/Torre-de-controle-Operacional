import streamlit as st
from utils.translations import TRANSLATIONS


IDIOMAS = {
    "🇧🇷 Português": "pt",
    "🇺🇸 English":   "en",
    "🇨🇳 中文":       "zh",
}


def get_lang() -> str:
    return st.session_state.get("idioma", "pt")


def t(chave: str) -> str:
    """Retorna o texto na língua ativa. Fallback para PT se não encontrado."""
    lang = get_lang()
    return TRANSLATIONS.get(chave, {}).get(lang) or TRANSLATIONS.get(chave, {}).get("pt", chave)


def render_seletor_idioma():
    """Renderiza o seletor de idioma no canto superior direito."""
    if "idioma" not in st.session_state:
        st.session_state.idioma = "pt"

    label_atual = next((k for k, v in IDIOMAS.items() if v == st.session_state.idioma), "🇧🇷 Português")

    col_esp, col_sel = st.columns([9, 1])
    with col_sel:
        escolha = st.selectbox(
            "lang",
            list(IDIOMAS.keys()),
            index=list(IDIOMAS.keys()).index(label_atual),
            label_visibility="collapsed",
            key="sel_idioma"
        )
        novo = IDIOMAS[escolha]
        if novo != st.session_state.idioma:
            st.session_state.idioma = novo
            st.rerun()
