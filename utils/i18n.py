import streamlit as st
from utils.translations import TRANSLATIONS

IDIOMAS = {
    "🇧🇷 Português": "pt",
    "🇺🇸 English":   "en",
    "🇨🇳 中文":       "zh",
}

_LANG_DEFAULT = "pt"


def get_lang() -> str:
    return st.session_state.get("idioma", _LANG_DEFAULT)


def t(chave: str) -> str:
    """Retorna o texto na língua ativa. Fallback para PT, depois para a própria chave."""
    entry = TRANSLATIONS.get(chave)
    if entry is None:
        return chave
    lang = st.session_state.get("idioma", _LANG_DEFAULT)
    return entry.get(lang) or entry.get(_LANG_DEFAULT) or chave


def render_seletor_idioma() -> None:
    """Renderiza o seletor de idioma no canto superior direito."""
    if "idioma" not in st.session_state:
        st.session_state.idioma = _LANG_DEFAULT

    labels = list(IDIOMAS.keys())
    lang_atual = st.session_state.idioma
    label_atual = next((k for k, v in IDIOMAS.items() if v == lang_atual), labels[0])

    _, col_sel = st.columns([9, 1])
    with col_sel:
        escolha = st.selectbox(
            "lang",
            labels,
            index=labels.index(label_atual),
            label_visibility="collapsed",
            key="sel_idioma",
        )
        novo = IDIOMAS[escolha]
        if novo != lang_atual:
            st.session_state.idioma = novo
            st.rerun()