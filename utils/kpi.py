def kpi_card(label, valor, total=None):
    import streamlit as st

    if total:
        perc = valor / total if total else 0

        if perc > 0.3:
            emoji = "🔴"
        elif perc > 0.15:
            emoji = "🟡"
        else:
            emoji = "🟢"

        st.metric(label, f"{emoji} {valor}")
    else:
        st.metric(label, valor)