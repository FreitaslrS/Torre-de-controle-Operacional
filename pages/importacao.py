import streamlit as st
import time
import pandas as pd
from datetime import date, timedelta
import os
from dotenv import load_dotenv

from utils.style import rodape_autoria, aplicar_css_global
from utils.i18n import t
from core.database import (
    executar_backlog, executar_historico, executar_operacional,
    consultar_historico, consultar_operacional, consultar_processamento,
    consultar_devolucoes, consultar_coletas, consultar_presenca,
    executar_processamento, executar_devolucoes, executar_coletas,
    executar_presenca,
)
from core.repository import salvar_log_importacao
from core.processar_arquivo import (
    importar_excel, importar_produtividade, limpar_base,
    importar_tempo_processamento, importar_devolucoes, importar_p90,
    importar_devolucao_monitoramento, importar_devolucao_enriquecida,
    importar_coletas_auto,
    importar_pacotes_grandes, importar_presenca,
    importar_shein_backlog, importar_presenca_historico_csv,
)

load_dotenv()


@st.cache_data(ttl=300)
def _carregar_historico():
    consultas = [
        (consultar_historico, """
            SELECT nome_arquivo, SUM(qtd) as registros, MAX(data_importacao) as data_importacao,
                   MAX(data_referencia) as data_referencia, 'Backlog' as tipo
            FROM pedidos_resumo GROUP BY nome_arquivo"""),
        (consultar_operacional, """
            SELECT nome_arquivo, COUNT(*) as registros, MAX(data_importacao) as data_importacao,
                   MAX(data) as data_referencia, 'Produtividade' as tipo
            FROM produtividade GROUP BY nome_arquivo"""),
        (consultar_processamento, """
            SELECT nome_arquivo, SUM(qtd_total) as registros, MAX(data_importacao) as data_importacao,
                   MAX(data) as data_referencia, 'Tempo Processamento' as tipo
            FROM tempo_processamento GROUP BY nome_arquivo"""),
        (consultar_devolucoes, """
            SELECT nome_arquivo, SUM(qtd_total) as registros, MAX(data_importacao) as data_importacao,
                   MAX(data_referencia) as data_referencia, 'Devolução - Monitoramento' as tipo
            FROM dev_sla_semanal
            WHERE nome_arquivo NOT LIKE '%+%'
            GROUP BY nome_arquivo"""),
        (consultar_operacional, """
            SELECT nome_arquivo, COUNT(*) as registros, MAX(data_importacao) as data_importacao,
                   CONCAT('Sem ', MAX(semana), '/', MAX(ano)) as data_referencia, 'Pacotes Grandes' as tipo
            FROM pacotes_grandes GROUP BY nome_arquivo"""),
        (consultar_coletas, """
            SELECT nome_arquivo, COUNT(*) as registros, MAX(data_importacao) as data_importacao,
                   MAX(data_referencia) as data_referencia,
                   CONCAT('Coletas — ', MAX(tipo)) as tipo
            FROM coletas GROUP BY nome_arquivo"""),
        (consultar_coletas, """
            SELECT nome_arquivo, COUNT(*) as registros, MAX(data_importacao) as data_importacao,
                   MAX(data_referencia) as data_referencia, 'Coletas — Itens Grandes' as tipo
            FROM coletas_grandes GROUP BY nome_arquivo"""),
        (consultar_coletas, """
            SELECT nome_arquivo, COUNT(*) as registros, MAX(data_importacao) as data_importacao,
                   MAX(data_referencia) as data_referencia, 'Coletas — Monitoramento Final' as tipo
            FROM coleta_final GROUP BY nome_arquivo"""),
        (consultar_devolucoes, """
            SELECT nome_arquivo, COUNT(*) as registros, MAX(data_importacao) as data_importacao,
                   MAX(data_referencia) as data_referencia, 'Devolução + Monitoramento' as tipo
            FROM dev_detalhado GROUP BY nome_arquivo"""),
        (consultar_devolucoes, """
            SELECT nome_arquivo, SUM(qtd_total) as registros, MAX(data_importacao) as data_importacao,
                   MAX(data_referencia) as data_referencia, 'Shein — Backlog Completo' as tipo
            FROM dev_shein_sla GROUP BY nome_arquivo"""),
        (consultar_presenca, """
            SELECT nome_arquivo, COUNT(*) as registros, MAX(data_importacao) as data_importacao,
                   CONCAT('Sem ', MAX(semana), '/', MAX(ano)) as data_referencia, 'Presença / Diário de Bordo' as tipo
            FROM presenca_turno GROUP BY nome_arquivo"""),
    ]
    dfs = []
    for fn, sql in consultas:
        try:
            df_item = fn(sql)
            if "data_importacao" in df_item.columns:
                df_item["data_importacao"] = pd.to_datetime(
                    df_item["data_importacao"], utc=True, errors="coerce"
                )
            dfs.append(df_item)
        except Exception:
            pass  # banco indisponível não derruba o histórico inteiro
    if not dfs:
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True).sort_values("data_importacao", ascending=False)


def _senha_configurada():
    """Retorna a senha do .env. Bloqueia acesso se não estiver configurada."""
    return os.getenv("SENHA_IMPORTACAO", "").strip()


_MAX_TENTATIVAS = 5


def verificar_senha():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False
    if "tentativas_senha" not in st.session_state:
        st.session_state.tentativas_senha = 0

    if st.session_state.autenticado:
        return True

    senha_correta = _senha_configurada()
    if not senha_correta:
        st.error(t("imp.bloqueada_env"))
        return False

    if st.session_state.tentativas_senha >= _MAX_TENTATIVAS:
        st.error(t("imp.acesso_bloqueado").format(n=_MAX_TENTATIVAS))
        return False

    st.markdown(f"""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem;">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
         stroke="#053B31" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
    </svg>
    <div>
        <h2 style="margin:0;font-size:20px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">{t("imp.area_restrita")}</h2>
        <p style="margin:0;font-size:12px;color:#6b7280;font-family:'Montserrat',sans-serif;">{t("imp.acesso_restrito")}</p>
    </div>
</div>
""", unsafe_allow_html=True)
    senha = st.text_input(t("imp.senha"), type="password")
    if st.button(t("imp.entrar")):
        if senha and senha == senha_correta:
            st.session_state.autenticado = True
            st.session_state.tentativas_senha = 0
            st.rerun()
        else:
            st.session_state.tentativas_senha += 1
            restantes = _MAX_TENTATIVAS - st.session_state.tentativas_senha
            if restantes > 0:
                st.error(t("imp.senha_incorreta").format(n=restantes))
            else:
                st.error(t("imp.acesso_bloqueado_final"))
    return False


# =========================
# 🚀 PROCESSAMENTO COM LOG DETALHADO
# =========================
def _extrair_qtd(resultado):
    """Extrai int de resultado que pode ser int ou dict."""
    if isinstance(resultado, dict):
        return resultado.get("registros", 0) or 0
    return resultado or 0


def _extrair_detalhe(resultado):
    """Extrai mensagem de detalhe do resultado."""
    if isinstance(resultado, dict):
        return resultado.get("detalhe", "")
    return ""


def processar_arquivo_individual(arquivo, data_ref, tipo_importacao, arquivo_secundario=None, arquivo_terciario=None):
    inicio = time.time()

    try:
        if tipo_importacao == "Backlog":
            resultado = importar_excel(arquivo, data_ref)

        elif tipo_importacao == "Produtividade":
            resultado = importar_produtividade(arquivo)

        elif tipo_importacao == "Tempo de Processamento":
            resultado = importar_tempo_processamento(arquivo)

        elif tipo_importacao == "Devolução":
            resultado = importar_devolucoes(arquivo, data_ref)

        elif tipo_importacao == "Devolução - P90":
            resultado = importar_p90(arquivo, data_ref)

        elif tipo_importacao == "Devolução - Monitoramento":
            resultado = importar_devolucao_monitoramento(arquivo, data_ref)

        elif tipo_importacao == "Devolução + Monitoramento":
            if arquivo_secundario is None:
                raise ValueError("Arquivo de Monitoramento não selecionado")
            resultado = importar_devolucao_enriquecida(arquivo, arquivo_secundario, data_ref)

        elif tipo_importacao == "Shein — Backlog Completo":
            if arquivo_secundario is None or arquivo_terciario is None:
                raise ValueError("Selecione os 3 arquivos: Insucesso LM, Folha e Monitoramento")
            resultado = importar_shein_backlog(arquivo, arquivo_secundario, arquivo_terciario, data_ref)

        elif tipo_importacao == "Coletas":
            resultado = importar_coletas_auto(arquivo, data_ref)

        elif tipo_importacao == "Pacotes Grandes":
            resultado = importar_pacotes_grandes(arquivo, data_ref)

        elif tipo_importacao == "Presença / Diário de Bordo":
            resultado = importar_presenca(arquivo)

        elif tipo_importacao == "Presença — Histórico CSV":
            resultado = importar_presenca_historico_csv(arquivo)

        else:
            raise ValueError("Tipo de importação inválido")

        status  = "Sucesso"
        qtd     = _extrair_qtd(resultado)
        detalhe = _extrair_detalhe(resultado)

    except Exception as e:
        qtd     = 0
        detalhe = ""
        status  = f"Erro: {type(e).__name__}: {e}"

    return {
        "arquivo": arquivo.name,
        "status":  status,
        "registros": qtd,
        "detalhe": detalhe,
        "tempo":   time.time() - inicio
    }

# =========================
# 🎯 TELA
# =========================
def render():

    aplicar_css_global()

    if not verificar_senha():
        return

    st.markdown(f"## {t('imp.titulo')}", unsafe_allow_html=True)

    _LIMITE_MB = 200
    arquivos = st.file_uploader(
        f"Selecione arquivos Excel ou CSV (máx. {_LIMITE_MB} MB por arquivo)",
        type=["xlsx", "xls", "csv"],
        accept_multiple_files=True
    )

    if "resultado_importacao" not in st.session_state:
        st.session_state.resultado_importacao = None
        st.session_state.total_importado = 0

    tipo_importacao = st.selectbox(
        t("imp.tipo"),
        [
            "Backlog",
            "Produtividade",
            "Tempo de Processamento",
            "Devolução + Monitoramento",
            "Devolução - Monitoramento",
            "Shein — Backlog Completo",
            "Coletas",
            "Pacotes Grandes",
            "Presença / Diário de Bordo",
            "Presença — Histórico CSV",
        ]
    )

    # Uploader secundário para "Devolução + Monitoramento"
    if tipo_importacao == "Coletas":
        st.info(
            "O sistema detecta automaticamente o tipo pelo número de colunas do arquivo:\n"
            "- **Monitoramento de caminhões** (≥ 19 colunas) → grava descarregamento **e** saída ao mesmo tempo\n"
            "- **Monitoramento Final** (13 colunas) → coleta_final\n"
            "- **Itens Grandes** (10 colunas) → coletas_grandes"
        )

    arquivo_monitor_secundario = None
    if tipo_importacao == "Devolução + Monitoramento":
        st.info(t("imp.dois_arquivos_info"))
        arquivo_monitor_secundario = st.file_uploader(
            t("imp.selecione_monitoramento"),
            type=["xlsx", "xls"],
            key="uploader_monitor_sec"
        )

    arquivo_folha_shein   = None
    arquivo_monitor_shein = None
    if tipo_importacao == "Shein — Backlog Completo":
        st.info("Selecione os 3 arquivos: o principal (Insucesso LM) no uploader acima + os dois abaixo.")
        arquivo_folha_shein = st.file_uploader(
            "Folha de Devolução (Shein)",
            type=["xlsx", "xls"],
            key="uploader_folha_shein"
        )
        arquivo_monitor_shein = st.file_uploader(
            "Monitoramento de Pontualidade (Shein)",
            type=["xlsx", "xls"],
            key="uploader_monitor_shein"
        )

    # ========================
    # 📅 SELETOR DE DATA / SEMANA
    # ========================
    TIPOS_SEMANAIS = {
        "Devolução", "Devolução - P90", "Devolução + Monitoramento",
        "Pacotes Grandes", "Shein — Backlog Completo",
    }

    if tipo_importacao in TIPOS_SEMANAIS:
        # Gera as últimas 52 semanas (segunda-feira de cada semana)
        hoje   = date.today()
        segunda_atual = hoje - timedelta(days=hoje.weekday())
        opcoes_sem = []
        for i in range(52):
            seg = segunda_atual - timedelta(weeks=i)
            dom = seg + timedelta(days=6)
            num = int(seg.strftime("%V"))
            ano = seg.year
            label = f"Semana {num:02d} / {ano}  ({seg.strftime('%d/%m')} – {dom.strftime('%d/%m')})"
            opcoes_sem.append((label, seg))

        labels_sem = [o[0] for o in opcoes_sem]
        idx_sel = st.selectbox(
            t("comum.semana_referencia"),
            range(len(labels_sem)),
            format_func=lambda i: labels_sem[i],
            key="sel_semana_ref"
        )
        data_ref = opcoes_sem[idx_sel][1]   # segunda-feira da semana selecionada
        st.caption(f"Semana {int(data_ref.strftime('%V')):02d} / {data_ref.year} — de {data_ref.strftime('%d/%m/%Y')} a {(data_ref + timedelta(days=6)).strftime('%d/%m/%Y')}")
    else:
        data_ref = st.date_input(t("comum.data_referencia"))

    # ========================
    # 🚀 IMPORTAR
    # ========================
    if st.button(t("imp.btn_importar")):

        if tipo_importacao == "Backlog" and not data_ref:
            st.warning(t("imp.selecione_data"))
            return

        if not arquivos:
            st.warning(t("imp.selecione_arquivos"))
            return

        arquivos_grandes = [a.name for a in arquivos if a.size > _LIMITE_MB * 1024 * 1024]
        if arquivos_grandes:
            st.error(
                f"Arquivo(s) acima de {_LIMITE_MB} MB não são aceitos: "
                + ", ".join(arquivos_grandes)
            )
            return

        if tipo_importacao == "Devolução + Monitoramento" and arquivo_monitor_secundario is None:
            st.warning(t("imp.selecione_monitoramento"))
            return

        if tipo_importacao == "Shein — Backlog Completo" and (
            arquivo_folha_shein is None or arquivo_monitor_shein is None
        ):
            st.warning("Selecione os 3 arquivos: Insucesso LM + Folha de Devolução + Monitoramento.")
            return

        resultados    = []
        logs          = []
        total_registros = 0

        with st.status(t("imp.processando"), expanded=True) as status_box:
            for i, arq in enumerate(arquivos):
                n     = i + 1
                total = len(arquivos)
                st.write(f"[{n}/{total}] Lendo `{arq.name}`...")
                inicio = time.time()
                sec = arquivo_folha_shein   if tipo_importacao == "Shein — Backlog Completo" else arquivo_monitor_secundario
                ter = arquivo_monitor_shein if tipo_importacao == "Shein — Backlog Completo" else None
                r = processar_arquivo_individual(
                    arq, data_ref, tipo_importacao, sec, ter
                )
                tempo = time.time() - inicio
                registros = r["registros"] or 0
                total_registros += registros

                if r["status"] == "Sucesso":
                    st.write(f"✓ `{arq.name}`: {registros:,} registros ({tempo:.1f}s)")
                    if r.get("detalhe"):
                        st.caption(r["detalhe"])
                else:
                    st.write(f"✗ `{arq.name}`: {r['status']}")

                resultados.append({"arquivo": r["arquivo"], "status": r["status"], "registros": registros})
                logs.append({"id": i, "nome_arquivo": r["arquivo"], "status": r["status"],
                             "registros": registros, "tempo_segundos": tempo,
                             "data_importacao": pd.Timestamp.now()})

            status_box.update(
                label=f"✓ {t('imp.concluida').format(n=f'{total_registros:,}')}",
                state="complete"
            )

        df_logs = pd.DataFrame(logs)
        salvar_log_importacao(df_logs)
        st.session_state.resultado_importacao = resultados
        st.session_state.total_importado = total_registros
        st.cache_data.clear()
        st.rerun()

    # ========================
    # 📊 RESULTADO
    # ========================
    if st.session_state.resultado_importacao is not None:
        erros = [r for r in st.session_state.resultado_importacao if r["status"] != "Sucesso"]
        if erros:
            for r in erros:
                st.error(f"{r['arquivo']} → {r['status']}")
        else:
            st.success(f"✓ {t('imp.concluida').format(n=f'{st.session_state.total_importado:,}')}")

    st.divider()

    # ========================
    # 📜 HISTÓRICO
    # ========================
    st.subheader(t("imp.historico"))

    df_hist = _carregar_historico()

    if df_hist.empty:
        st.info(t("imp.sem_arquivos"))
    else:
        # Formatar datas para exibição
        def fmt_ref(val):
            try:
                return pd.to_datetime(val).strftime("%d/%m/%Y")
            except Exception:
                return str(val) if pd.notna(val) else ""

        def fmt_import(val):
            try:
                return pd.to_datetime(val).strftime("%d/%m/%Y %H:%M")
            except Exception:
                return str(val) if pd.notna(val) else ""

        for i, (_, row) in enumerate(df_hist.iterrows()):
            col1, col2, col3, col4, col5, col6 = st.columns([4,2,2,3,3,1])

            col1.write(row["nome_arquivo"])
            col2.write(row["registros"])
            col3.write(row["tipo"])
            col4.write(fmt_ref(row['data_referencia']))
            col5.write(fmt_import(row['data_importacao']))

            if col6.button("X", key=f"del_{i}"):
                excluir_arquivo(row["nome_arquivo"])
                st.success(f"{row['nome_arquivo']} excluído")
                st.rerun()

    # ========================
    # ⚠️ ZONA DE PERIGO
    # ========================
    st.divider()
    st.subheader(t("imp.zona_perigo"))

    confirmar = st.checkbox(t("imp.confirmacao_destruicao"))

    if confirmar:
        col1, col2, col3 = st.columns([1, 1.6, 1])

        with col1:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button(t("imp.resetar_backlog"), use_container_width=True):
                executar_backlog("DELETE FROM backlog_atual")
                st.success(t("imp.backlog_zerado"))
                st.cache_data.clear()
                st.rerun()

        with col2:
            data_delete = st.date_input(t("imp.excluir_data_ref"))
            if st.button(t("imp.excluir_data"), use_container_width=True):
                executar_historico(
                    "DELETE FROM pedidos WHERE data_referencia = %s",
                    [data_delete]
                )
                st.success(f"Dados da data {data_delete} excluídos!")
                st.cache_data.clear()
                st.rerun()

        with col3:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button(t("imp.limpar_historico"), use_container_width=True):
                limpar_base()
                st.success(t("imp.historico_removido"))
                st.cache_data.clear()
                st.rerun()

    rodape_autoria()


# ========================
# 🗑️ DELETE
# ========================
def excluir_arquivo(nome_arquivo):
    executar_historico("DELETE FROM pedidos WHERE nome_arquivo = %s", [nome_arquivo])
    executar_historico("DELETE FROM pedidos_resumo WHERE nome_arquivo = %s", [nome_arquivo])
    executar_operacional("DELETE FROM produtividade WHERE nome_arquivo = %s", [nome_arquivo])
    executar_operacional("DELETE FROM pacotes_grandes WHERE nome_arquivo = %s", [nome_arquivo])
    executar_processamento("DELETE FROM tempo_processamento WHERE nome_arquivo = %s", [nome_arquivo])
    executar_processamento("DELETE FROM percentis_operacao WHERE nome_arquivo = %s", [nome_arquivo])

    for tabela in ["dev_status_semanal", "dev_iatas_semanal", "dev_sla_semanal",
                   "dev_motivos_semanal", "dev_dsp_sem3tent", "p90_semanal", "dev_detalhado",
                   "dev_shein_backlog", "dev_shein_sla", "dev_shein_motivos", "dev_shein_aging"]:
        executar_devolucoes(f"DELETE FROM {tabela} WHERE nome_arquivo = %s", [nome_arquivo])

    executar_coletas("DELETE FROM coletas WHERE nome_arquivo = %s", [nome_arquivo])
    executar_coletas("DELETE FROM coletas_grandes WHERE nome_arquivo = %s", [nome_arquivo])
    executar_coletas("DELETE FROM coleta_final WHERE nome_arquivo = %s", [nome_arquivo])
    executar_presenca("DELETE FROM presenca_turno WHERE nome_arquivo = %s", [nome_arquivo])
    executar_presenca("DELETE FROM presenca_diaria WHERE nome_arquivo = %s", [nome_arquivo])
    st.cache_data.clear()