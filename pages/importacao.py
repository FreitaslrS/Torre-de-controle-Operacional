import streamlit as st
import time
import pandas as pd
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from dotenv import load_dotenv

from utils.style import rodape_autoria, aplicar_css_global
from core.database import (
    executar_backlog, executar_historico, executar_operacional,
    consultar_historico, consultar_operacional, consultar_processamento,
    consultar_devolucoes, consultar_coletas,
    executar_processamento, executar_devolucoes, executar_coletas,
)
from core.repository import salvar_log_importacao
from core.processar_arquivo import (
    importar_excel, importar_produtividade, limpar_base,
    importar_tempo_processamento, importar_devolucoes, importar_p90,
    importar_devolucao_monitoramento, importar_devolucao_enriquecida,
    importar_coletas, importar_coletas_saida,
    importar_pacotes_grandes, importar_presenca,
)

load_dotenv()


@st.cache_data(ttl=60)
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
            SELECT nome_arquivo, SUM(qtd) as registros, MAX(data_importacao) as data_importacao,
                   MAX(data_referencia) as data_referencia, 'Devolução' as tipo
            FROM dev_status_semanal GROUP BY nome_arquivo"""),
        (consultar_devolucoes, """
            SELECT nome_arquivo, SUM(qtd_pedidos) as registros, MAX(data_importacao) as data_importacao,
                   MAX(data_referencia) as data_referencia, 'Devolução - P90' as tipo
            FROM p90_semanal GROUP BY nome_arquivo"""),
        (consultar_devolucoes, """
            SELECT nome_arquivo, SUM(qtd_total) as registros, MAX(data_importacao) as data_importacao,
                   MAX(data_referencia) as data_referencia, 'Devolução - Monitoramento' as tipo
            FROM dev_sla_semanal GROUP BY nome_arquivo"""),
        (consultar_operacional, """
            SELECT nome_arquivo, COUNT(*) as registros, MAX(data_importacao) as data_importacao,
                   CONCAT('Sem ', MAX(semana), '/', MAX(ano)) as data_referencia, 'Pacotes Grandes' as tipo
            FROM pacotes_grandes GROUP BY nome_arquivo"""),
        (consultar_coletas, """
            SELECT nome_arquivo, COUNT(*) as registros, MAX(data_importacao) as data_importacao,
                   MAX(data_referencia) as data_referencia, CONCAT('Coletas — ', MAX(tipo)) as tipo
            FROM coletas GROUP BY nome_arquivo"""),
        (consultar_devolucoes, """
            SELECT nome_arquivo, COUNT(*) as registros, MAX(data_importacao) as data_importacao,
                   MAX(data_referencia) as data_referencia, 'Devolução + Monitoramento' as tipo
            FROM dev_detalhado GROUP BY nome_arquivo"""),
        (consultar_operacional, """
            SELECT nome_arquivo, COUNT(*) as registros, MAX(data_importacao) as data_importacao,
                   CONCAT('Sem ', MAX(semana), '/', MAX(ano)) as data_referencia, 'Presença / Diário de Bordo' as tipo
            FROM presenca_turno GROUP BY nome_arquivo"""),
    ]
    dfs = []
    for fn, sql in consultas:
        try:
            dfs.append(fn(sql))
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
        st.error("Importação bloqueada: SENHA_IMPORTACAO não configurada no ambiente.")
        return False

    if st.session_state.tentativas_senha >= _MAX_TENTATIVAS:
        st.error(
            f"Acesso bloqueado após {_MAX_TENTATIVAS} tentativas incorretas. "
            "Recarregue a página para tentar novamente."
        )
        return False

    st.markdown("""
<div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem;">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
         stroke="#053B31" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
    </svg>
    <div>
        <h2 style="margin:0;font-size:20px;font-weight:700;color:#053B31;font-family:'Montserrat',sans-serif;">Área Restrita</h2>
        <p style="margin:0;font-size:12px;color:#6b7280;font-family:'Montserrat',sans-serif;">Acesso restrito a usuários autorizados</p>
    </div>
</div>
""", unsafe_allow_html=True)
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar"):
        if senha and senha == senha_correta:
            st.session_state.autenticado = True
            st.session_state.tentativas_senha = 0
            st.rerun()
        else:
            st.session_state.tentativas_senha += 1
            restantes = _MAX_TENTATIVAS - st.session_state.tentativas_senha
            if restantes > 0:
                st.error(f"Senha incorreta. {restantes} tentativa(s) restante(s).")
            else:
                st.error("Acesso bloqueado. Recarregue a página para tentar novamente.")
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


def processar_arquivo_individual(arquivo, data_ref, tipo_importacao, arquivo_secundario=None):
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

        elif tipo_importacao == "Coletas — Descarregamento em Perus":
            resultado = importar_coletas(arquivo, data_ref)

        elif tipo_importacao == "Coletas — Saída para Bases":
            resultado = importar_coletas_saida(arquivo, data_ref)

        elif tipo_importacao == "Pacotes Grandes":
            resultado = importar_pacotes_grandes(arquivo, data_ref)

        elif tipo_importacao == "Presença / Diário de Bordo":
            resultado = importar_presenca(arquivo)

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

    st.markdown("## Importação de Dados", unsafe_allow_html=True)

    _LIMITE_MB = 50
    arquivos = st.file_uploader(
        f"Selecione arquivos Excel (máx. {_LIMITE_MB} MB por arquivo)",
        type=["xlsx", "xls"],
        accept_multiple_files=True
    )

    if "resultado_importacao" not in st.session_state:
        st.session_state.resultado_importacao = None
        st.session_state.total_importado = 0

    tipo_importacao = st.selectbox(
        "Tipo de Importação",
        [
            "Backlog",
            "Produtividade",
            "Tempo de Processamento",
            "Devolução + Monitoramento",
            "Devolução - Monitoramento",
            "Coletas — Descarregamento em Perus",
            "Coletas — Saída para Bases",
            "Pacotes Grandes",
            "Presença / Diário de Bordo",
        ]
    )

    # Uploader secundário para "Devolução + Monitoramento"
    arquivo_monitor_secundario = None
    if tipo_importacao == "Devolução + Monitoramento":
        st.info("Este tipo requer dois arquivos: o arquivo principal (Folha de Devolução) vai no uploader acima. Selecione o Monitoramento abaixo.")
        arquivo_monitor_secundario = st.file_uploader(
            "Arquivo de Monitoramento de Pontualidade",
            type=["xlsx", "xls"],
            key="uploader_monitor_sec"
        )

    # ========================
    # 📅 SELETOR DE DATA / SEMANA
    # ========================
    TIPOS_SEMANAIS = {
        "Devolução", "Devolução - P90", "Devolução + Monitoramento",
        "Pacotes Grandes",
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
            "Semana de referência",
            range(len(labels_sem)),
            format_func=lambda i: labels_sem[i],
            key="sel_semana_ref"
        )
        data_ref = opcoes_sem[idx_sel][1]   # segunda-feira da semana selecionada
        st.caption(f"Semana {int(data_ref.strftime('%V')):02d} / {data_ref.year} — de {data_ref.strftime('%d/%m/%Y')} a {(data_ref + timedelta(days=6)).strftime('%d/%m/%Y')}")
    else:
        data_ref = st.date_input("Data de referência")

    # ========================
    # 🚀 IMPORTAR
    # ========================
    if st.button("Importar"):

        if tipo_importacao == "Backlog" and not data_ref:
            st.warning("Selecione a data de referência")
            return

        if not arquivos:
            st.warning("Selecione arquivos")
            return

        arquivos_grandes = [a.name for a in arquivos if a.size > _LIMITE_MB * 1024 * 1024]
        if arquivos_grandes:
            st.error(
                f"Arquivo(s) acima de {_LIMITE_MB} MB não são aceitos: "
                + ", ".join(arquivos_grandes)
            )
            return

        if tipo_importacao == "Devolução + Monitoramento" and arquivo_monitor_secundario is None:
            st.warning("Selecione o arquivo de Monitoramento de Pontualidade")
            return

        progress = st.progress(0)
        log_area = st.empty()
        log_linhas = []

        resultados = []
        logs = []
        total_registros = 0

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(
                    processar_arquivo_individual, arq, data_ref, tipo_importacao,
                    arquivo_monitor_secundario
                )
                for arq in arquivos
            ]

            for i, future in enumerate(as_completed(futures)):
                try:
                    r = future.result()
                except Exception as exc:
                    r = {
                        "arquivo": "desconhecido",
                        "status": f"Erro interno: {type(exc).__name__}: {exc}",
                        "registros": 0,
                        "detalhe": "",
                        "tempo": 0,
                    }

                registros = r["registros"] or 0
                total_registros += registros
                n = i + 1
                total = len(arquivos)

                # Monta linha de log estilo Luis
                linha_ok  = f"✓ [{n}/{total}] {r['arquivo']}: {registros:,} registros ({r['tempo']:.1f}s)"
                linha_det = f"   {r['detalhe']}" if r.get("detalhe") else ""
                if r["status"] != "Sucesso":
                    linha_ok = f"✗ [{n}/{total}] {r['arquivo']}: {r['status']}"

                log_linhas.append(linha_ok)
                if linha_det:
                    log_linhas.append(linha_det)
                log_area.code("\n".join(log_linhas), language=None)

                resultados.append({
                    "arquivo":   r["arquivo"],
                    "status":    r["status"],
                    "registros": registros
                })
                logs.append({
                    "id":              i,
                    "nome_arquivo":    r["arquivo"],
                    "status":          r["status"],
                    "registros":       r["registros"],
                    "tempo_segundos":  r["tempo"],
                    "data_importacao": pd.Timestamp.now()
                })
                progress.progress(n / total)

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
            st.success(f"✓ Importação concluída — {st.session_state.total_importado:,} registros")

    st.divider()

    # ========================
    # 📜 HISTÓRICO
    # ========================
    st.subheader("Histórico de Importações")

    df_hist = _carregar_historico()

    if df_hist.empty:
        st.info("Nenhum arquivo importado ainda")
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
    st.subheader("Zona de Perigo")

    confirmar = st.checkbox("Tenho certeza que quero fazer isso (modo destruição)")

    if confirmar:
        col1, col2, col3 = st.columns([1, 1.6, 1])

        with col1:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("Resetar Backlog Atual", use_container_width=True):
                executar_backlog("DELETE FROM backlog_atual")
                st.success("Backlog atual zerado!")
                st.cache_data.clear()
                st.rerun()

        with col2:
            data_delete = st.date_input("Excluir por data de referência")
            if st.button("Excluir por Data", use_container_width=True):
                executar_historico(
                    "DELETE FROM pedidos WHERE data_referencia = %s",
                    [data_delete]
                )
                st.success(f"Dados da data {data_delete} excluídos!")
                st.cache_data.clear()
                st.rerun()

        with col3:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("Limpar histórico > 30 dias", use_container_width=True):
                limpar_base()
                st.success("Histórico antigo removido!")
                st.cache_data.clear()
                st.rerun()

    rodape_autoria()


# ========================
# 🗑️ DELETE
# ========================
def excluir_arquivo(nome_arquivo):
    executar_historico("DELETE FROM pedidos WHERE nome_arquivo = %s", [nome_arquivo])
    executar_operacional("DELETE FROM produtividade WHERE nome_arquivo = %s", [nome_arquivo])
    executar_operacional("DELETE FROM pacotes_grandes WHERE nome_arquivo = %s", [nome_arquivo])
    executar_processamento("DELETE FROM tempo_processamento WHERE nome_arquivo = %s", [nome_arquivo])

    for tabela in ["dev_status_semanal", "dev_iatas_semanal", "dev_sla_semanal",
                   "dev_motivos_semanal", "dev_dsp_sem3tent", "p90_semanal", "dev_detalhado"]:
        executar_devolucoes(f"DELETE FROM {tabela} WHERE nome_arquivo = %s", [nome_arquivo])

    executar_coletas("DELETE FROM coletas WHERE nome_arquivo = %s", [nome_arquivo])
    executar_operacional("DELETE FROM presenca_turno WHERE nome_arquivo = %s", [nome_arquivo])
    executar_operacional("DELETE FROM presenca_diaria WHERE nome_arquivo = %s", [nome_arquivo])
    st.cache_data.clear()