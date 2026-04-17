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
    executar_historico,
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
# 📂 LISTAR ARQUIVOS
# =========================
@st.cache_data(ttl=300)
def listar_arquivos():
    return consultar_historico("""
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
            SUM(qtd)                                            AS qtd,
            SUM(CASE WHEN horas_max > 24 THEN qtd ELSE 0 END)  AS b24,
            SUM(CASE WHEN horas_max > 48 THEN qtd ELSE 0 END)  AS b48,
            SUM(CASE WHEN horas_max > 72 THEN qtd ELSE 0 END)  AS b72,
            SUM(CASE WHEN horas_max > 96 THEN qtd ELSE 0 END)  AS b96
        FROM backlog_atual
        GROUP BY estado, cliente
    """)


# =========================
# 📊 SLA POR ESTADO (agregado no banco)
# =========================
@st.cache_data(ttl=300)
def buscar_sla_por_estado():
    return consultar_backlog("""
        SELECT
            estado,
            SUM(CASE WHEN horas_max <= 24 THEN qtd ELSE 0 END) AS "Até 24h",
            SUM(CASE WHEN horas_max > 24 THEN qtd ELSE 0 END)  AS "+24h",
            SUM(CASE WHEN horas_max > 48 THEN qtd ELSE 0 END)  AS "+48h",
            SUM(CASE WHEN horas_max > 72 THEN qtd ELSE 0 END)  AS "+72h",
            SUM(CASE WHEN horas_max > 96 THEN qtd ELSE 0 END)  AS "+96h",
            SUM(qtd)                                            AS "Total"
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
    return consultar_historico("""
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
def buscar_percentis_operacao(data_inicio=None, data_fim=None):
    """Retorna P50/P80/P90 de tempo de hub por estado/cliente/data."""
    query = """
        SELECT estado, cliente, data, p50_horas, p80_horas, p90_horas, qtd_pedidos
        FROM percentis_operacao
        WHERE 1=1
    """
    params = []
    if data_inicio and data_fim:
        query += " AND data BETWEEN %s AND %s"
        params.extend([data_inicio, data_fim])
    else:
        query += " AND data >= CURRENT_DATE - INTERVAL '30 days'"
    query += " ORDER BY data DESC, estado"
    return consultar_processamento(query, params)


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
@st.cache_data(ttl=1800)
def buscar_p90(ano=None, cliente=None):
    """
    Calcula P90 diretamente de dev_detalhado (fonte unificada).
    Mantém a mesma assinatura de retorno: estado, semana, ano, cliente, p90_dias, qtd_pedidos.
    """
    query = """
        SELECT
            estado_dest AS estado,
            semana,
            ano,
            cliente,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY dias_dev) AS p50_dias,
            PERCENTILE_CONT(0.8) WITHIN GROUP (ORDER BY dias_dev) AS p80_dias,
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

@st.cache_data(ttl=1800)
def buscar_semanas_disponiveis_dev():
    """Retorna semana/ano disponíveis — lê de dev_detalhado (fonte unificada)."""
    return consultar_devolucoes("""
        SELECT DISTINCT semana, ano
        FROM dev_detalhado
        ORDER BY ano DESC, semana DESC
    """)


@st.cache_data(ttl=1800)
def buscar_datas_disponiveis_mon():
    """Retorna datas disponíveis em dev_sla_semanal (arquivo diário de Monitoramento)."""
    return consultar_devolucoes("""
        SELECT DISTINCT data_referencia
        FROM dev_sla_semanal
        ORDER BY data_referencia DESC
    """)


@st.cache_data(ttl=1800)
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


@st.cache_data(ttl=1800)
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


@st.cache_data(ttl=1800)
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


@st.cache_data(ttl=1800)
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


@st.cache_data(ttl=1800)
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


@st.cache_data(ttl=1800)
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
@st.cache_data(ttl=1800)
def buscar_p90_por_estado_detalhado(semana=None, ano=None, clientes=None):
    query = """
        SELECT
            estado_dest AS estado,
            semana,
            ano,
            cliente,
            pre_entrega,
            motivo,
            COUNT(*)            AS qtd_pedidos,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY dias_dev) AS p50_dias,
            PERCENTILE_CONT(0.8) WITHIN GROUP (ORDER BY dias_dev) AS p80_dias,
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


@st.cache_data(ttl=1800)
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

@st.cache_data(ttl=1800)
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

    if df_prod.empty and df_tfk.empty:
        return pd.DataFrame(columns=["data", "total_perus", "total_tfk", "total_geral"])

    if not df_prod.empty:
        df_prod["data"] = pd.to_datetime(df_prod["data"]).dt.date
    if not df_tfk.empty:
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


@st.cache_data(ttl=1800)
def buscar_semanas_pacotes_grandes():
    return consultar_operacional("""
        SELECT DISTINCT semana, ano
        FROM pacotes_grandes
        ORDER BY ano DESC, semana DESC
    """)

@st.cache_data(ttl=1800)
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
        SELECT
            num_registro,
            placa,
            carregador                                          AS motorista,
            rede_carregador                                     AS local_carregamento,
            SPLIT_PART(rede_carregador, '-', 1)                 AS estado_origem,
            tempo_carregamento,
            secao_destino                                       AS proximo_ponto,
            descarregador,
            rede_descarregador,
            tempo_descarga,
            CASE WHEN tempo_descarga IS NOT NULL THEN 'Sim'
                 ELSE 'Não' END                                 AS ja_descarregado,
            sacos_carregados,
            sacos_descarregados,
            dif_sacos,
            pacotes_carregados,
            pacotes_descarregados,
            dif_pacotes,
            modo_operacao,
            tipo_veiculo
        FROM coletas
        WHERE data_referencia = %s AND tipo = %s
        ORDER BY tempo_carregamento DESC
    """, [data_ref, tipo])


@st.cache_data(ttl=1800)
def buscar_datas_coletas_grandes():
    return consultar_coletas("""
        SELECT DISTINCT data_referencia
        FROM coletas_grandes
        ORDER BY data_referencia DESC
    """)


@st.cache_data(ttl=300)
def buscar_coletas_grandes(data_ref):
    return consultar_coletas("""
        SELECT tempo_coleta, cliente, waybill_anjun, waybill_escaneado,
               coletador, estado_origem, placa, motorista
        FROM coletas_grandes
        WHERE data_referencia = %s
        ORDER BY tempo_coleta DESC
    """, [data_ref])


@st.cache_data(ttl=1800)
def buscar_datas_coleta_final():
    return consultar_coletas("""
        SELECT DISTINCT data_referencia
        FROM coleta_final
        ORDER BY data_referencia DESC
    """)


@st.cache_data(ttl=300)
def buscar_coleta_final(data_ref):
    return consultar_coletas("""
        SELECT data, cliente, pac_a_coletar, pac_coletados, taxa_coleta,
               dif_coleta, pedidos_nao_coletados, falta_bipagem_coleta, perda_coleta,
               pac_carregados, dif_carregamento, falta_bipagem_carga, perda_carga
        FROM coleta_final
        WHERE data_referencia = %s
        ORDER BY pac_coletados DESC
    """, [data_ref])


@st.cache_data(ttl=1800)
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
@st.cache_data(ttl=1800)
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


@st.cache_data(ttl=1800)
def buscar_backlog_faixas_hc():
    """Retorna backlog 24h e 48h em uma única query para o Health Check."""
    return consultar_backlog("""
        SELECT
            estado,
            pre_entrega,
            SUM(CASE WHEN horas_max > 24 THEN qtd ELSE 0 END) AS total_24,
            SUM(CASE WHEN horas_max > 48 THEN qtd ELSE 0 END) AS total_48
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


# =========================
# 🛍️ SHEIN BACKLOG
# =========================
@st.cache_data(ttl=1800)
def buscar_shein_datas():
    return consultar_devolucoes("""
        SELECT DISTINCT data_referencia
        FROM dev_shein_sla
        ORDER BY data_referencia DESC
    """)


@st.cache_data(ttl=1800)
def buscar_shein_sla(data_ref=None):
    query = """
        SELECT segmento, qtd_total, qtd_concluido, qtd_pendente, pct_sla
        FROM dev_shein_sla
        WHERE 1=1
    """
    params = []
    if data_ref:
        query += " AND data_referencia = %s"
        params.append(data_ref)
    query += " ORDER BY segmento"
    return consultar_devolucoes(query, params if params else None)


@st.cache_data(ttl=1800)
def buscar_shein_motivos(data_ref=None, segmento=None):
    query = """
        SELECT segmento, motivo, SUM(qtd) AS qtd
        FROM dev_shein_motivos
        WHERE 1=1
    """
    params = []
    if data_ref:
        query += " AND data_referencia = %s"
        params.append(data_ref)
    if segmento:
        query += " AND segmento = %s"
        params.append(segmento)
    query += " GROUP BY segmento, motivo ORDER BY qtd DESC"
    return consultar_devolucoes(query, params if params else None)


@st.cache_data(ttl=1800)
def buscar_shein_aging(data_ref=None, segmento=None):
    query = """
        SELECT segmento, aging_range, SUM(qtd) AS qtd
        FROM dev_shein_aging
        WHERE 1=1
    """
    params = []
    if data_ref:
        query += " AND data_referencia = %s"
        params.append(data_ref)
    if segmento:
        query += " AND segmento = %s"
        params.append(segmento)
    query += " GROUP BY segmento, aging_range ORDER BY segmento, aging_range"
    return consultar_devolucoes(query, params if params else None)


@st.cache_data(ttl=1800)
def buscar_shein_backlog(data_ref=None, segmento=None):
    query = """
        SELECT waybill, segmento, is_d2d, aging_day, aging_range,
               return_initiaded_data, status_folha
        FROM dev_shein_backlog
        WHERE 1=1
    """
    params = []
    if data_ref:
        query += " AND data_referencia = %s"
        params.append(data_ref)
    if segmento:
        query += " AND segmento = %s"
        params.append(segmento)
    query += " ORDER BY aging_day DESC NULLS LAST"
    return consultar_devolucoes(query, params if params else None)