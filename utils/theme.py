import plotly.express as px

# =========================
# 🎨 CORES OFICIAIS
# =========================
COR_PRIMARIA = "#16A34A"   # verde principal
COR_SECUNDARIA = "#0F172A" # azul escuro
COR_TERCIARIA = "#CBD5E1"  # azul gelo

COR_ALERTA = "#0F172A"

PALETA = [
    COR_PRIMARIA,
    COR_SECUNDARIA,
    COR_TERCIARIA
]

# =========================
# 🎨 LAYOUT GLOBAL
# =========================
def aplicar_layout_padrao(fig):

    fig.update_layout(
        template="plotly_white",

        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",

        font=dict(
            family="Arial",
            size=12,
            color=COR_SECUNDARIA
        ),

        title=dict(
            font=dict(size=16)
        ),

        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor=COR_TERCIARIA),

        legend=dict(
            orientation="h",
            y=-0.2
        )
    )

    return fig


# =========================
# 📊 GRÁFICO BARRA
# =========================
def grafico_barra(df, x, y, text=None, cor=None):

    fig = px.bar(
        df,
        x=x,
        y=y,
        text=text,
        color_discrete_sequence=[cor or COR_PRIMARIA]
    )

    return aplicar_layout_padrao(fig)


# =========================
# 📊 GRÁFICO LINHA
# =========================
def grafico_linha(df, x, y):

    fig = px.line(
        df,
        x=x,
        y=y,
        markers=True,
        color_discrete_sequence=[COR_PRIMARIA]
    )

    return aplicar_layout_padrao(fig)


# =========================
# 🥧 GRÁFICO PIZZA
# =========================
def grafico_pizza(df, names, values, color=None, color_map=None):

    fig = px.pie(
        df,
        names=names,
        values=values,
        color=color,
        color_discrete_map=color_map,
        color_discrete_sequence=PALETA
    )

    return aplicar_layout_padrao(fig)