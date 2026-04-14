import streamlit as st
import psycopg2
import os
import pandas as pd
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()


# =========================
# 🔗 CONEXÕES DIRETAS COM RECONEXÃO AUTOMÁTICA
# Sem pool — cada query abre e fecha sua própria conexão.
# Elimina PoolError e SSL closed de uma vez.
# =========================

def _conectar(url_env):
    return psycopg2.connect(os.getenv(url_env), sslmode="require")


@contextmanager
def _conn(url_env):
    """Abre conexão, faz retry automático se SSL cair, garante fechamento."""
    conn = _conectar(url_env)
    try:
        yield conn
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _consultar(url_env, query, params=None):
    try:
        with _conn(url_env) as conn:
            return pd.read_sql(query, conn, params=params)
    except psycopg2.OperationalError:
        # SSL caiu durante a query — reconecta e tenta uma vez
        with _conn(url_env) as conn:
            return pd.read_sql(query, conn, params=params)


def _executar(url_env, query, params=None):
    try:
        with _conn(url_env) as conn:
            cur = conn.cursor()
            cur.execute(query, params or ())
            conn.commit()
            cur.close()
    except psycopg2.OperationalError:
        # SSL caiu — reconecta e tenta uma vez
        with _conn(url_env) as conn:
            cur = conn.cursor()
            cur.execute(query, params or ())
            conn.commit()
            cur.close()


# =========================
# 🔗 CONEXÕES DIRETAS (para processar_arquivo.py — mesma interface de antes)
# =========================
def conectar_backlog():       return _conectar("DATABASE_URL_BACKLOG")
def conectar_operacional():   return _conectar("DATABASE_URL_OPERACIONAL")
def conectar_historico():     return _conectar("DATABASE_URL_HISTORICO")
def conectar_devolucoes():    return _conectar("DATABASE_URL_DEVOLUCOES")
def conectar_processamento(): return _conectar("DATABASE_URL_PROCESSAMENTO")
def conectar_coletas():       return _conectar("DATABASE_URL_COLETAS")


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

    # ── ÍNDICES (performance de queries por data/semana) ─────────────────
    executar_historico("CREATE INDEX IF NOT EXISTS idx_pedidos_resumo_data ON pedidos_resumo (data_referencia)")
    executar_devolucoes("CREATE INDEX IF NOT EXISTS idx_dev_detalhado_data ON dev_detalhado (data_referencia)")
    executar_devolucoes("CREATE INDEX IF NOT EXISTS idx_dev_detalhado_semana ON dev_detalhado (semana, ano)")
    executar_devolucoes("CREATE INDEX IF NOT EXISTS idx_dev_resumo_semana ON dev_resumo (semana, ano)")
    executar_operacional("CREATE INDEX IF NOT EXISTS idx_produtividade_data ON produtividade (data)")
    executar_processamento("CREATE INDEX IF NOT EXISTS idx_tempo_processamento_data ON tempo_processamento (data)")

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
