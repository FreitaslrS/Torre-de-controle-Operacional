import html
import math
import os
import streamlit as st
import pandas as pd


@st.cache_resource
def _carregar_css():
    css_path = os.path.join(os.path.dirname(__file__), "..", "assets", "style_light.css")
    with open(css_path, encoding="utf-8") as f:
        return f.read()


def fmt_numero(n):
    """Formata número inteiro com separador de milhar brasileiro (ponto)."""
    try:
        return f"{int(n):,}".replace(",", ".")
    except (ValueError, TypeError):
        return str(n)


def aplicar_css_global():
    st.markdown(f"<style>{_carregar_css()}</style>", unsafe_allow_html=True)
    st.markdown("""
    <style>
    div[data-testid="stDataFrame"] { border-radius: 12px; overflow: hidden; }
    </style>
    """, unsafe_allow_html=True)


def rodape_autoria():
    from utils.i18n import t  # local import — evita importação circular
    st.markdown(f"""
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
        {t("rodape.texto")}
    </div>
    """, unsafe_allow_html=True)


def _fmt_celula(v, col_lower):
    """Formata um valor de célula para exibição na tabela."""
    eh_hora = any(k in col_lower for k in ("hora", "tempo", "horas", "time"))

    if eh_hora:
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
        except (ValueError, TypeError):
            s = str(v)
            return "–" if s in ("nan", "None", "") else s

    # Nulo
    if pd.isna(v):
        return "–"

    s = str(v)
    if s in ("nan", "None", "<NA>", ""):
        return "–"

    # Tenta formatar como número
    try:
        f = float(s)
        if math.isnan(f):
            return "–"
        # Inteiro (ex: 497598 → 497.598)
        if f == int(f):
            return f"{int(f):,}".replace(",", ".")
        # Float com 1 casa decimal (ex: P90 50.0 → 50, 12.3 → 12,3)
        rounded = round(f, 1)
        if rounded == int(rounded):
            return f"{int(rounded):,}".replace(",", ".")
        return f"{rounded:.1f}".replace(".", ",")
    except (ValueError, OverflowError):
        return s


def tabela_padrao(df, use_container_width=True, altura_linhas=13):
    if df is None or df.empty:
        st.info("Sem dados para exibir.")
        return

    HEADER_BG    = "#053B31"
    HEADER_COLOR = "#FFFFFF"
    ROW_BG       = "#FFFFFF"
    ROW_ALT_BG   = "#f4f9f5"
    BORDER_COLOR = "rgba(0,150,64,0.12)"
    TEXT_COLOR   = "#2B2D42"
    HOVER_BG     = "#f0faf4"

    ROW_H      = 37
    HEADER_H   = 42
    max_height = HEADER_H + altura_linhas * ROW_H

    cols = df.columns.tolist()

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

    td_style = (
        "padding:9px 14px;font-size:12px;"
        f"color:{TEXT_COLOR};"
        f"border-bottom:1px solid {BORDER_COLOR};"
        "font-family:'Montserrat',Arial,sans-serif;"
        "white-space:nowrap;"
    )

    rows_list = []
    for i, row in enumerate(df.itertuples(index=False, name=None)):
        bg    = ROW_BG if i % 2 == 0 else ROW_ALT_BG
        cells = "".join(
            f'<td style="{td_style}">{html.escape(str(_fmt_celula(v, str(cols[j]).lower())))}</td>'
            for j, v in enumerate(row)
        )
        rows_list.append(
            f'<tr style="background-color:{bg};" '
            f'onmouseover="this.style.backgroundColor=\'{HOVER_BG}\'" '
            f'onmouseout="this.style.backgroundColor=\'{bg}\'">'
            f'{cells}</tr>'
        )

    body_html = "".join(rows_list)
    width     = "100%" if use_container_width else "auto"

    tabela_html = f"""
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

    st.markdown(tabela_html, unsafe_allow_html=True)
