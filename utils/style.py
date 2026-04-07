from datetime import date, datetime, time
import math

import pandas as pd
import streamlit as st


def aplicar_css_global():
    return None


def _formatar_valor(col_name, valor):
    """
    Formata o valor de uma célula de acordo com o nome da coluna.
    Colunas com 'hora' ou 'tempo' no nome são tratadas como duração em horas
    e exibidas no formato  HH:MM  (ex: 23.79 → 23:47).
    Valores inválidos (nan, vazio, negativo) são exibidos como traço.
    """
    col_lower = str(col_name).lower()

    # detecta colunas de duração em horas
    eh_hora = any(k in col_lower for k in ("hora", "tempo", "horas", "time", "(h)"))

    if eh_hora:
        if isinstance(valor, str) and ":" in valor:
            return valor
        try:
            h = float(valor)
            if math.isnan(h) or h < 0:
                return "-"
            horas_int  = int(h)
            minutos    = int(round((h - horas_int) * 60))
            if minutos == 60:
                horas_int += 1
                minutos = 0
            return f"{horas_int:02d}:{minutos:02d}"
        except (ValueError, TypeError):
            s = str(valor)
            return s if s not in ("nan", "None", "", "NaT") else "-"

    if isinstance(valor, pd.Timestamp):
        if pd.isna(valor):
            return "-"
        if valor.time() == time.min:
            return valor.strftime("%d/%m/%Y")
        return valor.strftime("%d/%m/%Y %H:%M")

    if isinstance(valor, datetime):
        if valor.time() == time.min:
            return valor.strftime("%d/%m/%Y")
        return valor.strftime("%d/%m/%Y %H:%M")

    if isinstance(valor, date):
        return valor.strftime("%d/%m/%Y")

    # valor comum
    s = str(valor)
    return "-" if s in ("nan", "None", "", "NaT") else s


def tabela_padrao(df, use_container_width=True, altura_linhas=13):
    """
    Renderiza um DataFrame com o componente nativo do Streamlit:
    - Formatação automática de colunas de horas → HH:MM
    - Formatação automática de datas → DD/MM/AAAA ou DD/MM/AAAA HH:MM
    - Altura padronizada para manter scroll nativo
    """
    if df is None or df.empty:
        st.info("Sem dados para exibir.")
        return

    df_display = df.copy()

    # altura do scroll: ~13 linhas × 37px por linha + 42px do header
    ROW_H   = 37
    HEADER_H = 42
    max_height = HEADER_H + altura_linhas * ROW_H  # ≈ 523px

    for col in df_display.columns:
        df_display[col] = df_display[col].map(lambda valor, col=col: _formatar_valor(col, valor))

    st.dataframe(
        df_display,
        use_container_width=use_container_width,
        height=max_height,
        hide_index=True
    )
