import streamlit as st
from utils.style import aplicar_css_global

# SVGs inline — sem dependência de CDN
CARD_SVGS = {
    "backlog":       '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>',
    "historico":     '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "produtividade": '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    "tempo":         '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    "health_check":  '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>',
    "devolucoes":    '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.13"/></svg>',
    "importacao":    '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
}

CARDS = [
    ("backlog",       "Backlog Atual",     "Visão operacional em tempo real"),
    ("historico",     "Backlog Histórico", "Análise e evolução histórica"),
    ("produtividade", "Produtividade",     "Volume por turno e dispositivo"),
    ("tempo",         "Tempo",             "SLA e tempo de processamento"),
    ("health_check",  "Health Check",      "Saúde operacional consolidada"),
    ("devolucoes",    "Devoluções",        "Pedidos devolvidos e P90"),
    ("importacao",    "Importação",        "Upload de planilhas"),
]

CARD_H = 160  # altura do card em px


def _card_html(pagina, titulo, subtitulo):
    svg = CARD_SVGS[pagina]
    return f"""
    <div style="
        background:#ffffff;
        border:1px solid rgba(0,150,64,0.15);
        border-top:3px solid #009640;
        border-radius:14px;
        padding:24px 20px 20px;
        text-align:center;
        height:{CARD_H}px;
        box-sizing:border-box;
        pointer-events:none;
    ">
        <div style="width:50px;height:50px;background:rgba(0,150,64,0.08);
                    border-radius:12px;display:flex;align-items:center;
                    justify-content:center;margin:0 auto 12px;">{svg}</div>
        <div style="font-size:14px;font-weight:700;color:#053B31;
                    margin-bottom:4px;font-family:'Montserrat',sans-serif;">{titulo}</div>
        <div style="font-size:11px;color:#6b7280;
                    font-family:'Montserrat',sans-serif;">{subtitulo}</div>
    </div>
    """


def _render_card(pagina, titulo, subtitulo):
    """Renderiza card visual + botão transparente por cima (opacity:0, mesmo tamanho)."""
    # 1. Card visual
    st.markdown(_card_html(pagina, titulo, subtitulo), unsafe_allow_html=True)
    # 2. Botão invisível (opacity:0) com mesma altura, puxado para cima para sobrepor o card
    clicked = st.button(titulo, key=f"card_{pagina}", use_container_width=True)
    if clicked:
        st.session_state.page = pagina
        st.rerun()


def render():
    aplicar_css_global()

    # CSS scoped via :has(.anjun-home-cards) — só aplica quando o marcador da home está no DOM
    # Impede conflito com outras páginas ao navegar
    st.markdown(f"""
    <style>
    /* Botões de card: invisíveis mas clicáveis — APENAS quando marcador home está no DOM */
    :has(.anjun-home-cards) div[data-testid="column"] div[data-testid="stButton"] > button {{
        opacity: 0 !important;
        height: {CARD_H}px !important;
        min-height: {CARD_H}px !important;
        margin-top: -{CARD_H}px !important;
        position: relative !important;
        z-index: 10 !important;
        cursor: pointer !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
    }}
    :has(.anjun-home-cards) div[data-testid="column"] div[data-testid="stButton"] > button:focus {{
        outline: none !important;
        box-shadow: none !important;
    }}
    /* Remove gap entre card HTML e botão */
    :has(.anjun-home-cards) div[data-testid="column"] div[data-testid="stMarkdownContainer"] {{
        margin-bottom: 0 !important;
    }}
    :has(.anjun-home-cards) div[data-testid="column"] div[data-testid="stButton"] {{
        margin-top: 0 !important;
    }}
    </style>
    <div class="anjun-home-cards" style="display:none"></div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center;margin-bottom:2rem;">
        <h2 style="color:#053B31;font-size:22px;font-weight:700;margin-bottom:4px;
                   font-family:'Montserrat',sans-serif;">
            Anjun Express — BI de Operações
        </h2>
        <p style="color:#6b7280;font-size:13px;font-family:'Montserrat',sans-serif;">
            Selecione um módulo para começar
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Linha 1: 3 cards
    cols1 = st.columns(3)
    for i in range(3):
        pagina, titulo, subtitulo = CARDS[i]
        with cols1[i]:
            _render_card(pagina, titulo, subtitulo)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Linha 2: 4 cards centralizados
    _, c1, c2, c3, c4, _ = st.columns([0.5, 1, 1, 1, 1, 0.5])
    for i, col in enumerate([c1, c2, c3, c4]):
        pagina, titulo, subtitulo = CARDS[3 + i]
        with col:
            _render_card(pagina, titulo, subtitulo)
