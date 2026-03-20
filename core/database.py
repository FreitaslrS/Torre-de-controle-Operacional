import duckdb
import os

BASE_DIR = os.path.abspath(os.getcwd())
DB_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DB_DIR, "logistica.db")


def conectar():
    os.makedirs(DB_DIR, exist_ok=True)

    con = duckdb.connect(DB_PATH)

    con.execute("PRAGMA threads=4")
    con.execute("PRAGMA memory_limit='1GB'")

    con.execute("""
        CREATE TABLE IF NOT EXISTS pedidos (
            waybill VARCHAR,
            cliente VARCHAR,
            estado VARCHAR,
            cidade VARCHAR,
            pre_entrega VARCHAR,

            entrada_hub1 TIMESTAMP,
            saida_hub1 TIMESTAMP,
            entrada_hub2 TIMESTAMP,
            saida_hub2 TIMESTAMP,
            entrada_hub3 TIMESTAMP,
            saida_hub3 TIMESTAMP,

            nome_arquivo VARCHAR,
            data_referencia DATE,
            data_importacao TIMESTAMP,

            horas_backlog_snapshot DOUBLE,
            faixa_backlog_snapshot VARCHAR,
            status VARCHAR
        )
    """)

    con.execute("""
        CREATE TABLE IF NOT EXISTS backlog_atual (
            waybill VARCHAR PRIMARY KEY,
            cliente VARCHAR,
            estado VARCHAR,
            cidade VARCHAR,
            pre_entrega VARCHAR,
            entrada_hub1 TIMESTAMP,
            horas_backlog_snapshot DOUBLE,
            faixa_backlog_snapshot VARCHAR,
            data_atualizacao TIMESTAMP
        )
    """)

    con.execute("""
    CREATE TABLE IF NOT EXISTS log_importacoes (
        id INTEGER,
        nome_arquivo VARCHAR,
        status VARCHAR,
        registros INTEGER,
        tempo_segundos DOUBLE,
        data_importacao TIMESTAMP
        )
    """)

    return con