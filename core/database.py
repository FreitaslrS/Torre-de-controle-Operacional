import psycopg2
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# =========================
# 🔗 CONEXÃO NEON
# =========================
def conectar_postgres():
    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        raise Exception("DATABASE_URL não configurada!")

    return psycopg2.connect(
        DATABASE_URL,
        connect_timeout=10,
        sslmode="require"
    )


def conectar():
    return conectar_postgres()


# =========================
# 🚀 EXECUTAR
# =========================
def executar(query, params=None):
    conn = conectar()
    cur = conn.cursor()

    cur.execute(query, params or ())
    conn.commit()

    cur.close()
    conn.close()


# =========================
# 📊 CONSULTAR (OTIMIZADO)
# =========================
def consultar(query, params=None):
    conn = conectar()

    df = pd.read_sql(query, conn, params=params)

    conn.close()
    return df


# =========================
# 🧱 CRIAR TABELAS
# =========================
def inicializar_banco():
    executar("""
        CREATE TABLE IF NOT EXISTS pedidos (
            waybill TEXT,
            cliente TEXT,
            estado TEXT,
            cidade TEXT,
            pre_entrega TEXT,
            entrada_hub1 TIMESTAMP,
            saida_hub1 TIMESTAMP,
            entrada_hub2 TIMESTAMP,
            saida_hub2 TIMESTAMP,
            entrada_hub3 TIMESTAMP,
            saida_hub3 TIMESTAMP,
            nome_arquivo TEXT,
            data_referencia DATE,
            data_importacao TIMESTAMP,
            horas_backlog_snapshot DOUBLE PRECISION,
            faixa_backlog_snapshot TEXT,
            status TEXT
        )
    """)

    executar("""
        CREATE TABLE IF NOT EXISTS backlog_atual (
            waybill TEXT PRIMARY KEY,
            cliente TEXT,
            estado TEXT,
            cidade TEXT,
            pre_entrega TEXT,
            entrada_hub1 TIMESTAMP,
            horas_backlog_snapshot DOUBLE PRECISION,
            faixa_backlog_snapshot TEXT,
            data_atualizacao TIMESTAMP
        )
    """)

    executar("""
        CREATE TABLE IF NOT EXISTS produtividade (
            operador TEXT,
            hub TEXT,
            data DATE,
            volumes INTEGER,
            tempo_medio DOUBLE PRECISION,
            nome_arquivo TEXT,
            data_importacao TIMESTAMP
        )
    """)

    # LOG
    executar("""
        CREATE TABLE IF NOT EXISTS log_importacoes (
            id INTEGER,
            nome_arquivo TEXT,
            status TEXT,
            registros INTEGER,
            tempo_segundos DOUBLE PRECISION,
            data_importacao TIMESTAMP
        )
    """)