def aplicar_css_global():
    import streamlit as st
    st.markdown("""
    <style>
    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
    }
    </style>
    """, unsafe_allow_html=True)


def rodape_autoria():
    import streamlit as st
    st.markdown("""
    <div style="
        margin-top: 3rem;
        padding-top: 0.8rem;
        border-top: 1px solid rgba(0,0,0,0.08);
        text-align: center;
        font-family: 'Montserrat', sans-serif;
        font-size: 10px;
        color: #9CA3AF;
        letter-spacing: 0.5px;
    ">
        © 2026 Samuel Freitas — Torre de Controle. Todos os direitos reservados.
    </div>
    """, unsafe_allow_html=True)


def tabela_padrao(df, use_container_width=True, altura_linhas=13):
    import streamlit as st
    import pandas as pd
    import math

    if df is None or df.empty:
        st.info("Sem dados para exibir.")
        return

    # ── Paleta Anjun ──────────────────────────────────────────────────
    HEADER_BG    = "#053B31"
    HEADER_COLOR = "#FFFFFF"
    ROW_BG       = "#FFFFFF"
    ROW_ALT_BG   = "#f4f9f5"
    BORDER_COLOR = "rgba(0,150,64,0.12)"
    TEXT_COLOR   = "#2B2D42"
    HOVER_BG     = "#f0faf4"

    ROW_H    = 37
    HEADER_H = 42
    max_height = HEADER_H + altura_linhas * ROW_H

    cols = df.columns.tolist()

    # ── Cabeçalho ─────────────────────────────────────────────────────
    th_style = (
        f"background-color:{HEADER_BG};"
        f"color:{HEADER_COLOR};"
        "font-weight:700;font-size:12px;"
        "padding:10px 14px;text-align:left;"
        "white-space:nowrap;"
        "position:sticky;top:0;z-index:2;"
        "border-bottom:2px solid #009640;"
        "font-family:'Montserrat',Arial,sans-serif;"
        "letter-spacing:0.3px;"
        "text-transform:uppercase;"
    )
    header_html = "".join(f'<th style="{th_style}">{c}</th>' for c in cols)

    # ── Formatar valores ───────────────────────────────────────────────
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

    # ── Linhas ────────────────────────────────────────────────────────
    td_style = (
        f"padding:9px 14px;font-size:12px;"
        f"color:{TEXT_COLOR};"
        f"border-bottom:1px solid {BORDER_COLOR};"
        "font-family:'Montserrat',Arial,sans-serif;"
        "white-space:nowrap;"
    )

    rows_list = []
    valores = df_fmt.values

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
        box-shadow:0 1px 4px rgba(0,150,64,0.08);
        margin-bottom:1rem;
    ">
    <table style="border-collapse:collapse;width:{width};min-width:100%;">
        <thead><tr>{header_html}</tr></thead>
        <tbody>{body_html}</tbody>
    </table>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)