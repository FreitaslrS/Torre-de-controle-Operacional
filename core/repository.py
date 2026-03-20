from core.database import conectar


# =========================
# 📦 INSERÇÃO VIA PARQUET (FUTURO)
# =========================
def inserir_pedidos_parquet(caminho_parquet):
    with conectar() as con:
        con.execute(f"""
            INSERT INTO pedidos
            SELECT *
            FROM read_parquet('{caminho_parquet}') t
            WHERE NOT EXISTS (
                SELECT 1 FROM pedidos p
                WHERE p.waybill = t.waybill
                AND p.data_referencia = t.data_referencia
            )
        """)


# =========================
# 🗑️ DELETAR ARQUIVO
# =========================
def deletar_arquivo(nome_arquivo):
    with conectar() as con:
        con.execute("""
            DELETE FROM pedidos
            WHERE nome_arquivo = ?
        """, [nome_arquivo])


# =========================
# 📄 LISTAR ARQUIVOS
# =========================
def listar_arquivos():
    with conectar() as con:
        return con.execute("""
            SELECT nome_arquivo, COUNT(*) as registros
            FROM pedidos
            GROUP BY nome_arquivo
            ORDER BY nome_arquivo DESC
        """).df()


# =========================
# 📊 BUSCAR TODOS PEDIDOS
# =========================
def buscar_pedidos():
    with conectar() as con:
        return con.execute("""
            SELECT *
            FROM pedidos
        """).df()


# =========================
# 🔥 BACKLOG ATUAL (NOVO)
# =========================
def buscar_backlog_atual():
    with conectar() as con:
        return con.execute("""
            SELECT *
            FROM backlog_atual
        """).df()


# =========================
# 📈 BACKLOG POR PERÍODO
# =========================
def buscar_backlog_periodo(data_inicio, data_fim):
    with conectar() as con:
        return con.execute("""
            SELECT *
            FROM pedidos
            WHERE data_referencia BETWEEN ? AND ?
            AND horas_backlog_snapshot IS NOT NULL
        """, [data_inicio, data_fim]).df()
    
def salvar_log_importacao(logs):
    from core.database import conectar
    con = conectar()

    con.register("logs_temp", logs)

    con.execute("""
        INSERT INTO log_importacoes
        SELECT * FROM logs_temp
    """)