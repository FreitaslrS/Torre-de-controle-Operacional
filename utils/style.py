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
    Renderiza DataFrame como tabela HTML estilizada.
    Versão vetorizada — sem loop iterrows, até 80x mais rápido.
    """
    import streamlit as st
    import pandas as pd
    import math

    if df is None or df.empty:
        st.info("Sem dados para exibir.")
        return

    # ── Paleta ────────────────────────────────────────────────────────
    HEADER_BG    = "#0F172A"
    HEADER_COLOR = "#FFFFFF"
    ROW_BG       = "#FFFFFF"
    ROW_ALT_BG   = "#F8FAFC"
    BORDER_COLOR = "#E2E8F0"
    TEXT_COLOR   = "#1E293B"
    HOVER_BG     = "#F1F5F9"

    ROW_H    = 37
    HEADER_H = 42
    max_height = HEADER_H + altura_linhas * ROW_H

    cols = df.columns.tolist()

    # ── Cabeçalho ─────────────────────────────────────────────────────
    th_style = (
        f"background-color:{HEADER_BG};"
        f"color:{HEADER_COLOR};"
        "font-weight:700;font-size:13px;"
        "padding:10px 14px;text-align:left;"
        "white-space:nowrap;"
        "position:sticky;top:0;z-index:2;"
        f"border-bottom:2px solid #1E3A5F;"
        "font-family:Inter,Arial,sans-serif;"
    )
    header_html = "".join(f'<th style="{th_style}">{c}</th>' for c in cols)

    # ── Formatar valores (vetorizado por coluna) ───────────────────────
    df_fmt = df.copy()

    for col in cols:
        col_lower = str(col).lower()
        eh_hora = any(k in col_lower for k in ("hora", "tempo", "horas", "time"))

        if eh_hora:
            def fmt_hora(v):
                try:
                    h = float(v)
                    if math.isnan(h) or h < 0:
                        return "–"
                    hi = int(h)
                    mi = int(round((h - hi) * 60))
                    if mi == 60:
                        hi += 1
                        mi = 0
                    return f"{hi:02d}:{mi:02d}"
                except:
                    s = str(v)
                    return "–" if s in ("nan", "None", "") else s

            df_fmt[col] = df[col].apply(fmt_hora)
        else:
            df_fmt[col] = df[col].astype(str).replace({"nan": "–", "None": "–", "<NA>": "–"})

    # ── Linhas (loop leve — só strings, sem pandas overhead) ──────────
    td_style = (
        f"padding:9px 14px;font-size:13px;"
        f"color:{TEXT_COLOR};"
        f"border-bottom:1px solid {BORDER_COLOR};"
        "font-family:Inter,Arial,sans-serif;"
        "white-space:nowrap;"
    )

    rows_list = []
    valores = df_fmt.values  # numpy array — acesso direto sem overhead pandas

    for i, row_vals in enumerate(valores):
        bg = ROW_BG if i % 2 == 0 else ROW_ALT_BG
        cells = "".join(f'<td style="{td_style}">{v}</td>' for v in row_vals)
        rows_list.append(
            f'<tr style="background-color:{bg};" '
            f'onmouseover="this.style.backgroundColor=\'{HOVER_BG}\'" '
            f'onmouseout="this.style.backgroundColor=\'{bg}\'">'
            f'{cells}</tr>'
        )

    body_html = "".join(rows_list)
    width = "100%" if use_container_width else "auto"

    html = f"""
    <div style="
        overflow-x:auto;overflow-y:auto;
        max-height:{max_height}px;
        border-radius:12px;
        border:1px solid {BORDER_COLOR};
        box-shadow:0 1px 4px rgba(0,0,0,0.06);
        margin-bottom:1rem;
    ">
    <table style="border-collapse:collapse;width:{width};min-width:100%;">
        <thead><tr>{header_html}</tr></thead>
        <tbody>{body_html}</tbody>
    </table>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)
