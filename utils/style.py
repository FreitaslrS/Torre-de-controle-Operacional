def aplicar_css_global():
    import streamlit as st

    st.markdown("""
    <style>

    /* 🔥 ATAQUE DIRETO NO DATAFRAME */
    div[data-testid="stDataFrame"] * {
        background-color: #0F172A !important;
        color: white !important;
    }

    /* 🔥 fallback (caso outra estrutura) */
    div[data-testid="stDataFrame"] div[role="columnheader"] {
        background-color: #0F172A !important;
        color: white !important;
    }

    /* 🔥 remove estilo antigo */
    thead tr th {
        background-color: #0F172A !important;
        color: white !important;
    }

    </style>
    """, unsafe_allow_html=True)