import streamlit as st
import plotly.express as px
import pandas as pd

from core.repository import (
    buscar_produtividade,
    buscar_pacotes_grandes,
    buscar_semanas_pacotes_grandes,
    buscar_semanas_presenca,
    buscar_presenca_turno,
    buscar_presenca_diaria,
)
from utils.theme import grafico_barra, aplicar_layout_padrao
from utils.style import tabela_padrao, rodape_autoria, aplicar_css_global

# ── Paleta Produtividade ──────────────────────────────────────────────
COR_PRINCIPAL  = "#009640"   # Verde Anjun — cor dominante desta página
COR_SECUNDARIA = "#2B2D42"   # Navy — complementar
COR_APOIO      = "#053B31"   # Verde escuro — terciário
PALETA_PAGINA  = [COR_PRINCIPAL, COR_SECUNDARIA, COR_APOIO]

# Aliases mantidos para compatibilidade com o restante do código
COR_VERDE     = COR_PRINCIPAL
COR_AZUL      = COR_SECUNDARIA
COR_AZUL_GELO = COR_APOIO

color_dispositivo = {
    "Sorter Oval":   "#009640",
    "Sorter Linear": "#2B2D42",
    "Cubometro":     "#053B31"
}

color_turno = {
    "T1": "#009640",
    "T2": "#2B2D42",
    "T3": "#053B31"
}

map_traducao = {
    "Sorter Oval":   "Sorter Oval",
    "Sorter Linear": "Sorter Linear",
    "Cubometro":     "Cubômetro"
}


def render():
    aplicar_css_global()

    st.markdown("""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:0.5rem;">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
         stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
    </svg>
    <div>
        <h2 style="margin:0;font-size:20px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Produtividade</h2>
        <p style="margin:0;font-size:12px;color:#6b7280;font-family:'Montserrat',sans-serif;">Volume por turno e dispositivo</p>
    </div>
</div>
""", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["⚡ Produtividade", "📦 Pacotes Grandes", "👥 Presença e Eficiência"])

    with tab1:
        # =========================
        # 🎛️ FILTROS
        # =========================
        col1, col2, col3 = st.columns(3)

        data_inicio = col1.date_input("Data início", value=None, key="prod_di")
        data_fim    = col2.date_input("Data fim",    value=None, key="prod_df")

        if data_inicio and data_fim:
            df = buscar_produtividade(data_inicio, data_fim)
        else:
            df = buscar_produtividade()

        if df.empty:
            st.warning("Sem dados")
            return

        df["data"] = pd.to_datetime(df["data"]).dt.date

        turno = col3.selectbox("Turno", ["Todos", "T1", "T2", "T3"])
        if turno != "Todos":
            df = df[df["turno"] == turno]

        if df.empty:
            st.warning("Sem dados após filtros")
            return

        st.divider()

        # =========================
        # 📊 KPIs
        # =========================
        total = int(df["volumes"].sum())
        t1    = int(df[df["turno"] == "T1"]["volumes"].sum())
        t2    = int(df[df["turno"] == "T2"]["volumes"].sum())
        t3    = int(df[df["turno"] == "T3"]["volumes"].sum())

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total", total)
        col2.metric("🟢 T1", t1, f"{(t1/total*100):.1f}%" if total else "0%")
        col3.metric("🔵 T2", t2, f"{(t2/total*100):.1f}%" if total else "0%")
        col4.metric("⚪ T3", t3, f"{(t3/total*100):.1f}%" if total else "0%")

        st.divider()

        # =========================
        # 🥧 PIZZA — TURNO + DISPOSITIVO
        # =========================
        col_p1, col_p2 = st.columns(2)

        with col_p1:
            st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Por Turno</span>
</div>""", unsafe_allow_html=True)
            df_turno = df.groupby("turno")["volumes"].sum().reset_index()
            fig_pizza_turno = px.pie(
                df_turno, names="turno", values="volumes",
                color="turno", color_discrete_map=color_turno
            )
            fig_pizza_turno = aplicar_layout_padrao(fig_pizza_turno)
            st.plotly_chart(fig_pizza_turno, use_container_width=True)

        with col_p2:
            st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Por Dispositivo</span>
</div>""", unsafe_allow_html=True)
            df_disp = df.groupby("dispositivo")["volumes"].sum().reset_index()
            df_disp["nome"] = df_disp["dispositivo"].map(map_traducao).fillna(df_disp["dispositivo"])
            fig_pizza_disp = px.pie(
                df_disp, names="nome", values="volumes",
                color="dispositivo", color_discrete_map=color_dispositivo
            )
            fig_pizza_disp = aplicar_layout_padrao(fig_pizza_disp)
            st.plotly_chart(fig_pizza_disp, use_container_width=True)

        st.divider()

        # =========================
        # 📊 BARRA — HORA × DISPOSITIVO
        # =========================
        st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Produtividade por Hora (Dispositivos)</span>
</div>""", unsafe_allow_html=True)

        dispositivos = ["Sorter Oval", "Sorter Linear", "Cubometro"]

        df_bar = (
            df.groupby(["hora", "dispositivo"])["volumes"]
            .sum()
            .reset_index()
        )

        horas = pd.DataFrame({"hora": range(24)})
        base = horas.assign(key=1).merge(
            pd.DataFrame({"dispositivo": dispositivos, "key": 1}), on="key"
        ).drop("key", axis=1)
        df_bar = base.merge(df_bar, on=["hora", "dispositivo"], how="left").fillna(0)

        fig_bar = px.bar(
            df_bar, x="hora", y="volumes",
            color="dispositivo", barmode="stack",
            color_discrete_map=color_dispositivo,
            labels={"hora": "Hora", "volumes": "Volumes", "dispositivo": "Dispositivo"}
        )
        fig_bar.for_each_trace(lambda t: t.update(name=map_traducao.get(t.name, t.name)))
        fig_bar.update_xaxes(dtick=1)
        fig_bar = aplicar_layout_padrao(fig_bar)
        st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()

        # =========================
        # 📋 TABELA HORA × DISPOSITIVO
        # =========================
        st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18M15 3v18"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Resumo por Hora</span>
</div>""", unsafe_allow_html=True)

        df_tabela = (
            df.groupby(["hora", "dispositivo"])["volumes"]
            .sum()
            .unstack(fill_value=0)
            .reset_index()
        )
        for col in dispositivos:
            if col not in df_tabela.columns:
                df_tabela[col] = 0
        df_tabela.rename(columns=map_traducao, inplace=True)
        cols_disp = [map_traducao[d] for d in dispositivos if map_traducao[d] in df_tabela.columns]
        df_tabela["Total"] = df_tabela[cols_disp].sum(axis=1)
        df_tabela["hora"] = df_tabela["hora"].apply(lambda x: f"{int(x):02d}:00")
        df_tabela.rename(columns={"hora": "Hora"}, inplace=True)
        tabela_padrao(df_tabela)

        st.divider()

        # =========================
        # 🧑‍💼 TOP 10 CLIENTES
        # =========================
        df_cliente = (
            df.groupby("cliente")["volumes"]
            .sum()
            .reset_index()
            .sort_values("volumes", ascending=False)
        )
        df_top10 = df_cliente.head(10)

        col_c1, col_c2 = st.columns(2)

        with col_c1:
            st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/>
<path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Top 10 Clientes</span>
</div>""", unsafe_allow_html=True)
            cores = [COR_SECUNDARIA] + [COR_PRINCIPAL] * (len(df_top10) - 1)
            fig_cliente = px.bar(
                df_top10, x="volumes", y="cliente", orientation="h", text="volumes",
                labels={"volumes": "Volumes", "cliente": "Cliente"}
            )
            fig_cliente.update_traces(marker_color=cores, textposition="outside")
            fig_cliente = aplicar_layout_padrao(fig_cliente)
            st.plotly_chart(fig_cliente, use_container_width=True)

        with col_c2:
            st.markdown("""<div style="display:flex;align-items:center;gap:8px;margin:1rem 0 0.4rem;">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M3 15h18M9 3v18M15 3v18"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Produção por Cliente</span>
</div>""", unsafe_allow_html=True)
            df_cliente_fmt = df_cliente.copy()
            df_cliente_fmt.columns = ["Cliente", "Volumes"]
            tabela_padrao(df_cliente_fmt)

    with tab2:
        st.markdown("""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:0.5rem;">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
         stroke="#009640" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
        <polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/>
    </svg>
    <div>
        <h3 style="margin:0;font-size:16px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Pacotes Grandes</h3>
        <p style="margin:0;font-size:12px;color:#6b7280;font-family:'Montserrat',sans-serif;">Encomendas com prefixo AJG</p>
    </div>
</div>
""", unsafe_allow_html=True)
        st.caption("Encomendas com prefixo AJG — itens de grande volume e peso")

        df_sem_pg = buscar_semanas_pacotes_grandes()
        if df_sem_pg.empty:
            st.warning("Sem dados. Importe um arquivo do tipo 'Pacotes Grandes'.")
        else:
            semanas_pg = [
                f"{r['semana']}/{int(float(r['ano']))}"
                for _, r in df_sem_pg.iterrows()
                if pd.notna(r['ano']) and pd.notna(r['semana'])
            ]
            sem_pg_sel = st.selectbox("Semana", semanas_pg, key="sem_pacotes_grandes")
            sem_pg, ano_pg = sem_pg_sel.split("/")
            ano_pg = int(ano_pg)

            df_pg = buscar_pacotes_grandes(semana=sem_pg, ano=ano_pg)

            if df_pg.empty:
                st.warning("Sem dados para a semana selecionada.")
            else:
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("📦 Total Pacotes",  len(df_pg))
                col2.metric("🏋️ Peso Médio",     f"{df_pg['peso_kg'].mean():.1f} kg")
                col3.metric("📐 Volume Médio",   f"{df_pg['volume_m3'].mean():.2f} m³")
                col4.metric("✅ Entregues",
                    len(df_pg[df_pg["status"] == "Pedido entregue"])
                )

                st.divider()

                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    st.markdown("**Por Status**")
                    df_st_pg = df_pg.groupby("status").size().reset_index(name="qtd")
                    df_st_pg = df_st_pg.sort_values("qtd", ascending=False)
                    cores_pg  = [COR_SECUNDARIA] + [COR_PRINCIPAL] * (len(df_st_pg) - 1)
                    fig_st = grafico_barra(df_st_pg, x="qtd", y="status", text="qtd")
                    fig_st.update_traces(marker_color=cores_pg)
                    fig_st.update_layout(yaxis=dict(autorange="reversed"))
                    st.plotly_chart(fig_st, use_container_width=True, key="pg_status")

                with col_g2:
                    st.markdown("**Por Estado**")
                    df_est_pg = df_pg.groupby("estado").size().reset_index(name="qtd")
                    df_est_pg = df_est_pg.sort_values("qtd", ascending=False)
                    cores_est = [COR_SECUNDARIA] + [COR_PRINCIPAL] * (len(df_est_pg) - 1)
                    fig_est_pg = grafico_barra(df_est_pg, x="estado", y="qtd", text="qtd")
                    fig_est_pg.update_traces(marker_color=cores_est)
                    st.plotly_chart(fig_est_pg, use_container_width=True, key="pg_estado")

                st.divider()
                st.markdown("**Tabela Detalhada**")
                tabela_padrao(df_pg[[
                    "waybill_mae", "cliente", "status",
                    "estado", "cidade", "produto", "peso_kg", "volume_m3"
                ]].rename(columns={
                    "waybill_mae": "Waybill",
                    "cliente":     "Cliente",
                    "status":      "Status",
                    "estado":      "Estado",
                    "cidade":      "Cidade",
                    "produto":     "Produto",
                    "peso_kg":     "Peso (kg)",
                    "volume_m3":   "Volume (m³)"
                }))

    # ════════════════════════════════════════
    # TAB 3 — PRESENÇA E EFICIÊNCIA
    # ════════════════════════════════════════
    with tab3:
        st.markdown("""<div style="display:flex;align-items:center;gap:10px;margin-bottom:0.5rem;">
<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#009640"
     stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
<circle cx="9" cy="7" r="4"/>
<path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
<path d="M16 3.13a4 4 0 0 1 0 7.75"/>
</svg>
<span style="font-size:15px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Presença e Eficiência Operacional</span>
</div>""", unsafe_allow_html=True)

        df_sem_pres = buscar_semanas_presenca()

        if df_sem_pres.empty:
            st.warning("Sem dados. Importe a planilha de Presença na página de Importação.")
        else:
            col_f1, col_f2 = st.columns(2)
            opcoes_pres = [f"{r['semana']}/{int(r['ano'])}" for _, r in df_sem_pres.iterrows()]
            sem_pres = col_f1.selectbox("Semana", opcoes_pres, key="sem_pres")
            s_pres, a_pres = sem_pres.split("/")
            a_pres = int(a_pres)

            turno_pres = col_f2.selectbox("Turno", ["Todos", "T1", "T2", "T3"], key="turno_pres")

            df_turno  = buscar_presenca_turno(semana=s_pres, ano=a_pres)
            df_diario = buscar_presenca_diaria(semana=s_pres, ano=a_pres)

            if df_turno.empty:
                st.warning("Sem dados para a semana selecionada.")
            else:
                df_turno_f = df_turno[df_turno["turno"] == turno_pres] if turno_pres != "Todos" else df_turno.copy()

                # KPIs
                total_prod         = int(df_turno_f["produzido_turno"].sum())
                media_presenca     = round(df_turno_f["presenca_total"].mean(), 0)
                total_faltas_anjun = int(df_turno_f["faltas_anjun"].sum())
                total_faltas_temp  = int(df_turno_f["faltas_temporarios"].sum())
                perc_falta_med     = round(df_turno_f["perc_falta"].mean() * 100, 1) if df_turno_f["perc_falta"].notna().any() else 0

                col1, col2, col3, col4, col5 = st.columns(5)
                col1.metric("Produzido na semana",  f"{total_prod:,}")
                col2.metric("Presença média/dia",   int(media_presenca) if pd.notna(media_presenca) else 0)
                col3.metric("Faltas Anjun",          total_faltas_anjun)
                col4.metric("Faltas Temporários",    total_faltas_temp)
                col5.metric("% Absenteísmo médio",  f"{perc_falta_med}%")

                st.divider()

                col_g1, col_g2 = st.columns(2)

                with col_g1:
                    st.markdown("**Produção por Turno**")
                    df_prod_turno = (
                        df_turno_f.groupby("turno")["produzido_turno"]
                        .sum().reset_index()
                        .sort_values("produzido_turno", ascending=False)
                    )
                    cores_t = {"T1": COR_PRINCIPAL, "T2": COR_SECUNDARIA, "T3": COR_APOIO}
                    fig_pt = grafico_barra(df_prod_turno, x="turno", y="produzido_turno", text="produzido_turno")
                    fig_pt.update_traces(
                        marker_color=[cores_t.get(t, COR_PRINCIPAL) for t in df_prod_turno["turno"]],
                        hovertemplate="<b>%{x}</b><br>Produzido: %{y}<extra></extra>"
                    )
                    st.plotly_chart(fig_pt, use_container_width=True, key="fig_prod_turno_pres")

                with col_g2:
                    st.markdown("**Eficiência por Turno (vol/pessoa)**")
                    df_turno_f2 = df_turno_f.copy()
                    df_turno_f2["eficiencia"] = (
                        df_turno_f2["produzido_turno"] /
                        df_turno_f2["presenca_turno"].replace(0, pd.NA)
                    ).round(1)
                    df_ef = df_turno_f2.groupby("turno")["eficiencia"].mean().round(1).reset_index()
                    fig_ef = grafico_barra(df_ef, x="turno", y="eficiencia", text="eficiencia")
                    fig_ef.update_traces(marker_color=COR_SECUNDARIA)
                    fig_ef.update_layout(yaxis_title="Vol / pessoa")
                    st.plotly_chart(fig_ef, use_container_width=True, key="fig_efic_pres")

                st.divider()

                if not df_diario.empty:
                    st.markdown("**Evolução do Volume Diário por Cliente**")
                    df_diario["data"] = pd.to_datetime(df_diario["data"])
                    fig_vol = px.bar(
                        df_diario.melt(
                            id_vars=["data"],
                            value_vars=["vol_tfk", "vol_shein", "vol_d2d", "vol_kwai", "vol_b2c"],
                            var_name="cliente", value_name="volume"
                        ),
                        x="data", y="volume", color="cliente",
                        color_discrete_map={
                            "vol_tfk":   COR_PRINCIPAL,
                            "vol_shein": COR_SECUNDARIA,
                            "vol_d2d":   COR_APOIO,
                            "vol_kwai":  "#F0A202",
                            "vol_b2c":   "#DE121C",
                        },
                        labels={"data": "Data", "volume": "Volume", "cliente": "Cliente"}
                    )
                    fig_vol.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)",
                        margin=dict(t=10, b=0, l=0, r=0),
                        legend=dict(orientation="h", y=-0.15),
                        height=300
                    )
                    st.plotly_chart(fig_vol, use_container_width=True, key="fig_vol_cliente_pres")

                st.divider()

                st.markdown("**Custo de Diaristas por Dia**")
                df_custo = (
                    df_turno_f.groupby("data")["custo_diaristas"]
                    .sum().reset_index().sort_values("data")
                )
                df_custo["data_fmt"] = pd.to_datetime(df_custo["data"]).dt.strftime("%d/%m")
                fig_custo = grafico_barra(df_custo, x="data_fmt", y="custo_diaristas", text="custo_diaristas")
                fig_custo.update_traces(
                    marker_color=COR_PRINCIPAL,
                    texttemplate="R$ %{text:,.0f}",
                    hovertemplate="<b>%{x}</b><br>Custo: R$ %{y:,.0f}<extra></extra>"
                )
                fig_custo.update_layout(yaxis_title="R$")
                st.plotly_chart(fig_custo, use_container_width=True, key="fig_custo_pres")

                st.divider()

                st.markdown("**Detalhamento por Turno**")
                df_tab = df_turno_f[[
                    "data", "turno", "produzido_turno", "presenca_turno",
                    "anjun", "temporarios", "diaristas_presenciais",
                    "faltas_anjun", "faltas_temporarios", "perc_falta",
                    "custo_por_pedido", "custo_diaristas"
                ]].copy()
                df_tab["data"]             = pd.to_datetime(df_tab["data"]).dt.strftime("%d/%m/%Y")
                df_tab["perc_falta"]       = (df_tab["perc_falta"] * 100).round(1).astype(str) + "%"
                df_tab["custo_por_pedido"] = df_tab["custo_por_pedido"].apply(lambda x: f"R$ {x:.2f}" if pd.notna(x) else "-")
                df_tab["custo_diaristas"]  = df_tab["custo_diaristas"].apply(lambda x: f"R$ {x:,.0f}" if pd.notna(x) else "-")
                df_tab.columns = [
                    "Data", "Turno", "Produzido", "Presença",
                    "Anjun", "Temp.", "Diaristas",
                    "Faltas Anjun", "Faltas Temp.", "% Falta",
                    "Custo/Pedido", "Custo Diaristas"
                ]
                tabela_padrao(df_tab)

    rodape_autoria()
