import streamlit as st
import psycopg2
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# =========================
# 🔗 CONEXÕES COM CACHE (1 conexão reutilizada por sessão — leitura)
# =========================

@st.cache_resource
def _conn_backlog():
    return psycopg2.connect(os.getenv("DATABASE_URL_BACKLOG"), sslmode="require")

@st.cache_resource
def _conn_operacional():
    return psycopg2.connect(os.getenv("DATABASE_URL_OPERACIONAL"), sslmode="require")

@st.cache_resource
def _conn_historico():
    return psycopg2.connect(os.getenv("DATABASE_URL_HISTORICO"), sslmode="require")

@st.cache_resource
def _conn_devolucoes():
    return psycopg2.connect(os.getenv("DATABASE_URL_DEVOLUCOES"), sslmode="require")

@st.cache_resource
def _conn_processamento():
    return psycopg2.connect(os.getenv("DATABASE_URL_PROCESSAMENTO"), sslmode="require")


def _get_conn(fn):
    """Retorna conexão cacheada; reconecta se caiu."""
    conn = fn()
    try:
        conn.cursor().execute("SELECT 1")
    except Exception:
        fn.clear()
        conn = fn()
    return conn


# =========================
# 🔗 CONEXÕES DIRETAS (mantém compatibilidade com processar_arquivo.py)
# =========================
def conectar_backlog():       return _get_conn(_conn_backlog)
def conectar_operacional():   return _get_conn(_conn_operacional)
def conectar_historico():     return _get_conn(_conn_historico)
def conectar_devolucoes():    return _get_conn(_conn_devolucoes)
def conectar_processamento(): return _get_conn(_conn_processamento)


# =========================
# 📊 CONSULTAR (usa conexão cacheada — sem overhead de reconexão)
# =========================
def consultar_backlog(query, params=None):
    return pd.read_sql(query, _get_conn(_conn_backlog), params=params)

def consultar_operacional(query, params=None):
    return pd.read_sql(query, _get_conn(_conn_operacional), params=params)

def consultar_historico(query, params=None):
    return pd.read_sql(query, _get_conn(_conn_historico), params=params)

def consultar_devolucoes(query, params=None):
    return pd.read_sql(query, _get_conn(_conn_devolucoes), params=params)

def consultar_processamento(query, params=None):
    return pd.read_sql(query, _get_conn(_conn_processamento), params=params)


# =========================
# 🚀 EXECUTAR (abre conexão nova — correto para writes)
# =========================
def executar_backlog(query, params=None):
    conn = psycopg2.connect(os.getenv("DATABASE_URL_BACKLOG"), sslmode="require")
    cur = conn.cursor()
    cur.execute(query, params or ())
    conn.commit()
    cur.close()
    conn.close()

def executar_operacional(query, params=None):
    conn = psycopg2.connect(os.getenv("DATABASE_URL_OPERACIONAL"), sslmode="require")
    cur = conn.cursor()
    cur.execute(query, params or ())
    conn.commit()
    cur.close()
    conn.close()

def executar_historico(query, params=None):
    conn = psycopg2.connect(os.getenv("DATABASE_URL_HISTORICO"), sslmode="require")
    cur = conn.cursor()
    cur.execute(query, params or ())
    conn.commit()
    cur.close()
    conn.close()

def executar_devolucoes(query, params=None):
    conn = psycopg2.connect(os.getenv("DATABASE_URL_DEVOLUCOES"), sslmode="require")
    cur = conn.cursor()
    cur.execute(query, params or ())
    conn.commit()
    cur.close()
    conn.close()

def executar_processamento(query, params=None):
    conn = psycopg2.connect(os.getenv("DATABASE_URL_PROCESSAMENTO"), sslmode="require")
    cur = conn.cursor()
    cur.execute(query, params or ())
    conn.commit()
    cur.close()
    conn.close()


# =========================
# 🧱 CRIAR TABELAS
# =========================
def inicializar_banco():
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