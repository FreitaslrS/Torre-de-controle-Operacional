def aplicar_css_global():
    import streamlit as st

    st.markdown("""
    <style>

    /* 🎯 SOMENTE HEADER */
    div[data-testid="stDataFrame"] div[role="columnheader"] {
        background-color: #0F172A !important;
        color: white !important;
        font-weight: 700 !important;
    }

    /* ❌ REMOVE QUALQUER FUNDO FORÇADO NAS LINHAS */
    div[data-testid="stDataFrame"] div[role="gridcell"] {
        background-color: transparent !important;
        color: inherit !important;
    }

    /* hover leve */
    div[data-testid="stDataFrame"] div[role="row"]:hover {
        background-color: rgba(22,163,74,0.08) !important;
    }

    </style>
    """, unsafe_allow_html=True)