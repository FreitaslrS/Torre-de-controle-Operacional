import pandas as pd
import streamlit as st


def exibir_tabela(df, altura=400, coluna_total=None):
    """
    Exibe dataframe estilizado com:
    - Header azul escuro com texto branco
    - Scroll vertical
    - Zebra nas linhas
    - Hover
    - Coluna Total destacada
    - Formatação automática de colunas de tempo (hh:mm)
    """

    # =========================
    # 🛡️ PROTEÇÃO (não altera df original)
    # =========================
    df = df.copy()

    # =========================
    # ⏱️ FORMATADOR DE HORAS
    # =========================
    def formatar_horas(valor):
        if pd.isna(valor):
            return ""

        try:
            horas = int(valor)
            minutos = int((valor - horas) * 60)
            return f"{horas:02d}:{minutos:02d}"
        except:
            return valor

    # aplica automaticamente em colunas de tempo
    for col in df.columns:
        if "hora" in col.lower() or "tempo" in col.lower():
            df[col] = df[col].apply(formatar_horas)

    # =========================
    # 🎨 ESTILO
    # =========================
    def estilo_coluna_total(col):
        return [
            "color: #16A34A; font-weight: bold;"
            if coluna_total and col.name == coluna_total
            else ""
            for _ in col
        ]

    def estilo_primeira_coluna(df):
        styles = pd.DataFrame("", index=df.index, columns=df.columns)
        styles.iloc[:, 0] = "font-weight: 600;"
        return styles

    styled = (
        df.style
        .apply(estilo_coluna_total, axis=0)
        .apply(estilo_primeira_coluna, axis=None)
        .set_table_styles([
            {
                "selector": "th",
                "props": [
                    ("background-color", "#0F172A"),
                    ("color", "white !important"),
                    ("font-weight", "bold"),
                    ("text-align", "center"),
                    ("border-bottom", "2px solid #16A34A"),
                    ("padding", "10px"),
                ]
            },
            {
                "selector": "tbody tr:hover td",
                "props": [
                    ("background-color", "rgba(22, 163, 74, 0.08)")
                ]
            },
            {
                "selector": "tbody tr td",
                "props": [
                    ("text-align", "center"),
                    ("padding", "8px 12px"),
                    ("border-bottom", "1px solid rgba(15,23,42,0.07)"),
                ]
            },
            {
                "selector": "tbody tr:nth-child(even)",
                "props": [
                    ("background-color", "#f8fafc")
                ]
            }
        ])
        .hide(axis="index")
    )

    # =========================
    # 📦 SCROLL
    # =========================
    st.markdown(f"""
    <div style="overflow-y: auto; max-height: {altura}px;">
        {styled.to_html()}
    </div>
    """, unsafe_allow_html=True)