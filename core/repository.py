from core.database import consultar, executar, conectar_duckdb


def inserir_pedidos_parquet(caminho_parquet):
    executar(f"""
        INSERT INTO pedidos
        SELECT *
        FROM read_parquet('{caminho_parquet}') t
        WHERE NOT EXISTS (
            SELECT 1 FROM pedidos p
            WHERE p.waybill = t.waybill
            AND p.data_referencia = t.data_referencia
        )
    """)


def deletar_arquivo(nome_arquivo):
    executar(
        "DELETE FROM pedidos WHERE nome_arquivo = %s",
        [nome_arquivo]
    )


def listar_arquivos():
    return consultar("""
        SELECT nome_arquivo, COUNT(*) as registros
        FROM pedidos
        GROUP BY nome_arquivo
        ORDER BY nome_arquivo DESC
    """)


def buscar_pedidos():
    return consultar("""
        SELECT 
            waybill,
            cliente,
            estado,
            cidade,
            pre_entrega,
            horas_backlog_snapshot,
            data_referencia
        FROM pedidos
    """)


# 🔥 FUNÇÃO QUE ESTAVA QUEBRANDO
def buscar_backlog_periodo(data_inicio, data_fim):
    return consultar("""
        SELECT 
            waybill,
            cliente,
            estado,
            cidade,
            pre_entrega,
            horas_backlog_snapshot,
            data_referencia
        FROM pedidos
        WHERE status = 'backlog'
        AND data_referencia BETWEEN %s AND %s
        AND horas_backlog_snapshot IS NOT NULL
    """, [data_inicio, data_fim])


def salvar_log_importacao(logs):
    con = conectar_duckdb()
    con.register("logs_temp", logs)

    con.execute("""
        INSERT INTO log_importacoes
        SELECT * FROM logs_temp
    """)