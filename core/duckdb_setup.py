import duckdb

DB_PATH = "database.duckdb"

def criar_banco():
    conn = duckdb.connect(DB_PATH)

    # 🔥 pedidos
    conn.execute("""
    CREATE TABLE IF NOT EXISTS pedidos (
        waybill TEXT,
        cliente TEXT,
        estado TEXT,
        cidade TEXT,
        pre_entrega TEXT,
        proximo_ponto TEXT,
        entrada_hub1 TIMESTAMP,
        saida_hub1 TIMESTAMP,
        entrada_hub2 TIMESTAMP,
        saida_hub2 TIMESTAMP,
        entrada_hub3 TIMESTAMP,
        saida_hub3 TIMESTAMP,
        data_inbound_ponto TIMESTAMP,
        data_entrega TIMESTAMP,
        status_etapa TEXT,
        nome_arquivo TEXT,
        data_referencia DATE,
        data_importacao TIMESTAMP,
        horas_backlog_snapshot DOUBLE,
        faixa_backlog_snapshot TEXT,
        status TEXT
    )
    """)

    # 🔥 backlog atual
    conn.execute("""
    CREATE TABLE IF NOT EXISTS backlog_atual (
        waybill TEXT,
        cliente TEXT,
        estado TEXT,
        cidade TEXT,
        pre_entrega TEXT,
        proximo_ponto TEXT,
        entrada_hub1 TIMESTAMP,
        horas_backlog_snapshot DOUBLE,
        faixa_backlog_snapshot TEXT,
        data_atualizacao TIMESTAMP
    )
    """)

    # 🔥 produtividade
    conn.execute("""
    CREATE TABLE IF NOT EXISTS produtividade (
        cliente TEXT,
        estado TEXT,
        hub TEXT,
        operador TEXT,
        data DATE,
        hora INTEGER,
        turno TEXT,
        dispositivo TEXT,
        volumes INTEGER
    )
    """)

    # 🔥 tempo processamento
    conn.execute("""
    CREATE TABLE IF NOT EXISTS tempo_processamento (
        estado TEXT,
        ponto_entrada TEXT,
        entrada_hub1 TIMESTAMP,
        saida_hub1 TIMESTAMP,
        cliente TEXT,
        hiata TEXT,
        data DATE,
        data_snapshot DATE
    )
    """)

    conn.close()