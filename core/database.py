import logging
import os

import pandas as pd
import psycopg2
import streamlit as st
from contextlib import contextmanager
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


# =========================
# 🔗 CONEXÕES DIRETAS COM RECONEXÃO AUTOMÁTICA
# Sem pool — cada query abre e fecha sua própria conexão.
# Elimina PoolError e SSL closed de uma vez.
# =========================

_CONNECT_TIMEOUT = 10  # segundos — evita que o app trave em cold start do Neon


def _conectar(url_env):
    url = os.getenv(url_env)
    if not url:
        raise EnvironmentError(
            f"Variável de ambiente '{url_env}' não configurada. "
            "Verifique o .env (local) ou os Secrets do Streamlit Cloud."
        )
    return psycopg2.connect(url, sslmode="require", connect_timeout=_CONNECT_TIMEOUT)


@contextmanager
def _conn(url_env):
    """Abre conexão, faz retry automático se SSL cair, garante fechamento."""
    conn = _conectar(url_env)
    try:
        yield conn
    finally:
        try:
            conn.close()
        except psycopg2.Error as e:
            logger.warning("Erro ao fechar conexão: %s", e)


def _com_retry(fn):
    try:
        return fn()
    except psycopg2.OperationalError as e:
        logger.warning("Erro operacional no banco, tentando novamente: %s", e)
        return fn()


def _consultar(url_env, query, params=None):
    return _com_retry(lambda: _fazer_consulta(url_env, query, params))


def _fazer_consulta(url_env, query, params):
    with _conn(url_env) as conn:
        return pd.read_sql(query, conn, params=params)


def _executar(url_env, query, params=None):
    return _com_retry(lambda: _fazer_execucao(url_env, query, params))


def _fazer_execucao(url_env, query, params):
    with _conn(url_env) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            conn.commit()


# =========================
# 📊 CONSULTAR
# =========================
def consultar_backlog(query, params=None):       return _consultar("DATABASE_URL_BACKLOG",       query, params)
def consultar_operacional(query, params=None):   return _consultar("DATABASE_URL_OPERACIONAL",   query, params)
def consultar_historico(query, params=None):     return _consultar("DATABASE_URL_HISTORICO",     query, params)
def consultar_devolucoes(query, params=None):    return _consultar("DATABASE_URL_DEVOLUCOES",    query, params)
def consultar_processamento(query, params=None): return _consultar("DATABASE_URL_PROCESSAMENTO", query, params)
def consultar_coletas(query, params=None):       return _consultar("DATABASE_URL_COLETAS",       query, params)


# =========================
# 🚀 EXECUTAR
# =========================
def executar_backlog(query, params=None):       _executar("DATABASE_URL_BACKLOG",       query, params)
def executar_operacional(query, params=None):   _executar("DATABASE_URL_OPERACIONAL",   query, params)
def executar_historico(query, params=None):     _executar("DATABASE_URL_HISTORICO",     query, params)
def executar_devolucoes(query, params=None):    _executar("DATABASE_URL_DEVOLUCOES",    query, params)
def executar_processamento(query, params=None): _executar("DATABASE_URL_PROCESSAMENTO", query, params)
def executar_coletas(query, params=None):       _executar("DATABASE_URL_COLETAS",       query, params)


# =========================
# 🧱 CRIAR TABELAS
# =========================
def inicializar_banco():
    # ── BACKLOG ──────────────────────────────────────────────────────────
    executar_backlog("""
        CREATE TABLE IF NOT EXISTS pedidos (
            waybill TEXT,
            cliente TEXT,
            estado TEXT,
            cidade TEXT,
            pre_entrega TEXT,
            proximo_ponto TEXT,
            entrada_hub1 TIMESTAMP,
            horas_backlog_snapshot DOUBLE PRECISION,
            faixa_backlog_snapshot TEXT,
            data_referencia DATE,
            data_importacao TIMESTAMP,
            nome_arquivo TEXT
        )
    """)

    executar_backlog("""
        CREATE TABLE IF NOT EXISTS backlog_atual (
            waybill TEXT PRIMARY KEY,
            cliente TEXT,
            estado TEXT,
            cidade TEXT,
            pre_entrega TEXT,
            proximo_ponto TEXT,
            entrada_hub1 TIMESTAMP,
            horas_backlog_snapshot DOUBLE PRECISION,
            faixa_backlog_snapshot TEXT,
            data_atualizacao TIMESTAMP
        )
    """)

    # ── HISTÓRICO ─────────────────────────────────────────────────────────
    executar_historico("""
        CREATE TABLE IF NOT EXISTS pedidos_resumo (
            data_referencia         DATE,
            estado                  TEXT,
            cliente                 TEXT,
            pre_entrega             TEXT,
            proximo_ponto           TEXT,
            faixa_backlog_snapshot  TEXT,
            qtd                     INTEGER,
            nome_arquivo            TEXT,
            data_importacao         TIMESTAMP
        )
    """)

    # ── OPERACIONAL ───────────────────────────────────────────────────────
    executar_operacional("""
        CREATE TABLE IF NOT EXISTS produtividade (
            cliente         TEXT,
            data            DATE,
            hora            INTEGER,
            turno           TEXT,
            dispositivo     TEXT,
            volumes         INTEGER,
            nome_arquivo    TEXT,
            data_importacao TIMESTAMP
        )
    """)

    executar_operacional("""
        CREATE TABLE IF NOT EXISTS pacotes_grandes (
            waybill_mae     TEXT,
            waybill         TEXT,
            cliente         TEXT,
            status          TEXT,
            estado          TEXT,
            cidade          TEXT,
            pre_entrega     TEXT,
            produto         TEXT,
            peso_kg         DOUBLE PRECISION,
            volume_m3       DOUBLE PRECISION,
            semana          TEXT,
            ano             INTEGER,
            nome_arquivo    TEXT,
            data_importacao TIMESTAMP
        )
    """)

    executar_operacional("""
        CREATE TABLE IF NOT EXISTS presenca_turno (
            data                    DATE,
            semana                  TEXT,
            ano                     INTEGER,
            turno                   TEXT,
            produzido_turno         INTEGER,
            presenca_turno          INTEGER,
            presenca_total          INTEGER,
            anjun                   INTEGER,
            temporarios             INTEGER,
            diaristas_presenciais   INTEGER,
            faltas_anjun            INTEGER,
            faltas_temporarios      INTEGER,
            perc_falta              DOUBLE PRECISION,
            custo_diaristas         DOUBLE PRECISION,
            custo_por_pedido        DOUBLE PRECISION,
            nome_arquivo            TEXT,
            data_importacao         TIMESTAMP
        )
    """)

    executar_operacional("""
        CREATE TABLE IF NOT EXISTS presenca_diaria (
            data            DATE,
            semana          TEXT,
            ano             INTEGER,
            vol_tfk         INTEGER,
            vol_shein       INTEGER,
            vol_d2d         INTEGER,
            vol_kwai        INTEGER,
            vol_b2c         INTEGER,
            nome_arquivo    TEXT,
            data_importacao TIMESTAMP
        )
    """)

    # ── PROCESSAMENTO ─────────────────────────────────────────────────────
    executar_processamento("""
        CREATE TABLE IF NOT EXISTS tempo_processamento (
            estado          TEXT,
            ponto_entrada   TEXT,
            hiata           TEXT,
            cliente         TEXT,
            data            DATE,
            data_snapshot   DATE,
            qtd_total       INTEGER,
            qtd_dentro_sla  INTEGER,
            qtd_fora_sla    INTEGER,
            qtd_sem_saida   INTEGER,
            tempo_medio_h   DOUBLE PRECISION,
            nome_arquivo    TEXT,
            data_importacao TIMESTAMP
        )
    """)

    # ── DEVOLUÇÕES ────────────────────────────────────────────────────────
    executar_devolucoes("""
        CREATE TABLE IF NOT EXISTS dev_resumo (
            semana          TEXT,
            ano             INTEGER,
            data_referencia DATE,
            status          TEXT,
            cliente         TEXT,
            estado_dest     TEXT,
            motivo          TEXT,
            qtd             INTEGER,
            nome_arquivo    TEXT,
            data_importacao TIMESTAMP
        )
    """)

    executar_devolucoes("""
        CREATE TABLE IF NOT EXISTS dev_detalhado (
            waybill             TEXT,
            status              TEXT,
            tipo_operacao       TEXT,
            cliente             TEXT,
            data_operacao       TIMESTAMP,
            ponto_operacao      TEXT,
            estado_dest         TEXT,
            cidade_dest         TEXT,
            pre_entrega         TEXT,
            ponto_entrada       TEXT,
            motivo              TEXT,
            data_criacao        TIMESTAMP,
            dias_dev            INTEGER,
            semana              TEXT,
            ano                 INTEGER,
            data_referencia     DATE,
            nome_arquivo        TEXT,
            data_importacao     TIMESTAMP
        )
    """)

    executar_devolucoes("""
        CREATE TABLE IF NOT EXISTS p90_semanal (
            estado          TEXT,
            semana          TEXT,
            ano             INTEGER,
            cliente         TEXT,
            p90_dias        DOUBLE PRECISION,
            qtd_pedidos     INTEGER,
            data_referencia DATE,
            nome_arquivo    TEXT,
            data_importacao TIMESTAMP
        )
    """)

    # ── ÍNDICES (performance de queries por data/semana) ─────────────────
    executar_historico("CREATE INDEX IF NOT EXISTS idx_pedidos_resumo_data ON pedidos_resumo (data_referencia)")
    executar_devolucoes("CREATE INDEX IF NOT EXISTS idx_dev_detalhado_data ON dev_detalhado (data_referencia)")
    executar_devolucoes("CREATE INDEX IF NOT EXISTS idx_dev_detalhado_semana ON dev_detalhado (semana, ano)")
    executar_devolucoes("CREATE INDEX IF NOT EXISTS idx_dev_detalhado_status ON dev_detalhado (status) WHERE status = 'Recebido de devolução'")
    executar_devolucoes("CREATE INDEX IF NOT EXISTS idx_dev_detalhado_p90 ON dev_detalhado (semana, ano, estado_dest, cliente) WHERE status = 'Recebido de devolução' AND dias_dev >= 0")
    executar_devolucoes("CREATE INDEX IF NOT EXISTS idx_dev_resumo_semana ON dev_resumo (semana, ano)")
    executar_operacional("CREATE INDEX IF NOT EXISTS idx_produtividade_data ON produtividade (data)")
    executar_processamento("CREATE INDEX IF NOT EXISTS idx_tempo_processamento_data ON tempo_processamento (data)")
    executar_operacional("CREATE INDEX IF NOT EXISTS idx_pacotes_grandes_semana ON pacotes_grandes (semana, ano)")
    executar_operacional("CREATE INDEX IF NOT EXISTS idx_presenca_turno_semana ON presenca_turno (semana, ano)")
    executar_operacional("CREATE INDEX IF NOT EXISTS idx_presenca_diaria_semana ON presenca_diaria (semana, ano)")
    executar_devolucoes("CREATE INDEX IF NOT EXISTS idx_dev_status_semanal_semana ON dev_status_semanal (semana, ano)")
    executar_devolucoes("CREATE INDEX IF NOT EXISTS idx_dev_iatas_semanal_semana ON dev_iatas_semanal (semana, ano)")
    executar_devolucoes("CREATE INDEX IF NOT EXISTS idx_dev_sla_semanal_data ON dev_sla_semanal (data_referencia)")
    executar_devolucoes("CREATE INDEX IF NOT EXISTS idx_dev_sla_semanal_cliente ON dev_sla_semanal (cliente_fantasia)")
    executar_devolucoes("CREATE INDEX IF NOT EXISTS idx_dev_motivos_semanal_data ON dev_motivos_semanal (data_referencia)")
    executar_devolucoes("CREATE INDEX IF NOT EXISTS idx_dev_dsp_sem3tent_data ON dev_dsp_sem3tent (data_referencia)")
    executar_devolucoes("CREATE INDEX IF NOT EXISTS idx_dev_iatas_semanal_estado ON dev_iatas_semanal (semana, ano, estado)")

    # ── COLETAS (banco separado) ───────────────────────────────────────────
    executar_coletas("""
        CREATE TABLE IF NOT EXISTS coletas (
            num_registro            TEXT,
            placa                   TEXT,
            carregador              TEXT,
            rede_carregador         TEXT,
            tempo_carga             TIMESTAMP,
            secao_destino           TEXT,
            descarregador           TEXT,
            rede_descarregador      TEXT,
            tempo_descarga          TIMESTAMP,
            sacos_carregados        INTEGER,
            sacos_descarregados     INTEGER,
            dif_sacos               INTEGER,
            pacotes_carregados      INTEGER,
            pacotes_descarregados   INTEGER,
            dif_pacotes             INTEGER,
            modo_operacao           TEXT,
            tipo_veiculo            TEXT,
            tipo                    TEXT,
            data_referencia         DATE,
            nome_arquivo            TEXT,
            data_importacao         TIMESTAMP
        )
    """)
    executar_coletas("CREATE INDEX IF NOT EXISTS idx_coletas_data ON coletas (data_referencia, tipo)")
