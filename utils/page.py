def pagina(titulo, subtitulo):
    import streamlit as st
    from utils.style import aplicar_css_global

    aplicar_css_global()
    st.title(titulo)
    st.caption(subtitulo)
    st.divider()