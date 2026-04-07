def filtros_padrao(df, com_data=False):
    import streamlit as st

    col1, col2 = st.columns(2)

    remover_estados = col1.multiselect(
        "Estados",
        options=sorted(df["estado"].dropna().unique())
    )

    remover_clientes = col2.multiselect(
        "Clientes",
        options=sorted(df["cliente"].dropna().unique())
    )

    faixa = st.selectbox(
        "Faixa de backlog",
        ["Todos", "0-24h", "24-48h", "48-72h", "72h+"]
    )

    if com_data:
        col3, col4 = st.columns(2)
        data_inicio = col3.date_input("Data início")
        data_fim = col4.date_input("Data fim")
    else:
        data_inicio, data_fim = None, None

    return remover_estados, remover_clientes, faixa, data_inicio, data_fim