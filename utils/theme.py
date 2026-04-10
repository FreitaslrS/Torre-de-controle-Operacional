import plotly.express as px

# =========================
# PALETA ANJUN EXPRESS
# =========================
COR_PRIMARIA   = "#009640"   # Verde principal Anjun
COR_SECUNDARIA = "#053B31"   # Verde escuro
COR_DESTAQUE   = "#DE121C"   # Vermelho Anjun
COR_AMARELO    = "#F0A202"   # Amarelo Anjun
COR_NAVY       = "#2B2D42"   # Navy
COR_NEUTRA     = "#e2e8f0"   # Cinza claro

# Aliases mantidos para compatibilidade com as pages existentes
COR_VERDE = COR_PRIMARIA
COR_AZUL  = COR_SECUNDARIA
COR_GELO  = COR_NEUTRA

PALETA = [COR_PRIMARIA, COR_SECUNDARIA, COR_AMARELO, COR_DESTAQUE, COR_NAVY, COR_NEUTRA]


def aplicar_layout_padrao(fig):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Montserrat, Arial, sans-serif",
            size=11,
            color=COR_SECUNDARIA
        ),
        title=dict(
            font=dict(size=15, family="Montserrat, Arial, sans-serif")
        ),
        xaxis=dict(
            showgrid=False,
            tickfont=dict(size=11)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="rgba(0,150,64,0.07)",
            tickfont=dict(size=11)
        ),
        legend=dict(
            orientation="h",
            y=-0.2,
            font=dict(size=11)
        ),
        margin=dict(l=0, r=0, t=30, b=0),
        hoverlabel=dict(
            bgcolor="#053B31",
            font_size=12,
            font_family="Montserrat, Arial, sans-serif",
            font_color="white"
        )
    )
    return fig


def grafico_barra(df, x, y, text=None, cor=None):
    fig = px.bar(
        df, x=x, y=y, text=text,
        color_discrete_sequence=[cor or COR_PRIMARIA]
    )
    fig.update_traces(textfont_size=11, textposition="outside")
    return aplicar_layout_padrao(fig)


def grafico_linha(df, x, y):
    fig = px.line(
        df, x=x, y=y,
        markers=True,
        color_discrete_sequence=[COR_PRIMARIA]
    )
    return aplicar_layout_padrao(fig)


def grafico_pizza(df, names, values, color=None, color_map=None):
    fig = px.pie(
        df, names=names, values=values,
        color=color,
        color_discrete_map=color_map,
        color_discrete_sequence=PALETA
    )
    fig.update_traces(textfont_size=11)
    return aplicar_layout_padrao(fig)