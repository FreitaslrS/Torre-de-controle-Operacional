import streamlit as st
import psycopg2
import psycopg2.pool
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# =========================
# 🔗 POOLS DE CONEXÃO (thread-safe, 1–3 conexões por banco)
# =========================

@st.cache_resource
def _pool_backlog():
    return psycopg2.pool.ThreadedConnectionPool(1, 3, os.getenv("DATABASE_URL_BACKLOG"), sslmode="require")

@st.cache_resource
def _pool_operacional():
    return psycopg2.pool.ThreadedConnectionPool(1, 3, os.getenv("DATABASE_URL_OPERACIONAL"), sslmode="require")

@st.cache_resource
def _pool_historico():
    return psycopg2.pool.ThreadedConnectionPool(1, 3, os.getenv("DATABASE_URL_HISTORICO"), sslmode="require")

@st.cache_resource
def _pool_devolucoes():
    return psycopg2.pool.ThreadedConnectionPool(1, 3, os.getenv("DATABASE_URL_DEVOLUCOES"), sslmode="require")

@st.cache_resource
def _pool_processamento():
    return psycopg2.pool.ThreadedConnectionPool(1, 3, os.getenv("DATABASE_URL_PROCESSAMENTO"), sslmode="require")

@st.cache_resource
def _pool_coletas():
    return psycopg2.pool.ThreadedConnectionPool(1, 3, os.getenv("DATABASE_URL_COLETAS"), sslmode="require")


def _consultar(pool_fn, query, params=None):
    """Pega conexão do pool, executa query, devolve ao pool."""
    pool = pool_fn()
    conn = pool.getconn()
    try:
        return pd.read_sql(query, conn, params=params)
    finally:
        pool.putconn(conn)


def _executar_pool(pool_fn, query, params=None):
    """Pega conexão do pool, executa write, devolve ao pool."""
    pool = pool_fn()
    conn = pool.getconn()
    try:
        cur = conn.cursor()
        cur.execute(query, params or ())
        conn.commit()
        cur.close()
    finally:
        pool.putconn(conn)


# =========================
# 🔗 CONEXÕES DIRETAS (compatível com processar_arquivo.py que usa conn diretamente)
# =========================
def conectar_backlog():       return _pool_backlog().getconn()
def conectar_operacional():   return _pool_operacional().getconn()
def conectar_historico():     return _pool_historico().getconn()
def conectar_devolucoes():    return _pool_devolucoes().getconn()
def conectar_processamento(): return _pool_processamento().getconn()
def conectar_coletas():       return _pool_coletas().getconn()


# =========================
# 📊 CONSULTAR
# =========================
def consultar_backlog(query, params=None):       return _consultar(_pool_backlog,       query, params)
def consultar_operacional(query, params=None):   return _consultar(_pool_operacional,   query, params)
def consultar_historico(query, params=None):     return _consultar(_pool_historico,     query, params)
def consultar_devolucoes(query, params=None):    return _consultar(_pool_devolucoes,    query, params)
def consultar_processamento(query, params=None): return _consultar(_pool_processamento, query, params)
def consultar_coletas(query, params=None):       return _consultar(_pool_coletas,       query, params)


# =========================
# 🚀 EXECUTAR
# =========================
def executar_backlog(query, params=None):       _executar_pool(_pool_backlog,       query, params)
def executar_operacional(query, params=None):   _executar_pool(_pool_operacional,   query, params)
def executar_historico(query, params=None):     _executar_pool(_pool_historico,     query, params)
def executar_devolucoes(query, params=None):    _executar_pool(_pool_devolucoes,    query, params)
def executar_processamento(query, params=None): _executar_pool(_pool_processamento, query, params)
def executar_coletas(query, params=None):       _executar_pool(_pool_coletas,       query, params)


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
