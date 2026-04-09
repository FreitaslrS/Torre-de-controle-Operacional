import streamlit as st
import time
import pandas as pd
from datetime import date, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.database import executar_backlog
from core.repository import salvar_log_importacao
from core.processar_arquivo import importar_excel, importar_produtividade, limpar_base
from core.database import conectar_backlog
from core.database import (
    consultar_historico,
    consultar_operacional,
    executar_historico,
    executar_operacional
)
from core.processar_arquivo import importar_tempo_processamento
from core.database import consultar_processamento

@st.cache_resource

def get_conexao():
    return conectar_backlog()

# =========================
# 🔐 LOGIN
# =========================
def obter_senha():
    return "Ss.sist@05060711*"


def verificar_senha():
    if "autenticado" not in st.session_state:
        st.session_state.autenticado = False

    if st.session_state.autenticado:
        return True

    st.title("🔐 Área Restrita / 受限区域")

    senha = st.text_input("Digite a senha / 输入密码", type="password")

    if st.button("Entrar / 登录"):
        if senha == obter_senha():
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Senha incorreta")

    return False


# =========================
# 🚀 PROCESSAMENTO PARALELO
# =========================
def processar_arquivo_individual(arquivo, data_ref, tipo_importacao):
    inicio = time.time()

    try:
        if tipo_importacao == "Backlog":
            qtd = importar_excel(arquivo, data_ref)

        elif tipo_importacao == "Produtividade":
            qtd = importar_produtividade(arquivo)

        elif tipo_importacao == "Tempo de Processamento":
            qtd = importar_tempo_processamento(arquivo)

        elif tipo_importacao == "Devolução":
            from core.processar_arquivo import importar_devolucoes
            qtd = importar_devolucoes(arquivo, data_ref)

        elif tipo_importacao == "Devolução - P90":
            from core.processar_arquivo import importar_p90
            qtd = importar_p90(arquivo, data_ref)

        elif tipo_importacao == "Devolução - Monitoramento":
            from core.processar_arquivo import importar_devolucao_monitoramento
            qtd = importar_devolucao_monitoramento(arquivo, data_ref)

        elif tipo_importacao == "Pacotes Grandes":
            from core.processar_arquivo import importar_pacotes_grandes
            qtd = importar_pacotes_grandes(arquivo)

        else:
            raise Exception("Tipo de importação inválido")

        status = "Sucesso"

    except Exception as e:
        qtd = 0
        status = str(e)

    tempo = time.time() - inicio

    return {
        "arquivo": arquivo.name,
        "status": status,
        "registros": qtd,
        "tempo": tempo
    }

# =========================
# 🎯 TELA
# =========================
def render():

    if not verificar_senha():
        return

    st.markdown("## <i class='fas fa-upload'></i> Importação de Dados / 数据导入", unsafe_allow_html=True)

    arquivos = st.file_uploader(
        "Selecione arquivos Excel / 选择Excel文件",
        type=["xlsx", "xls"],
        accept_multiple_files=True
    )

    if "resultado_importacao" not in st.session_state:
        st.session_state.resultado_importacao = None
        st.session_state.total_importado = 0

    tipo_importacao = st.selectbox(
        "Tipo de Importação / 导入类型",
        ["Backlog", "Produtividade", "Tempo de Processamento", "Devolução", "Devolução - P90", "Devolução - Monitoramento", "Pacotes Grandes"]
    )

    # ========================
    # 📅 SELETOR DE DATA / SEMANA
    # ========================
    TIPOS_SEMANAIS = {"Devolução", "Devolução - P90", "Pacotes Grandes"}

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
            "Semana de referência / 参考周",
            range(len(labels_sem)),
            format_func=lambda i: labels_sem[i],
            key="sel_semana_ref"
        )
        data_ref = opcoes_sem[idx_sel][1]   # segunda-feira da semana selecionada
        st.caption(f"Semana {int(data_ref.strftime('%V')):02d} / {data_ref.year} — de {data_ref.strftime('%d/%m/%Y')} a {(data_ref + timedelta(days=6)).strftime('%d/%m/%Y')}")
    else:
        data_ref = st.date_input("Data de referência / 参考日期")

    # ========================
    # 🚀 IMPORTAR
    # ========================
    if st.button("Importar / 导入"):

        if tipo_importacao == "Backlog" and not data_ref:
            st.warning("Selecione a data de referência")
            return

        if not arquivos:
            st.warning("Selecione arquivos")
            return

        progress = st.progress(0)
        status_text = st.empty()

        resultados = []
        logs = []
        total_registros = 0

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(processar_arquivo_individual, arq, data_ref, tipo_importacao)
                for arq in arquivos
            ]

            for i, future in enumerate(as_completed(futures)):
                r = future.result()

                registros = r["registros"] or 0
                total_registros += registros

                resultados.append({
                    "arquivo": r["arquivo"],
                    "status": r["status"],
                    "registros": registros
                })

                logs.append({
                    "id": i,
                    "nome_arquivo": r["arquivo"],
                    "status": r["status"],
                    "registros": r["registros"],
                    "tempo_segundos": r["tempo"],
                    "data_importacao": pd.Timestamp.now()
                })

                progress.progress((i + 1) / len(arquivos))
                status_text.text(f"Finalizado: {r['arquivo']}")

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

        st.success(f"{st.session_state.total_importado} registros importados")

        for r in st.session_state.resultado_importacao:
            if r["status"] != "Sucesso":
                st.error(f"{r['arquivo']} → {r['status']}")
            else:
                st.success(f"{r['arquivo']} → {r['registros']} registros")

    st.divider()

    # ========================
    # 📜 HISTÓRICO
    # ========================
    st.subheader("📊 Histórico de Importações / 导入历史")

    from core.database import consultar_backlog as consultar

    df_hist_backlog = consultar_historico("""
        SELECT
            nome_arquivo,
            SUM(qtd) as registros,
            MAX(data_importacao) as data_importacao,
            MAX(data_referencia) as data_referencia,
            'Backlog' as tipo
        FROM pedidos_resumo
        GROUP BY nome_arquivo
    """)

    df_hist_prod = consultar_operacional("""
        SELECT 
            nome_arquivo,
            COUNT(*) as registros,
            MAX(data_importacao) as data_importacao,
            MAX(data) as data_referencia,
            'Produtividade' as tipo
        FROM produtividade
        GROUP BY nome_arquivo
    """)

    df_hist_proc = consultar_processamento("""
        SELECT
            nome_arquivo,
            SUM(qtd_total) as registros,
            MAX(data_importacao) as data_importacao,
            MAX(data) as data_referencia,
            'Tempo Processamento' as tipo
        FROM tempo_processamento
        GROUP BY nome_arquivo
    """)

    from core.database import consultar_devolucoes

    df_hist_dev = consultar_devolucoes("""
        SELECT
            nome_arquivo,
            SUM(qtd) as registros,
            MAX(data_importacao) as data_importacao,
            MAX(data_importacao) as data_referencia,
            'Devolução' as tipo
        FROM dev_status_semanal
        GROUP BY nome_arquivo
    """)

    df_hist_p90 = consultar_devolucoes("""
        SELECT
            nome_arquivo,
            SUM(qtd_pedidos) as registros,
            MAX(data_importacao) as data_importacao,
            MAX(data_importacao) as data_referencia,
            'Devolução - P90' as tipo
        FROM p90_semanal
        GROUP BY nome_arquivo
    """)

    df_hist_mon = consultar_devolucoes("""
        SELECT
            nome_arquivo,
            SUM(qtd_total) as registros,
            MAX(data_importacao) as data_importacao,
            MAX(data_importacao) as data_referencia,
            'Devolução - Monitoramento' as tipo
        FROM dev_sla_semanal
        GROUP BY nome_arquivo
    """)

    df_hist_pg = consultar_operacional("""
        SELECT
            nome_arquivo,
            COUNT(*) as registros,
            MAX(data_importacao) as data_importacao,
            MAX(data_importacao) as data_referencia,
            'Pacotes Grandes' as tipo
        FROM pacotes_grandes
        GROUP BY nome_arquivo
    """)

    df_hist = pd.concat(
        [df_hist_backlog, df_hist_prod, df_hist_proc, df_hist_dev, df_hist_p90, df_hist_mon, df_hist_pg],
        ignore_index=True
    )

    df_hist = df_hist.sort_values("data_importacao", ascending=False)

    if df_hist.empty:
        st.info("Nenhum arquivo importado ainda / 暂无导入记录")
    else:
        for _, row in df_hist.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([4,2,2,3,3,1])

            col1.write(row["nome_arquivo"])
            col2.write(row["registros"])
            col3.write(row["tipo"])  # 🔥 novo
            col4.write(f"📅: {row['data_referencia']}")
            col5.write(f"⏱️ {row['data_importacao']}")

            if col6.button("🗑️", key=f"{row['nome_arquivo']}_{row['data_importacao']}"):
                excluir_arquivo(row["nome_arquivo"])
                st.success(f"{row['nome_arquivo']} excluído")
                st.rerun()

    # ========================
    # ⚠️ ZONA DE PERIGO
    # ========================
    st.divider()
    st.subheader("⚠️ Zona de Perigo")

    confirmar = st.checkbox("Tenho certeza que quero fazer isso (modo destruição)")

    col1, col2, col3 = st.columns(3)

    if confirmar:

        with col1:
            if st.button("🔥 Resetar Backlog Atual"):
                executar_backlog("DELETE FROM backlog_atual")
                st.success("Backlog atual zerado!")
                st.cache_data.clear()
                st.rerun()

        with col2:
            data_delete = st.date_input("Excluir por data de referência")

            if st.button("🗑️ Excluir por Data"):
                executar_historico(
                    "DELETE FROM pedidos WHERE data_referencia = %s",
                    [data_delete]
                )
                st.success(f"Dados da data {data_delete} excluídos!")
                st.cache_data.clear()
                st.rerun()

        with col3:
            if st.button("🧹 Limpar histórico > 30 dias"):
                limpar_base()
                st.success("Histórico antigo removido!")
                st.cache_data.clear()
                st.rerun()


# ========================
# 🗑️ DELETE
# ========================
def excluir_arquivo(nome_arquivo):

    executar_historico(
        "DELETE FROM pedidos WHERE nome_arquivo = %s",
        [nome_arquivo]
    )

    executar_operacional(
        "DELETE FROM produtividade WHERE nome_arquivo = %s",
        [nome_arquivo]
    )

    executar_operacional(
        "DELETE FROM pacotes_grandes WHERE nome_arquivo = %s",
        [nome_arquivo]
    )

    from core.database import executar_processamento, executar_devolucoes

    executar_processamento(
        "DELETE FROM tempo_processamento WHERE nome_arquivo = %s",
        [nome_arquivo]
    )

    for tabela in ["dev_status_semanal", "dev_iatas_semanal", "dev_sla_semanal",
                   "dev_motivos_semanal", "dev_dsp_sem3tent", "p90_semanal"]:
        executar_devolucoes(
            f"DELETE FROM {tabela} WHERE nome_arquivo = %s",
            [nome_arquivo]
        )

    st.cache_data.clear()