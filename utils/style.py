def aplicar_css_global():
    import streamlit as st

    st.markdown("""
    <style>

    /* Estilos globais da aplicação */
    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
    }

    </style>
    """, unsafe_allow_html=True)


def _formatar_valor(col_name, valor):
    """
    Formata o valor de uma célula de acordo com o nome da coluna.
    Colunas com 'hora' ou 'tempo' no nome são tratadas como duração em horas
    e exibidas no formato  HH:MM  (ex: 23.79 → 23:47).
    Valores inválidos (nan, vazio, negativo) são exibidos como traço.
    """
    import math

    col_lower = str(col_name).lower()

    # detecta colunas de duração em horas
    eh_hora = any(k in col_lower for k in ("hora", "tempo", "horas", "time"))

    if eh_hora:
        try:
            h = float(valor)
            if math.isnan(h) or h < 0:
                return "–"
            horas_int  = int(h)
            minutos    = int(round((h - horas_int) * 60))
            if minutos == 60:
                horas_int += 1
                minutos = 0
            return f"{horas_int:02d}:{minutos:02d}"
        except (ValueError, TypeError):
            return str(valor) if str(valor) not in ("nan", "None", "") else "–"

    # valor comum
    s = str(valor)
    return "–" if s in ("nan", "None", "") else s


def tabela_padrao(df, use_container_width=True, altura_linhas=13):
    """
    Renderiza um DataFrame como tabela HTML estilizada com:
    - Cabeçalho azul escuro (#0F172A)
    - Scroll vertical (≈13 linhas visíveis por padrão)
    - Scroll horizontal automático
    - Formatação automática de colunas de horas → HH:MM
    - Linhas alternadas (zebra) + hover
    """
    import streamlit as st
    import pandas as pd

    if df is None or df.empty:
        st.info("Sem dados para exibir.")
        return

    df_display = df.copy()

    # ── Paleta ─────────────────────────────────────────────────────────
    header_bg    = "#0F172A"
    header_color = "#FFFFFF"
    row_bg       = "#FFFFFF"
    row_alt_bg   = "#F8FAFC"
    border_color = "#E2E8F0"
    text_color   = "#1E293B"
    hover_bg     = "#F1F5F9"

    # altura do scroll: ~13 linhas × 37px por linha + 42px do header
    ROW_H   = 37
    HEADER_H = 42
    max_height = HEADER_H + altura_linhas * ROW_H  # ≈ 523px

    cols = df_display.columns.tolist()

    # ── Cabeçalho ──────────────────────────────────────────────────────
    header_cells = "".join(
        f'<th style="'
        f'background-color:{header_bg};'
        f'color:{header_color};'
        f'font-weight:700;'
        f'font-size:13px;'
        f'padding:10px 14px;'
        f'text-align:left;'
        f'white-space:nowrap;'
        f'position:sticky;top:0;z-index:2;'
        f'border-bottom:2px solid #1E3A5F;'
        f'font-family:Inter,Arial,sans-serif;'
        f'">{col}</th>'
        for col in cols
    )

    # ── Linhas ─────────────────────────────────────────────────────────
    rows_html = ""
    for i, (_, row) in enumerate(df_display.iterrows()):
        bg = row_bg if i % 2 == 0 else row_alt_bg
        cells = "".join(
            f'<td style="'
            f'padding:9px 14px;'
            f'font-size:13px;'
            f'color:{text_color};'
            f'border-bottom:1px solid {border_color};'
            f'font-family:Inter,Arial,sans-serif;'
            f'white-space:nowrap;'
            f'">{_formatar_valor(col, row[col])}</td>'
            for col in cols
        )
        rows_html += (
            f'<tr style="background-color:{bg};" '
            f'onmouseover="this.style.backgroundColor=\'{hover_bg}\'" '
            f'onmouseout="this.style.backgroundColor=\'{bg}\'">'
            f'{cells}</tr>'
        )

    width = "100%" if use_container_width else "auto"

    html = f"""
    <div style="
        overflow-x:auto;
        overflow-y:auto;
        max-height:{max_height}px;
        border-radius:12px;
        border:1px solid {border_color};
        box-shadow:0 1px 4px rgba(0,0,0,0.06);
        margin-bottom:1rem;
    ">
    <table style="
        border-collapse:collapse;
        width:{width};
        min-width:100%;
    ">
        <thead><tr>{header_cells}</tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)
