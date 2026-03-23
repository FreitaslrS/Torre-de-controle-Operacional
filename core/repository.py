from core.database import consultar, executar
from psycopg2.extras import execute_values


# =========================
# 🗑️ DELETE
# =========================
def deletar_arquivo(nome_arquivo):
    executar(
        "DELETE FROM pedidos WHERE nome_arquivo = %s",
        [nome_arquivo]
    )


# =========================
# 📂 LISTAR ARQUIVOS
# =========================
def listar_arquivos():
    return consultar("""
        SELECT 
            nome_arquivo, 
            COUNT(*) as registros
        FROM pedidos
        GROUP BY nome_arquivo
        ORDER BY nome_arquivo DESC
    """)


# =========================
# 📊 PEDIDOS
# =========================
def buscar_pedidos(limit=2000):
    return consultar(f"""
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
        LIMIT {limit}
    """)


# =========================
# 📊 BACKLOG HISTÓRICO
# =========================
def buscar_backlog_historico(data_inicio, data_fim):
    return consultar("""
        SELECT 
            data_referencia,
            estado,
            pre_entrega,
            COUNT(*) as qtd
        FROM pedidos
        WHERE status = 'backlog'
        AND data_referencia BETWEEN %s AND %s
        GROUP BY data_referencia, estado, pre_entrega
    """, [data_inicio, data_fim])


# =========================
# ⚡ BACKLOG ATUAL
# =========================
def buscar_backlog_atual():
    return consultar("""
        SELECT 
            waybill,
            cliente,
            estado,
            cidade,
            pre_entrega,
            horas_backlog_snapshot,
            faixa_backlog_snapshot,
            data_atualizacao
        FROM backlog_atual
    """)


# =========================
# ⚡ PRODUTIVIDADE
# =========================
def buscar_produtividade():
    return consultar("""
        SELECT 
            operador,
            hub,
            data,
            volumes,
            tempo_medio
        FROM produtividade
    """)


# =========================
# 💾 LOG IMPORTAÇÃO (OTIMIZADO)
# =========================
def salvar_log_importacao(logs_df):
    if logs_df.empty:
        return

    from core.database import conectar
    conn = conectar()
    cur = conn.cursor()

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
    cur.close()
    conn.close()