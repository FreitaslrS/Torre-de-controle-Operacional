import streamlit as st
import pandas as pd
from psycopg2.extras import execute_values

from core.database import (
    consultar_backlog,
    consultar_operacional,
    consultar_processamento,
    consultar_historico,
    consultar_devolucoes,
    consultar_coletas,
    executar_backlog,
    executar_operacional,
    _conn,
)

# =========================
# 🔧 HELPERS
# =========================
def _filtro_cliente(query, params, cliente):
    """Adiciona filtro de cliente a query/params. Aceita string ou lista."""
    if not cliente:
        return query, params
    if isinstance(cliente, list):
        if len(cliente) == 1:
            query += " AND cliente = %s"
            params.append(cliente[0])
        else:
            query += " AND cliente = ANY(%s)"
            params.append(cliente)
    else:
        query += " AND cliente = %s"
        params.append(cliente)
    return query, params


# =========================
# 🗑️ DELETE
# =========================
def deletar_arquivo(nome_arquivo):
    executar_backlog(
        "DELETE FROM pedidos WHERE nome_arquivo = %s",
        [nome_arquivo]
    )


# =========================
# 📂 LISTAR ARQUIVOS
# =========================
@st.cache_data(ttl=300)
def listar_arquivos():
    return consultar_backlog("""
        SELECT 
            nome_arquivo,
            COUNT(*) as registros
        FROM pedidos
        GROUP BY nome_arquivo
        ORDER BY nome_arquivo DESC
    """)


# =========================
# 📊 BACKLOG COMPLETO (cache p/ filtros em Python)
# =========================
@st.cache_data(ttl=300)
def carregar_backlog_atual_completo():
    """
    Carrega backlog_atual agregado. Filtros de estado/cliente/faixa aplicados em Python.
    Download de waybills individuais continua via tabela `pedidos`.
    """
    return consultar_backlog("""
        SELECT
            estado, cliente, pre_entrega, proximo_ponto,
            faixa_backlog_snapshot,
            qtd, horas_min, horas_max, horas_media,
            entrada_hub1_mais_ant, data_referencia, data_importacao
        FROM backlog_atual
    """)


# =========================
# 📊 BACKLOG RESUMO
# =========================
@st.cache_data(ttl=300)
def buscar_backlog_resumo():
    return consultar_backlog("""
        SELECT
            estado, cliente,
            SUM(qtd)                                                    AS qtd,
            SUM(CASE WHEN faixa_backlog_snapshot != '1 dia'
                THEN qtd ELSE 0 END)                                    AS b24,
            SUM(CASE WHEN faixa_backlog_snapshot IN
                ('1-5 dias','5-10 dias','10-20 dias','20-30 dias','30+ dias')
                AND horas_min > 48 THEN qtd ELSE 0 END)                 AS b48,
            SUM(CASE WHEN faixa_backlog_snapshot IN
                ('1-5 dias','5-10 dias','10-20 dias','20-30 dias','30+ dias')
                AND horas_min > 72 THEN qtd ELSE 0 END)                 AS b72
        FROM backlog_atual
        GROUP BY estado, cliente
    """)


# =========================
# 📊 GRÁFICO POR ESTADO
# =========================
def buscar_backlog_por_estado(remover_estados=None, remover_clientes=None, faixa=None):

    query = """
        SELECT estado, COUNT(*) as qtd
        FROM backlog_atual
        WHERE 1=1
    """

    params = []

    if remover_estados:
        query += " AND estado != ALL(%s)"
        params.append(remover_estados)

    if remover_clientes:
        query += " AND cliente != ALL(%s)"
        params.append(remover_clientes)

    if faixa == "0-24h":
        query += " AND horas_backlog_snapshot <= 24"

    elif faixa == "24-48h":
        query += " AND horas_backlog_snapshot > 24 AND horas_backlog_snapshot <= 48"

    elif faixa == "48-72h":
        query += " AND horas_backlog_snapshot > 48 AND horas_backlog_snapshot <= 72"

    elif faixa == "72h+":
        query += " AND horas_backlog_snapshot > 72"

    query += " GROUP BY estado ORDER BY qtd DESC"

    return consultar_backlog(query, params)


# =========================
# 📊 GRÁFICO POR CLIENTE
# =========================
def buscar_backlog_por_cliente(remover_clientes=None, remover_estados=None, faixa=None):

    query = """
        SELECT cliente, COUNT(*) as qtd
        FROM backlog_atual
        WHERE 1=1
    """

    params = []

    if remover_clientes:
        query += " AND cliente != ALL(%s)"
        params.append(remover_clientes)

    if remover_estados:
        query += " AND estado != ALL(%s)"
        params.append(remover_estados)

    # 🔥 AQUI TAVA FALTANDO
    if faixa == "0-24h":
        query += " AND horas_backlog_snapshot <= 24"

    elif faixa == "24-48h":
        query += " AND horas_backlog_snapshot > 24 AND horas_backlog_snapshot <= 48"

    elif faixa == "48-72h":
        query += " AND horas_backlog_snapshot > 48 AND horas_backlog_snapshot <= 72"

    elif faixa == "72h+":
        query += " AND horas_backlog_snapshot > 72"

    query += " GROUP BY cliente ORDER BY qtd DESC"

    return consultar_backlog(query, params)


# =========================
# 📊 GRAFICO PRÓXIMO PONTO
# =========================
def buscar_backlog_por_proximo_ponto(faixa=None):

    query = """
        SELECT 
            CASE 
                WHEN proximo_ponto IS NULL OR proximo_ponto = '' 
                THEN 'Sem informação / 无信息'
                ELSE proximo_ponto
            END as proximo_ponto,
            COUNT(*) as qtd
        FROM backlog_atual
        WHERE 1=1
    """

    if faixa == "0-24h":
        query += " AND horas_backlog_snapshot <= 24"

    elif faixa == "24-48h":
        query += " AND horas_backlog_snapshot > 24 AND horas_backlog_snapshot <= 48"

    elif faixa == "48-72h":
        query += " AND horas_backlog_snapshot > 48 AND horas_backlog_snapshot <= 72"

    elif faixa == "72h+":
        query += " AND horas_backlog_snapshot > 72"

    query += """
        GROUP BY 
            CASE 
                WHEN proximo_ponto IS NULL OR proximo_ponto = '' 
                THEN 'Sem informação / 无信息'
                ELSE proximo_ponto
            END
        ORDER BY qtd DESC
    """

    return consultar_backlog(query)


# =========================
# 🏆 GRAFICO TOP 10 PRÉ-ENTREGA
# =========================
def buscar_top10_pre_entrega(faixa=None):

    query = """
        SELECT pre_entrega, COUNT(*) as qtd
        FROM backlog_atual
        WHERE 1=1
    """

    # 🔥 ADICIONA ISSO
    if faixa == "24h+":
        query += " AND horas_backlog_snapshot > 24"
    elif faixa == "48h+":
        query += " AND horas_backlog_snapshot > 48"
    elif faixa == "72h+":
        query += " AND horas_backlog_snapshot > 72"

    query += " GROUP BY pre_entrega ORDER BY qtd DESC LIMIT 10"

    return consultar_backlog(query)


# =========================
# 📊 BACKLOG DETALHADO
# =========================
@st.cache_data(ttl=300)
def buscar_backlog_paginado(limit=100, offset=0, estados=None, clientes=None, faixa=None):

    query = """
        SELECT 
            waybill,
            cliente,
            estado,
            cidade,
            pre_entrega,
            proximo_ponto,
            horas_backlog_snapshot,
            faixa_backlog_snapshot,
            data_atualizacao
        FROM backlog_atual
        WHERE 1=1
    """

    params = []

    if estados:
        query += " AND estado = ANY(%s)"
        params.append(estados)

    if clientes:
        query += " AND cliente = ANY(%s)"
        params.append(clientes)

    if faixa == "24h+":
        query += " AND horas_backlog_snapshot > 24"
    elif faixa == "48h+":
        query += " AND horas_backlog_snapshot > 48"
    elif faixa == "72h+":
        query += " AND horas_backlog_snapshot > 72"

    query += " ORDER BY data_atualizacao DESC LIMIT %s OFFSET %s"
    params.extend([limit, offset])

    return consultar_backlog(query, params)


# =========================
# 📊 SLA POR ESTADO (agregado no banco)
# =========================
@st.cache_data(ttl=300)
def buscar_sla_por_estado():
    return consultar_backlog("""
        SELECT
            estado,
            SUM(CASE WHEN faixa_backlog_snapshot = '1 dia'
                THEN qtd ELSE 0 END)                                    AS "0-24h",
            SUM(CASE WHEN faixa_backlog_snapshot = '1-5 dias'
                THEN qtd ELSE 0 END)                                    AS "24-120h",
            SUM(CASE WHEN faixa_backlog_snapshot IN
                ('5-10 dias','10-20 dias','20-30 dias','30+ dias')
                THEN qtd ELSE 0 END)                                    AS "5d+",
            SUM(qtd)                                                    AS "Total"
        FROM backlog_atual
        GROUP BY estado
        ORDER BY "Total" DESC
    """)


# =========================
# 🔢 CONTAGEM BACKLOG
# =========================
@st.cache_data(ttl=300)
def contar_backlog(estados=None, clientes=None, faixa=None):

    query = "SELECT COUNT(*) as total FROM backlog_atual WHERE 1=1"
    params = []

    if estados:
        query += " AND estado = ANY(%s)"
        params.append(estados)

    if clientes:
        query += " AND cliente = ANY(%s)"
        params.append(clientes)

    # ❌ NÃO usa faixa aqui (view não tem horas)

    return consultar_backlog(query, params)


# =========================
# 📊 BACKLOG HISTÓRICO
# =========================
@st.cache_data(ttl=600)
def buscar_backlog_historico(data_inicio, data_fim):
    return consultar_historico("""
        SELECT
            data_referencia,
            estado,
            pre_entrega,
            cliente,
            proximo_ponto,
            faixa_backlog_snapshot,
            qtd,
            horas_min,
            horas_max
        FROM pedidos_resumo
        WHERE data_referencia BETWEEN %s AND %s
    """, [data_inicio, data_fim])


# =========================
# 📊 PRODUTIVIDADE (AGORA NO RAILWAY)
# =========================
@st.cache_data(ttl=600)
def buscar_produtividade(data_inicio=None, data_fim=None):
    """
    Query direta na tabela produtividade — sem depender da view materializada.
    Sempre retorna dados atualizados após cada importação.
    """
    query = """
        SELECT
            cliente,
            data,
            hora,
            turno,
            dispositivo,
            SUM(volumes) AS volumes
        FROM produtividade
        WHERE 1=1
    """
    params = []

    if data_inicio and data_fim:
        query += " AND data BETWEEN %s AND %s"
        params.extend([data_inicio, data_fim])
    else:
        query += " AND data = (SELECT MAX(data) FROM produtividade)"

    query += " GROUP BY cliente, data, hora, turno, dispositivo"

    return consultar_operacional(query, params if params else None)

# =========================
# 📦 PEDIDOS
# =========================
@st.cache_data(ttl=300)
def buscar_pedidos(limit=1000):
    return consultar_backlog("""
        SELECT 
            waybill,
            cliente,
            estado,
            cidade,
            pre_entrega,
            horas_backlog_snapshot,
            data_referencia
        FROM pedidos
        ORDER BY data_referencia DESC
        LIMIT %s
    """, [limit])


# =========================
# 💾 LOG IMPORTAÇÃO (RAILWAY)
# =========================
def salvar_log_importacao(logs_df):

    if logs_df.empty:
        return

    logs_df = logs_df.fillna(0)

    values = [
        (
            int(row["id"] or 0),
            row["nome_arquivo"],
            row["status"],
            int(row["registros"] or 0),
            float(row["tempo_segundos"] or 0),
            row["data_importacao"]
        )
        for _, row in logs_df.iterrows()
    ]

    with _conn("DATABASE_URL_OPERACIONAL") as conn:
        cur = conn.cursor()
        try:
            execute_values(
                cur,
                """
                INSERT INTO log_importacoes (
                    id,
                    nome_arquivo,
                    status,
                    registros,
                    tempo_segundos,
                    data_importacao
                ) VALUES %s
                """,
                values
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()


# =========================
# 🔍 DRILL
# =========================
def buscar_waybills_por_faixa_dias(data_inicio, data_fim, faixa):

    query = """
        SELECT waybill, estado, cliente, pre_entrega, horas_backlog_snapshot
        FROM pedidos
        WHERE data_referencia BETWEEN %s AND %s
    """

    params = [data_inicio, data_fim]

    if faixa == "1 dia":
        query += " AND horas_backlog_snapshot <= 24"
    elif faixa == "1-5 dias":
        query += " AND horas_backlog_snapshot > 24 AND horas_backlog_snapshot <= 120"
    elif faixa == "5-10 dias":
        query += " AND horas_backlog_snapshot > 120 AND horas_backlog_snapshot <= 240"
    elif faixa == "10-20 dias":
        query += " AND horas_backlog_snapshot > 240 AND horas_backlog_snapshot <= 480"
    elif faixa == "30+ dias":
        query += " AND horas_backlog_snapshot > 720"

    return consultar_historico(query, params)

# =========================
# ⏱️ TEMPO PROCESSAMENTO
# =========================
@st.cache_data(ttl=300)
def buscar_tempo_processamento(data_inicio=None, data_fim=None):
    query = """
        SELECT
            estado, ponto_entrada, hiata, cliente, data,
            qtd_total, qtd_dentro_sla, qtd_fora_sla,
            qtd_sem_saida, tempo_medio_h
        FROM tempo_processamento
        WHERE 1=1
    """
    params = []
    if data_inicio and data_fim:
        query += " AND data BETWEEN %s AND %s"
        params.extend([data_inicio, data_fim])
    else:
        query += " AND data >= CURRENT_DATE - INTERVAL '30 days'"

    return consultar_processamento(query, params)

# =========================
# ⏱️ DEVOLUÇÕES
# =========================
def buscar_devolucoes(limit=1000):
    return consultar_devolucoes("""
        SELECT *
        FROM devolucoes
        ORDER BY data_devolucao DESC
        LIMIT %s
    """, [limit])


# ================================
# 📊 P90 DEVOLUÇÕES
# ================================
@st.cache_data(ttl=300)
def buscar_p90(ano=None, cliente=None):
    """
    Calcula P90 diretamente de dev_detalhado (fonte unificada).
    Mantém a mesma assinatura de retorno: estado, semana, ano, cliente, p90_dias, qtd_pedidos.
    """
    query = """
        SELECT
            estado_dest         AS estado,
            semana,
            ano,
            cliente,
            PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY dias_dev) AS p90_dias,
            COUNT(*)            AS qtd_pedidos
        FROM dev_detalhado
        WHERE status = 'Recebido de devolução'
          AND dias_dev >= 0
          AND estado_dest IS NOT NULL
    """
    params = []

    if ano:
        query += " AND ano = %s"
        params.append(ano)

    query, params = _filtro_cliente(query, params, cliente)
    query += " GROUP BY estado_dest, semana, ano, cliente ORDER BY estado, ano, semana"

    return consultar_devolucoes(query, params if params else None)


# ================================
# 📊 DASHBOARDS DEVOLUÇÃO
# ================================

@st.cache_data(ttl=300)
def buscar_semanas_disponiveis_dev():
    """Retorna semana/ano disponíveis — lê de dev_detalhado (fonte unificada)."""
    return consultar_devolucoes("""
        SELECT DISTINCT semana, ano
        FROM dev_detalhado
        ORDER BY ano DESC, semana DESC
    """)


@st.cache_data(ttl=300)
def buscar_datas_disponiveis_mon():
    """Retorna datas disponíveis em dev_sla_semanal (arquivo diário de Monitoramento)."""
    return consultar_devolucoes("""
        SELECT DISTINCT data_referencia
        FROM dev_sla_semanal
        ORDER BY data_referencia DESC
    """)


@st.cache_data(ttl=300)
def buscar_dev_status_semanal(semana=None, ano=None, cliente=None):
    query = "SELECT estado, status, semana, ano, data_referencia, cliente, cliente_fantasia, qtd FROM dev_status_semanal WHERE 1=1"
    params = []
    if semana:
        query += " AND semana = %s"
        params.append(semana)
    if ano:
        query += " AND ano = %s"
        params.append(ano)
    query, params = _filtro_cliente(query, params, cliente)
    return consultar_devolucoes(query, params if params else None)


@st.cache_data(ttl=300)
def buscar_dev_iatas_semanal(semana=None, ano=None, estado=None, cliente=None):
    """Retorna pré-entregas por estado (col Y do monitoramento) agrupados por semana."""
    query = "SELECT ponto_operacao, estado, semana, ano, qtd FROM dev_iatas_semanal WHERE 1=1"
    params = []
    if semana:
        query += " AND semana = %s"
        params.append(semana)
    if ano:
        query += " AND ano = %s"
        params.append(ano)
    if estado:
        query += " AND estado = %s"
        params.append(estado)
    if cliente:
        query += " AND cliente_fantasia ILIKE %s"
        params.append(f"%{cliente}%")
    query += " ORDER BY qtd DESC"
    return consultar_devolucoes(query, params if params else None)


@st.cache_data(ttl=300)
def buscar_dev_sla_semanal(cliente=None):
    query = """
        SELECT data_referencia, cliente, cliente_fantasia,
               SUM(qtd_total) as qtd_total,
               SUM(qtd_no_prazo) as qtd_no_prazo
        FROM dev_sla_semanal
        WHERE 1=1
    """
    params = []
    query, params = _filtro_cliente(query, params, cliente)
    query += " GROUP BY data_referencia, cliente, cliente_fantasia ORDER BY data_referencia"
    return consultar_devolucoes(query, params if params else None)


@st.cache_data(ttl=300)
def buscar_dev_motivos(data_ref=None, cliente=None):
    query = """
        SELECT motivo, SUM(qtd) as qtd
        FROM dev_motivos_semanal
        WHERE 1=1
    """
    params = []
    if data_ref:
        query += " AND data_referencia = %s"
        params.append(data_ref)
    query, params = _filtro_cliente(query, params, cliente)
    query += " GROUP BY motivo ORDER BY qtd DESC"
    return consultar_devolucoes(query, params if params else None)


def buscar_dev_interceptados(data_ref=None, cliente=None):
    query = """
        SELECT ponto_entrada, estado, SUM(qtd) as qtd
        FROM dev_dsp_sem3tent
        WHERE motivo = 'O pacote foi interceptado'
    """
    params = []
    if data_ref:
        query += " AND data_referencia = %s"
        params.append(data_ref)
    query, params = _filtro_cliente(query, params, cliente)
    query += " GROUP BY ponto_entrada, estado ORDER BY qtd DESC"
    return consultar_devolucoes(query, params if params else None)


@st.cache_data(ttl=300)
def buscar_dev_dsp_sem3tent(data_ref=None, cliente=None):
    query = """
        SELECT ponto_entrada, estado, SUM(qtd) as qtd
        FROM dev_dsp_sem3tent
        WHERE 1=1
    """
    params = []
    if data_ref:
        query += " AND data_referencia = %s"
        params.append(data_ref)
    query, params = _filtro_cliente(query, params, cliente)
    query += " GROUP BY ponto_entrada, estado ORDER BY qtd DESC"
    return consultar_devolucoes(query, params if params else None)


# ================================
# 📊 DEV DETALHADO — P90 por Estado Real
# ================================
@st.cache_data(ttl=600)
def buscar_p90_por_estado_detalhado(semana=None, ano=None, clientes=None):
    query = """
        SELECT
            estado_dest         AS estado,
            semana,
            ano,
            cliente,
            pre_entrega,
            motivo,
            COUNT(*)            AS qtd_pedidos,
            PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY dias_dev) AS p90_dias
        FROM dev_detalhado
        WHERE status = 'Recebido de devolução'
          AND dias_dev >= 0
          AND estado_dest IS NOT NULL
    """
    params = []
    if semana:
        query += " AND semana = %s"
        params.append(semana)
    if ano:
        query += " AND ano = %s"
        params.append(ano)
    query, params = _filtro_cliente(query, params, clientes)
    query += " GROUP BY estado_dest, semana, ano, cliente, pre_entrega, motivo ORDER BY p90_dias DESC"
    return consultar_devolucoes(query, params if params else None)


@st.cache_data(ttl=300)
def buscar_semanas_dev_detalhado():
    return consultar_devolucoes("""
        SELECT DISTINCT semana, ano
        FROM dev_detalhado
        ORDER BY ano DESC, semana DESC
    """)


# =========================
# ⏱️ CALCULO DE PACOTES H1
# =========================
@st.cache_data(ttl=600)
def buscar_tempo_processamento_geral():

    query = """
        SELECT 
            estado,
            ponto_entrada,
            entrada_hub1,
            saida_hub1,
            cliente,
            hiata
        FROM tempo_processamento
        WHERE entrada_hub1 IS NOT NULL
    """

    return consultar_processamento(query)

@st.cache_data(ttl=600)
def buscar_hiata_por_dia(data_inicio=None, data_fim=None):

    query = """
        SELECT
            data,
            hiata,
            SUM(qtd_total) as qtd
        FROM tempo_processamento
        WHERE hiata IS NOT NULL
        AND UPPER(TRIM(hiata)) IN (
            'ES-W-H001',
            'MG-W-H001',
            'PR-W-H001',
            'RJ-W-H001',
            'RS-W-H001',
            'SC-W-H001'
        )
        AND 1=1
    """

    params = []

    # 🔥 PERÍODO
    if data_inicio and data_fim:
        query += " AND data BETWEEN %s AND %s"
        params.extend([data_inicio, data_fim])

    # 🔥 SNAPSHOT
    else:
        query += """
            AND data >= CURRENT_DATE - INTERVAL '30 days'
        """

    query += """
        GROUP BY data, hiata
        ORDER BY data DESC
    """

    return consultar_processamento(query, params)

@st.cache_data(ttl=600)
def buscar_consolidado_por_dia(data_inicio=None, data_fim=None):

    query_prod = """
        SELECT
            data,
            SUM(volumes) as total_perus
        FROM produtividade
        WHERE 1=1
    """

    query_tfk = """
        SELECT
            data,
            SUM(qtd_total) as total_tfk
        FROM tempo_processamento
        WHERE UPPER(TRIM(hiata)) IN (
            'ES-W-H001',
            'MG-W-H001',
            'PR-W-H001',
            'RJ-W-H001',
            'RS-W-H001',
            'SC-W-H001'
        )
        AND 1=1
    """

    params = []

    # 🔥 PERÍODO
    if data_inicio and data_fim:
        query_prod += " AND data BETWEEN %s AND %s"
        query_tfk += " AND data BETWEEN %s AND %s"
        params.extend([data_inicio, data_fim])

    # 🔥 SNAPSHOT
    else:
        query_prod += " AND data >= CURRENT_DATE - INTERVAL '30 days'"
        query_tfk += " AND data >= CURRENT_DATE - INTERVAL '30 days'"

    query_prod += " GROUP BY data"
    query_tfk += " GROUP BY data"

    df_prod = consultar_operacional(query_prod, params)
    df_tfk = consultar_processamento(query_tfk, params)

    df_prod["data"] = pd.to_datetime(df_prod["data"]).dt.date
    df_tfk["data"] = pd.to_datetime(df_tfk["data"]).dt.date

    df = pd.merge(df_prod, df_tfk, on="data", how="outer")

    df["total_perus"] = df["total_perus"].fillna(0)
    df["total_tfk"] = df["total_tfk"].fillna(0)
    df["total_geral"] = df["total_perus"] + df["total_tfk"]

    return df.sort_values("data", ascending=False)


# ================================
# 👥 CLIENTES — mapeamento código → fantasia
# ================================
@st.cache_data(ttl=3600)
def buscar_clientes_fantasia():
    """
    Retorna mapeamento unico de cliente_cod → cliente_fantasia.
    Fonte: dev_sla_semanal (alimentada pelo monitoramento).
    """
    return consultar_devolucoes("""
        SELECT DISTINCT
            cliente         AS cliente_cod,
            cliente_fantasia
        FROM dev_sla_semanal
        WHERE cliente_fantasia IS NOT NULL
          AND cliente_fantasia != ''
        ORDER BY cliente_fantasia
    """)


@st.cache_data(ttl=600)
def buscar_dev_por_cliente_fantasia(cliente_fantasia, semana=None, ano=None):
    """
    Busca dados de SLA filtrados pelo nome fantasia do cliente.
    """
    query = """
        SELECT estado, semana, ano, SUM(qtd_total) as qtd_total,
               SUM(qtd_no_prazo) as qtd_no_prazo
        FROM dev_sla_semanal
        WHERE cliente_fantasia ILIKE %s
    """
    params = [f"%{cliente_fantasia}%"]
    if semana:
        query += " AND semana = %s"
        params.append(semana)
    if ano:
        query += " AND ano = %s"
        params.append(ano)
    query += " GROUP BY estado, semana, ano ORDER BY semana"
    return consultar_devolucoes(query, params)


# ================================
# 📦 PACOTES GRANDES
# ================================
@st.cache_data(ttl=600)
def buscar_pacotes_grandes(semana=None, ano=None):
    query = """
        SELECT
            waybill_mae, waybill, cliente, status,
            estado, cidade, pre_entrega, produto,
            peso_kg, volume_m3, semana, ano
        FROM pacotes_grandes
        WHERE 1=1
    """
    params = []
    if semana:
        query += " AND semana = %s"
        params.append(semana)
    if ano:
        query += " AND ano = %s"
        params.append(ano)
    query += " ORDER BY peso_kg DESC"

    return consultar_operacional(query, params if params else None)


@st.cache_data(ttl=600)
def buscar_semanas_pacotes_grandes():
    return consultar_operacional("""
        SELECT DISTINCT semana, ano
        FROM pacotes_grandes
        ORDER BY ano DESC, semana DESC
    """)

@st.cache_data(ttl=300)
def buscar_datas_coletas(tipo="descarregamento"):
    return consultar_coletas("""
        SELECT DISTINCT data_referencia
        FROM coletas
        WHERE tipo = %s
        ORDER BY data_referencia DESC
    """, [tipo])


@st.cache_data(ttl=300)
def buscar_coletas(data_ref, tipo="descarregamento"):
    return consultar_coletas("""
        SELECT num_registro, placa, motorista, carregador, estado_origem,
               centro_transito, local_carregamento, proximo_ponto,
               tempo_carregamento, tempo_bloqueio, tempo_liberacao,
               ja_descarregado, num_lacre,
               sacos_carregados, sacos_descarregados, sacos_anomalia, sacos_nao_desc, dif_sacos,
               pacotes_carregados, pacotes_descarregados, pacotes_anomalia,
               pacotes_nao_desc, pacotes_triados, pacotes_nao_triados, dif_pacotes
        FROM coletas
        WHERE data_referencia = %s AND tipo = %s
        ORDER BY tempo_carregamento DESC
    """, [data_ref, tipo])


@st.cache_data(ttl=600)
def buscar_semanas_presenca():
    return consultar_operacional("""
        SELECT DISTINCT semana, ano
        FROM presenca_turno
        ORDER BY ano DESC, semana DESC
    """)


@st.cache_data(ttl=600)
def buscar_presenca_turno(semana, ano):
    return consultar_operacional("""
        SELECT *
        FROM presenca_turno
        WHERE semana = %s AND ano = %s
        ORDER BY data, turno
    """, [semana, ano])


@st.cache_data(ttl=600)
def buscar_presenca_diaria(semana, ano):
    return consultar_operacional("""
        SELECT *
        FROM presenca_diaria
        WHERE semana = %s AND ano = %s
        ORDER BY data
    """, [semana, ano])


# =========================
# 🏥 HEALTH CHECK
# =========================
@st.cache_data(ttl=600)
def buscar_semanas_health_check():
    return consultar_processamento("""
        SELECT DISTINCT
            TO_CHAR(data, '"w"IW')            AS semana,
            EXTRACT(YEAR FROM data)::INTEGER   AS ano
        FROM tempo_processamento
        ORDER BY ano DESC, semana DESC
    """)


@st.cache_data(ttl=600)
def buscar_sla_hub(data_inicio, data_fim):
    return consultar_processamento("""
        SELECT
            SUM(qtd_total)      AS total,
            SUM(qtd_dentro_sla) AS dentro,
            SUM(qtd_fora_sla)   AS fora,
            SUM(qtd_sem_saida)  AS sem_info,
            ROUND(
                (SUM(qtd_dentro_sla * tempo_medio_h) /
                 NULLIF(SUM(qtd_dentro_sla), 0))::numeric, 2
            )                   AS lead_medio_h
        FROM tempo_processamento
        WHERE data BETWEEN %s AND %s
    """, [data_inicio, data_fim])


@st.cache_data(ttl=600)
def buscar_backlog_faixas_hc():
    """Retorna backlog 24h e 48h em uma única query para o Health Check."""
    return consultar_backlog("""
        SELECT
            estado,
            pre_entrega,
            SUM(CASE WHEN horas_backlog_snapshot > 24 THEN 1 ELSE 0 END) AS total_24,
            SUM(CASE WHEN horas_backlog_snapshot > 48 THEN 1 ELSE 0 END) AS total_48
        FROM backlog_atual
        GROUP BY estado, pre_entrega
        ORDER BY total_24 DESC
    """)


@st.cache_data(ttl=600)
def buscar_produtividade_turno_hc(data_inicio, data_fim):
    return consultar_operacional("""
        SELECT turno, SUM(volumes) AS volumes
        FROM produtividade
        WHERE data BETWEEN %s AND %s
        GROUP BY turno
        ORDER BY turno
    """, [data_inicio, data_fim])