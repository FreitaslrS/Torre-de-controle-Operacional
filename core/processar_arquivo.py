import io
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from psycopg2.extras import execute_values
from core.database import (
    consultar_backlog,
    executar_historico,
    executar_devolucoes,
    executar_operacional,
    executar_processamento,
    _conn,
)


# ================================
# ⚡ LEITURA RÁPIDA: XLSX → Parquet em memória
# ================================
def xlsx_para_dataframe(arquivo, engine="openpyxl", **kwargs):
    """
    Lê XLSX, converte para Parquet em memória (snappy) e retorna
    um DataFrame columnar — ~3-10x mais rápido para manipulação
    em arquivos grandes (+10k linhas).
    """
    df = pd.read_excel(arquivo, engine=engine, **kwargs)
    with io.BytesIO() as buf:
        df.to_parquet(buf, index=False, compression="snappy")
        buf.seek(0)
        return pd.read_parquet(buf)


# ================================
# 🧹 LIMPEZA AUTOMÁTICA — 90 DIAS
# ================================
def limpar_historico_antigo():
    try:
        executar_operacional("""
            DELETE FROM produtividade
            WHERE data < CURRENT_DATE - INTERVAL '90 days'
        """)
        executar_processamento("""
            DELETE FROM tempo_processamento
            WHERE data < CURRENT_DATE - INTERVAL '90 days'
        """)
        executar_historico("""
            DELETE FROM pedidos_resumo
            WHERE data_referencia < CURRENT_DATE - INTERVAL '90 days'
        """)
        executar_historico("""
            DELETE FROM pedidos
            WHERE data_referencia < CURRENT_DATE - INTERVAL '7 days'
        """)
        executar_devolucoes("""
            DELETE FROM dev_status_semanal
            WHERE data_importacao < CURRENT_DATE - INTERVAL '90 days'
        """)
        executar_devolucoes("""
            DELETE FROM dev_iatas_semanal
            WHERE data_importacao < CURRENT_DATE - INTERVAL '90 days'
        """)
        executar_devolucoes("""
            DELETE FROM dev_sla_semanal
            WHERE data_importacao < CURRENT_DATE - INTERVAL '90 days'
        """)
        executar_devolucoes("""
            DELETE FROM dev_motivos_semanal
            WHERE data_importacao < CURRENT_DATE - INTERVAL '90 days'
        """)
        executar_devolucoes("""
            DELETE FROM dev_dsp_sem3tent
            WHERE data_importacao < CURRENT_DATE - INTERVAL '90 days'
        """)
        executar_devolucoes("""
            DELETE FROM p90_semanal
            WHERE data_importacao < CURRENT_DATE - INTERVAL '90 days'
        """)
    except Exception as e:
        print(f"⚠️ Erro na limpeza automática: {e}")


def limpar_base():
    executar_historico("""
        DELETE FROM pedidos
        WHERE data_referencia < CURRENT_DATE - INTERVAL '30 days'
    """)


def importar_excel(arquivo, data_referencia):
    # Lê só colunas necessárias
    df = xlsx_para_dataframe(
        arquivo,
        usecols=[0, 11, 12, 21, 24, 25, 41, 42, 43, 48, 56]
    )
    df.columns = [
        "waybill", "estado", "cidade", "cliente",
        "pre_entrega", "ponto_entrada",
        "entrada_hub1", "saida_hub1", "proximo_ponto",
        "entrada_hub2", "entrada_hub3"
    ]

    df["waybill"] = df["waybill"].astype(str).str.strip()
    df = df[df["waybill"].str.lower() != "nan"]

    for col in ["entrada_hub1", "saida_hub1", "entrada_hub2", "entrada_hub3"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # Filtra só backlog real (parado no hub1)
    df_backlog = df[
        df["entrada_hub1"].notna() &
        df["saida_hub1"].isna() &
        df["entrada_hub2"].isna() &
        df["entrada_hub3"].isna()
    ].copy()

    if df_backlog.empty:
        return 0

    agora = pd.to_datetime(data_referencia)

    df_backlog["horas_backlog_snapshot"] = (
        (agora - df_backlog["entrada_hub1"]).dt.total_seconds() / 3600
    )

    def classificar_faixa(h):
        if pd.isna(h) or h < 0: return None
        elif h <= 24:   return "1 dia"
        elif h <= 120:  return "1-5 dias"
        elif h <= 240:  return "5-10 dias"
        elif h <= 480:  return "10-20 dias"
        elif h <= 720:  return "20-30 dias"
        else:           return "30+ dias"

    df_backlog["faixa_backlog_snapshot"] = df_backlog["horas_backlog_snapshot"].apply(classificar_faixa)
    df_backlog["data_referencia"]        = agora.date()
    df_backlog["data_importacao"]        = datetime.now(timezone.utc)
    df_backlog["nome_arquivo"]           = arquivo.name
    df_backlog["proximo_ponto"]          = df_backlog["proximo_ponto"].fillna("Sem informação")

    # ── CAMADA 1: backlog_atual (snapshot atual por waybill) ──────────
    existentes     = consultar_backlog("SELECT waybill FROM backlog_atual")
    existentes_set = set(existentes["waybill"]) if not existentes.empty else set()
    novos_set      = set(df_backlog["waybill"])

    removidos = existentes_set - novos_set
    with _conn("DATABASE_URL_BACKLOG") as conn:
        cur = conn.cursor()
        if removidos:
            cur.execute("DELETE FROM backlog_atual WHERE waybill = ANY(%s)", (list(removidos),))
        execute_values(cur, """
            INSERT INTO backlog_atual (
                waybill, cliente, estado, cidade, pre_entrega,
                proximo_ponto, entrada_hub1,
                horas_backlog_snapshot, faixa_backlog_snapshot
            ) VALUES %s
            ON CONFLICT (waybill) DO UPDATE SET
                horas_backlog_snapshot = EXCLUDED.horas_backlog_snapshot,
                faixa_backlog_snapshot = EXCLUDED.faixa_backlog_snapshot,
                proximo_ponto          = EXCLUDED.proximo_ponto,
                data_atualizacao       = NOW()
        """, [
            (row["waybill"], row["cliente"], row["estado"], row["cidade"],
             row["pre_entrega"], row["proximo_ponto"], row["entrada_hub1"],
             row["horas_backlog_snapshot"], row["faixa_backlog_snapshot"])
            for _, row in df_backlog.iterrows()
        ])
        conn.commit()
        cur.close()

    # ── CAMADA 2: pedidos_resumo (agregado para gráficos históricos) ──
    df_resumo = (
        df_backlog.groupby([
            "data_referencia", "estado", "cliente",
            "pre_entrega", "proximo_ponto", "faixa_backlog_snapshot"
        ])
        .size()
        .reset_index(name="qtd")
    )
    df_resumo["nome_arquivo"]    = arquivo.name
    df_resumo["data_importacao"] = datetime.now(timezone.utc)

    with _conn("DATABASE_URL_HISTORICO") as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM pedidos_resumo WHERE nome_arquivo = %s", [arquivo.name])

        colunas_resumo = [
            "data_referencia", "estado", "cliente", "pre_entrega",
            "proximo_ponto", "faixa_backlog_snapshot", "qtd",
            "nome_arquivo", "data_importacao"
        ]
        execute_values(cur,
            f"INSERT INTO pedidos_resumo ({','.join(colunas_resumo)}) VALUES %s",
            [tuple(None if pd.isna(v) else v for v in row)
             for row in df_resumo[colunas_resumo].itertuples(index=False, name=None)]
        )

        # ── CAMADA 3: pedidos bruto — só 7 dias para drill down ──────────
        cur.execute("DELETE FROM pedidos WHERE data_referencia = %s", [agora.date()])
        cur.execute("DELETE FROM pedidos WHERE data_referencia < CURRENT_DATE - INTERVAL '7 days'")

        colunas_bruto = [
            "waybill", "cliente", "estado", "cidade", "pre_entrega", "proximo_ponto",
            "entrada_hub1", "horas_backlog_snapshot", "faixa_backlog_snapshot",
            "data_referencia", "data_importacao", "nome_arquivo"
        ]
        execute_values(cur,
            f"INSERT INTO pedidos ({','.join(colunas_bruto)}) VALUES %s",
            [tuple(None if pd.isna(v) else v for v in row)
             for row in df_backlog[colunas_bruto].itertuples(index=False, name=None)]
        )
        conn.commit()
        cur.close()

    limpar_historico_antigo()
    return len(df_backlog)


def importar_produtividade(arquivo):
    # Colunas: D=3 (cliente), I=8 (data_hora), U=20 (operador)
    df = xlsx_para_dataframe(arquivo, usecols=[3, 8, 20])
    df.columns = ["cliente", "data_hora", "operador"]

    if df.empty:
        return 0

    df = df[df["data_hora"].notna()]
    df["data_hora"] = pd.to_datetime(df["data_hora"], errors="coerce")
    df = df[df["data_hora"].notna()]

    # Remove devoluções e operadores MG
    mask_remover = (
        df["operador"].astype(str).str.upper().str.contains("DEVOL", na=False) |
        df["operador"].astype(str).str.upper().str.startswith("MG", na=False)
    )
    df = df[~mask_remover]

    if df.empty:
        return 0

    # Dispositivo
    def classificar_dispositivo(op):
        op = str(op).strip().upper()
        if "PERUS01" in op:
            return "Sorter Oval"
        elif "PERUS02" in op:
            return "Sorter Linear"
        else:
            return "Cubometro"

    df["dispositivo"] = df["operador"].apply(classificar_dispositivo)

    # Turno + data operacional (T3 madrugada = dia anterior)
    def classificar_turno_e_data(dt):
        minuto_total = dt.hour * 60 + dt.minute
        if 330 <= minuto_total <= 829:       # 05:30–13:49
            return "T1", dt.date()
        elif 830 <= minuto_total <= 1319:    # 13:50–21:59
            return "T2", dt.date()
        else:                                # 22:00–05:29 (T3)
            data_op = (dt - pd.Timedelta(days=1)).date() if dt.hour < 6 else dt.date()
            return "T3", data_op

    turnos_datas = df["data_hora"].apply(
        lambda dt: pd.Series(classificar_turno_e_data(dt), index=["turno", "data"])
    )
    df[["turno", "data"]] = turnos_datas
    df["hora"] = df["data_hora"].dt.hour

    df_agg = (
        df.groupby(["cliente", "data", "hora", "turno", "dispositivo"])
        .size()
        .reset_index(name="volumes")
    )

    df_agg["nome_arquivo"]    = arquivo.name
    df_agg["data_importacao"] = datetime.now(timezone.utc)

    with _conn("DATABASE_URL_OPERACIONAL") as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM produtividade WHERE nome_arquivo = %s", [arquivo.name])
        colunas = ["cliente", "data", "hora", "turno", "dispositivo", "volumes", "nome_arquivo", "data_importacao"]
        values  = [tuple(None if pd.isna(v) else v for v in row)
                   for row in df_agg[colunas].itertuples(index=False, name=None)]
        execute_values(cur, f"INSERT INTO produtividade ({','.join(colunas)}) VALUES %s", values)
        conn.commit()
        cur.close()

    # View materializada substituída por query direta em buscar_produtividade()
    # Não é mais necessário fazer REFRESH

    limpar_historico_antigo()
    return len(df_agg)


def importar_tempo_processamento(arquivo):
    # Lê só colunas necessárias
    df = xlsx_para_dataframe(
        arquivo,
        usecols=[0, 11, 21, 24, 25, 41, 42, 43]
    )
    df.columns = [
        "waybill", "estado", "cliente",
        "pre_entrega", "ponto_entrada",
        "entrada_hub1", "saida_hub1", "hiata"
    ]

    if df.empty:
        return 0

    df["entrada_hub1"] = pd.to_datetime(df["entrada_hub1"], errors="coerce")
    df["saida_hub1"]   = pd.to_datetime(df["saida_hub1"],   errors="coerce")
    df = df[df["entrada_hub1"].notna()]
    df["data"] = df["entrada_hub1"].dt.date

    # Tempo em horas
    df["tempo_horas"] = (
        (df["saida_hub1"] - df["entrada_hub1"])
        .dt.total_seconds() / 3600
    )

    # Remove tempos absurdos
    df = df[
        (df["tempo_horas"].isna()) |
        ((df["tempo_horas"] >= 0) & (df["tempo_horas"] <= 240))
    ]

    # Hiata padronizado
    df["hiata"] = df["hiata"].astype(str).str.strip().str.upper()

    # Status SLA por linha
    def classificar_status(row):
        if pd.isna(row["saida_hub1"]):
            return "sem_saida"
        elif row["tempo_horas"] <= 24:
            return "dentro_sla"
        else:
            return "fora_sla"

    df["status"] = df.apply(classificar_status, axis=1)

    # Agrega — de 178k linhas para ~500
    agg = df.groupby(["estado", "ponto_entrada", "hiata", "cliente", "data"]).agg(
        qtd_total      = ("waybill",     "count"),
        qtd_dentro_sla = ("status",      lambda x: (x == "dentro_sla").sum()),
        qtd_fora_sla   = ("status",      lambda x: (x == "fora_sla").sum()),
        qtd_sem_saida  = ("status",      lambda x: (x == "sem_saida").sum()),
        tempo_medio_h  = ("tempo_horas", lambda x: x.dropna().mean() if x.dropna().any() else None)
    ).reset_index()

    agg["data_snapshot"]   = datetime.now(timezone.utc).date()
    agg["nome_arquivo"]    = arquivo.name
    agg["data_importacao"] = datetime.now(timezone.utc)

    with _conn("DATABASE_URL_PROCESSAMENTO") as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM tempo_processamento WHERE nome_arquivo = %s", [arquivo.name])
        colunas = [
            "estado", "ponto_entrada", "hiata", "cliente", "data",
            "data_snapshot", "qtd_total", "qtd_dentro_sla", "qtd_fora_sla",
            "qtd_sem_saida", "tempo_medio_h", "nome_arquivo", "data_importacao"
        ]
        values = [tuple(None if pd.isna(v) else v for v in row)
                  for row in agg[colunas].itertuples(index=False, name=None)]
        execute_values(cur, f"INSERT INTO tempo_processamento ({','.join(colunas)}) VALUES %s", values)
        conn.commit()
        cur.close()

    limpar_historico_antigo()
    return len(agg)


# ================================
# 📊 DEVOLUÇÃO — P90
# ================================
def importar_p90(arquivo, data_ref):
    df = xlsx_para_dataframe(arquivo)

    if df.empty:
        return 0

    df.columns = [
        "waybill", "status", "tipo_operacao", "cliente",
        "data_operacao", "proximo_ponto", "operador",
        "ponto_operacao", "estado", "regiao"
    ]

    # Filtra só "Recebido de devolução"
    df = df[df["status"] == "Recebido de devolução"].copy()

    if df.empty:
        return 0

    df["data_operacao"] = pd.to_datetime(df["data_operacao"], errors="coerce")
    df = df[df["data_operacao"].notna()]

    # Extrai data de criação do código do waybill (AJ AAMMDD...)
    def extrair_data_criacao(waybill):
        try:
            w = str(waybill).strip()
            ano = int("20" + w[2:4])
            mes = int(w[4:6])
            dia = int(w[6:8])
            return pd.Timestamp(ano, mes, dia)
        except Exception:
            return None

    df["data_criacao"] = df["waybill"].apply(extrair_data_criacao)
    df = df[df["data_criacao"].notna()]

    # Dias corridos: criação → recebimento devolução
    df["dias"] = (df["data_operacao"] - df["data_criacao"]).dt.days
    df = df[df["dias"] >= 0]

    if df.empty:
        return 0

    # Semana e ano forçados pela data de referência selecionada pelo usuário
    ref_ts = pd.Timestamp(data_ref)
    df["semana"] = ref_ts.strftime("w%V")
    df["ano"]    = int(ref_ts.year)

    # Agrega por estado + semana + ano + cliente
    agg = (
        df.groupby(["estado", "semana", "ano", "cliente"])
        .agg(
            p90_dias    = ("dias", lambda x: round(float(np.percentile(x, 90)), 1)),
            qtd_pedidos = ("dias", "count")
        )
        .reset_index()
    )

    agg["data_referencia"] = data_ref
    agg["nome_arquivo"]    = arquivo.name
    agg["data_importacao"] = datetime.now(timezone.utc)

    with _conn("DATABASE_URL_DEVOLUCOES") as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM p90_semanal WHERE nome_arquivo = %s", [arquivo.name])
        colunas = [
            "estado", "semana", "ano", "cliente", "p90_dias",
            "qtd_pedidos", "data_referencia", "nome_arquivo", "data_importacao"
        ]
        values = [
            tuple(None if pd.isna(v) else v for v in row)
            for row in agg[colunas].itertuples(index=False, name=None)
        ]
        execute_values(cur, f"INSERT INTO p90_semanal ({','.join(colunas)}) VALUES %s", values)
        conn.commit()
        cur.close()

    limpar_historico_antigo()
    return len(agg)


# ================================
# 🔁 DEVOLUÇÃO (arquivo Folha_de_registro)
# ================================
def importar_devolucoes(arquivo, data_ref):
    df = xlsx_para_dataframe(arquivo)

    if df.empty:
        return 0

    df.columns = [
        "waybill", "status", "tipo_operacao", "cliente",
        "data_operacao", "proximo_ponto", "operador",
        "ponto_operacao", "estado", "regiao"
    ]

    # Deriva semana e ano a partir da data de referência
    data_ref_ts = pd.Timestamp(data_ref)
    semana = data_ref_ts.strftime("w%V")
    ano    = int(data_ref_ts.year)

    agora = datetime.now(timezone.utc)

    status_agg = (
        df.groupby(["status", "estado", "cliente"])
        .size()
        .reset_index(name="qtd")
    )
    status_agg["semana"]           = semana
    status_agg["ano"]              = ano
    status_agg["data_referencia"]  = data_ref
    status_agg["nome_arquivo"]     = arquivo.name
    status_agg["data_importacao"]  = agora
    status_agg["cliente_fantasia"] = None

    iata_agg = (
        df.groupby(["ponto_operacao", "estado"])
        .size()
        .reset_index(name="qtd")
    )
    iata_agg["semana"]           = semana
    iata_agg["ano"]              = ano
    iata_agg["data_referencia"]  = data_ref
    iata_agg["nome_arquivo"]     = arquivo.name
    iata_agg["data_importacao"]  = agora
    iata_agg["cliente_fantasia"] = None

    colunas_status = [
        "estado", "status", "semana", "ano", "data_referencia", "cliente",
        "cliente_fantasia", "qtd", "nome_arquivo", "data_importacao"
    ]
    colunas_iata = [
        "ponto_operacao", "estado", "semana", "ano", "data_referencia",
        "cliente_fantasia", "qtd", "nome_arquivo", "data_importacao"
    ]

    with _conn("DATABASE_URL_DEVOLUCOES") as conn:
        cur = conn.cursor()
        for tabela in ["dev_status_semanal", "dev_iatas_semanal"]:
            cur.execute(f"DELETE FROM {tabela} WHERE nome_arquivo = %s", [arquivo.name])
        execute_values(cur,
            f"INSERT INTO dev_status_semanal ({','.join(colunas_status)}) VALUES %s",
            [tuple(None if pd.isna(v) else v for v in row)
             for row in status_agg[colunas_status].itertuples(index=False, name=None)]
        )
        execute_values(cur,
            f"INSERT INTO dev_iatas_semanal ({','.join(colunas_iata)}) VALUES %s",
            [tuple(None if pd.isna(v) else v for v in row)
             for row in iata_agg[colunas_iata].itertuples(index=False, name=None)]
        )
        conn.commit()
        cur.close()

    limpar_historico_antigo()
    return len(status_agg) + len(iata_agg)


# ================================
# 📊 DEVOLUÇÃO - MONITORAMENTO (arquivo monitoramento_da_pontualidade)
# ================================
def importar_devolucao_monitoramento(arquivo, data_ref):
    df = xlsx_para_dataframe(
        arquivo,
        usecols=[0, 4, 8, 11, 21, 22, 25, 33, 66, 67, 68, 71, 73]
    )
    df.columns = [
        "waybill", "status", "motivo", "estado", "cliente",
        "cliente_fantasia", "ponto_entrada", "data_criacao",
        "tent1", "tent2", "tent3", "assinatura", "prazo_dias"
    ]

    if df.empty:
        return 0

    for col in ["tent1", "tent2", "tent3", "assinatura", "data_criacao"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    agora       = datetime.now(timezone.utc)
    sla_agg     = pd.DataFrame()
    motivos_agg = pd.DataFrame()
    dsp_agg     = pd.DataFrame()
    colunas_sla = ["estado", "data_referencia", "cliente", "cliente_fantasia", "qtd_total", "qtd_no_prazo", "nome_arquivo", "data_importacao"]
    colunas_mot = ["estado", "motivo", "cliente", "cliente_fantasia", "data_referencia", "qtd", "nome_arquivo", "data_importacao"]
    colunas_dsp = ["ponto_entrada", "estado", "motivo", "cliente", "cliente_fantasia", "data_referencia", "qtd", "nome_arquivo", "data_importacao"]

    df_entregues = df[df["assinatura"].notna()].copy()
    if not df_entregues.empty:
        df_entregues["dias"]     = (df_entregues["assinatura"] - df_entregues["data_criacao"]).dt.total_seconds() / 86400
        df_entregues["prazo"]    = df_entregues["prazo_dias"].fillna(7)
        df_entregues["no_prazo"] = df_entregues["dias"] <= df_entregues["prazo"]
        sla_agg = (
            df_entregues.groupby(["estado", "cliente", "cliente_fantasia"])
            .agg(qtd_total=("waybill", "count"), qtd_no_prazo=("no_prazo", "sum"))
            .reset_index()
        )
        sla_agg["data_referencia"] = data_ref
        sla_agg["nome_arquivo"]    = arquivo.name
        sla_agg["data_importacao"] = agora

    df_motivos = df[df["motivo"].notna()].copy()
    if not df_motivos.empty:
        motivos_agg = (
            df_motivos.groupby(["estado", "motivo", "cliente", "cliente_fantasia"])
            .size().reset_index(name="qtd")
        )
        motivos_agg["data_referencia"] = data_ref
        motivos_agg["nome_arquivo"]    = arquivo.name
        motivos_agg["data_importacao"] = agora

    dsp_sem3 = df[
        df["motivo"].notna() & df["tent1"].notna() &
        df["tent3"].isna()   & df["assinatura"].isna()
    ].copy()
    if not dsp_sem3.empty:
        dsp_agg = (
            dsp_sem3.groupby(["ponto_entrada", "estado", "motivo", "cliente", "cliente_fantasia"])
            .size().reset_index(name="qtd")
        )
        dsp_agg["data_referencia"] = data_ref
        dsp_agg["nome_arquivo"]    = arquivo.name
        dsp_agg["data_importacao"] = agora

    with _conn("DATABASE_URL_DEVOLUCOES") as conn:
        cur = conn.cursor()
        for tabela in ["dev_sla_semanal", "dev_motivos_semanal", "dev_dsp_sem3tent"]:
            cur.execute(f"DELETE FROM {tabela} WHERE nome_arquivo = %s", [arquivo.name])
        if not sla_agg.empty:
            execute_values(cur,
                f"INSERT INTO dev_sla_semanal ({','.join(colunas_sla)}) VALUES %s",
                [tuple(None if pd.isna(v) else v for v in row)
                 for row in sla_agg[colunas_sla].itertuples(index=False, name=None)]
            )
        if not motivos_agg.empty:
            execute_values(cur,
                f"INSERT INTO dev_motivos_semanal ({','.join(colunas_mot)}) VALUES %s",
                [tuple(None if pd.isna(v) else v for v in row)
                 for row in motivos_agg[colunas_mot].itertuples(index=False, name=None)]
            )
        if not dsp_agg.empty:
            execute_values(cur,
                f"INSERT INTO dev_dsp_sem3tent ({','.join(colunas_dsp)}) VALUES %s",
                [tuple(None if pd.isna(v) else v for v in row)
                 for row in dsp_agg[colunas_dsp].itertuples(index=False, name=None)]
            )
        conn.commit()
        cur.close()

    limpar_historico_antigo()
    return len(sla_agg) + len(motivos_agg) + len(dsp_agg)


# ================================
# 📦 PACOTES GRANDES (AJG)
# ================================
def importar_pacotes_grandes(arquivo, data_ref=None):
    df = xlsx_para_dataframe(arquivo)

    if df.empty:
        return 0

    df.columns = [
        "data_criacao", "cliente", "id_cliente", "pedido_cliente", "waybill_mae",
        "qtd_pecas", "waybill", "status", "data_status", "pre_entrega", "regiao",
        "metodo_entrega", "tipo_area", "cep_dest", "nome_dest", "estado",
        "rua_dest", "num_dest", "bairro_dest", "cidade", "end_dest",
        "cep_rem", "nome_rem", "estado_rem", "av_rem", "num_rem", "area_rem",
        "cidade_rem", "end_rem", "pagamento", "peso_kg", "volume_m3",
        "carga_transf", "vol_transito", "peso_cobranca", "ponto_entrega",
        "entregador", "sku", "produto", "qtd_entregadores", "anomalias"
    ]

    df["data_status"]  = pd.to_datetime(df["data_status"],  errors="coerce")
    df["data_criacao"] = pd.to_datetime(df["data_criacao"], errors="coerce")

    # Semana e ano forçados pela data de referência selecionada pelo usuário
    if data_ref is not None:
        ref_ts = pd.Timestamp(data_ref)
        df["semana"] = ref_ts.strftime("w%V")
        df["ano"]    = int(ref_ts.year)
    else:
        df["semana"] = df["data_criacao"].dt.strftime("w%V")
        df["ano"]    = df["data_criacao"].dt.year
    df["nome_arquivo"]    = arquivo.name
    df["data_importacao"] = datetime.now(timezone.utc)

    colunas = [
        "waybill_mae", "waybill", "cliente", "status", "data_status",
        "estado", "cidade", "pre_entrega", "produto", "peso_kg", "volume_m3",
        "semana", "ano", "nome_arquivo", "data_importacao"
    ]
    values = [
        tuple(None if pd.isna(v) else v for v in row)
        for row in df[colunas].itertuples(index=False, name=None)
    ]

    with _conn("DATABASE_URL_OPERACIONAL") as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM pacotes_grandes WHERE nome_arquivo = %s", [arquivo.name])
        execute_values(cur, f"INSERT INTO pacotes_grandes ({','.join(colunas)}) VALUES %s", values)
        conn.commit()
        cur.close()

    return len(df)
# ================================
# 📊 DEVOLUÇÃO ENRIQUECIDA (Folha + Monitoramento)
# ================================
def importar_devolucao_enriquecida(arquivo_folha, arquivo_monitor, data_ref):
    # ── Lê folha de devolução ──────────────────────────────────────
    with io.BytesIO(arquivo_folha.read()) as buf_folha:
        df_dev = xlsx_para_dataframe(buf_folha)
    arquivo_folha.seek(0)
    df_dev = df_dev.iloc[:, :10]
    df_dev.columns = [
        "waybill", "status", "tipo_operacao", "cliente",
        "data_operacao", "proximo_ponto", "operador",
        "ponto_operacao", "estado", "regiao"
    ]
    df_dev["data_operacao"] = pd.to_datetime(df_dev["data_operacao"], errors="coerce")
    df_dev["waybill"] = df_dev["waybill"].astype(str).str.strip()

    # ── Lê monitoramento ──────────────────────────────────────────
    with io.BytesIO(arquivo_monitor.read()) as buf_monitor:
        df_mon_raw = xlsx_para_dataframe(buf_monitor)
    arquivo_monitor.seek(0)

    # Colunas completas do monitoramento (igual a importar_devolucao_monitoramento)
    cols_mon_full = [0, 4, 8, 11, 21, 22, 25, 33, 66, 67, 68, 71, 73]
    cols_mon_full = [c for c in cols_mon_full if c < len(df_mon_raw.columns)]
    df_mon_full = df_mon_raw.iloc[:, cols_mon_full].copy()
    df_mon_full.columns = [
        "waybill", "status_mon", "motivo", "estado_dest",
        "cliente_mon", "cliente_fantasia", "ponto_entrada", "data_criacao",
        "tent1", "tent2", "tent3", "assinatura", "prazo_dias"
    ][:len(cols_mon_full)]
    for col in ["tent1", "tent2", "tent3", "assinatura", "data_criacao"]:
        if col in df_mon_full.columns:
            df_mon_full[col] = pd.to_datetime(df_mon_full[col], errors="coerce")
    df_mon_full["waybill"] = df_mon_full["waybill"].astype(str).str.strip()

    # Colunas reduzidas para o merge com dev (estado_dest, cidade_dest, pre_entrega, ponto_entrada, motivo, data_criacao)
    cols_idx = [0, 4, 8, 11, 12, 21, 24, 25, 33]
    cols_idx = [c for c in cols_idx if c < len(df_mon_raw.columns)]
    df_mon = df_mon_raw.iloc[:, cols_idx].copy()
    df_mon.columns = [
        "waybill", "status_mon", "motivo", "estado_dest", "cidade_dest",
        "cliente_mon", "pre_entrega", "ponto_entrada", "data_criacao"
    ][:len(cols_idx)]
    df_mon["data_criacao"] = pd.to_datetime(df_mon["data_criacao"], errors="coerce")
    df_mon["waybill"] = df_mon["waybill"].astype(str).str.strip()

    # ── Merge para dev_detalhado ───────────────────────────────────
    df = df_dev.merge(df_mon, on="waybill", how="left")
    df["dias_dev"] = (df["data_operacao"] - df["data_criacao"]).dt.days

    # Para pedidos sem match no monitoramento (ex: Shein Nacional),
    # extrai data_criacao do waybill (formato AJ AAMMDD...)
    def _data_do_waybill(waybill):
        try:
            w = str(waybill).strip()
            return pd.Timestamp(int("20" + w[2:4]), int(w[4:6]), int(w[6:8]))
        except Exception:
            return pd.NaT

    sem_criacao = df["data_criacao"].isna()
    if sem_criacao.any():
        df.loc[sem_criacao, "data_criacao"] = df.loc[sem_criacao, "waybill"].apply(_data_do_waybill)
        df.loc[sem_criacao, "dias_dev"] = (
            (df.loc[sem_criacao, "data_operacao"] - df.loc[sem_criacao, "data_criacao"])
            .dt.days
        )

    # Descarta apenas dias_dev negativos (dados inconsistentes)
    df = df[df["dias_dev"].isna() | (df["dias_dev"] >= 0)]

    ref_ts   = pd.Timestamp(data_ref)
    semana   = ref_ts.strftime("w%V")
    ano      = int(ref_ts.year)
    nome_arq = f"{arquivo_folha.name}+{arquivo_monitor.name}"
    agora    = datetime.now(timezone.utc)

    df["semana"]          = semana
    df["ano"]             = ano
    df["data_referencia"] = data_ref
    df["nome_arquivo"]    = nome_arq
    df["data_importacao"] = agora

    colunas_det = [
        "waybill", "status", "tipo_operacao", "cliente", "data_operacao",
        "ponto_operacao", "estado_dest", "cidade_dest", "pre_entrega",
        "ponto_entrada", "motivo", "data_criacao", "dias_dev",
        "semana", "ano", "data_referencia", "nome_arquivo", "data_importacao"
    ]
    for col in colunas_det:
        if col not in df.columns:
            df[col] = None

    df_save = df[colunas_det].copy()

    def _val(v):
        if hasattr(v, '__class__') and v.__class__.__name__ == 'NaTType':
            return None
        try:
            return None if pd.isna(v) else v
        except Exception:
            return v

    with _conn("DATABASE_URL_DEVOLUCOES") as conn:
        cur = conn.cursor()

        # ── Salva dev_detalhado ────────────────────────────────────────
        cur.execute("DELETE FROM dev_detalhado WHERE data_referencia = %s", [data_ref])
        execute_values(cur,
            f"INSERT INTO dev_detalhado ({','.join(colunas_det)}) VALUES %s",
            [tuple(_val(v) for v in row) for row in df_save.itertuples(index=False, name=None)]
        )

        # ── Salva dev_resumo ───────────────────────────────────────────
        df_resumo_dev = (
            df_save
            .groupby(["semana", "ano", "data_referencia", "status",
                      "cliente", "estado_dest", "motivo"], dropna=False)
            .agg(qtd=("waybill", "count"))
            .reset_index()
        )
        df_resumo_dev["nome_arquivo"]    = nome_arq
        df_resumo_dev["data_importacao"] = agora
        cur.execute("DELETE FROM dev_resumo WHERE data_referencia = %s", [data_ref])
        colunas_resumo_dev = ["semana", "ano", "data_referencia", "status",
                              "cliente", "estado_dest", "motivo", "qtd",
                              "nome_arquivo", "data_importacao"]
        execute_values(cur,
            f"INSERT INTO dev_resumo ({','.join(colunas_resumo_dev)}) VALUES %s",
            [tuple(_val(v) for v in row)
             for row in df_resumo_dev[colunas_resumo_dev].itertuples(index=False, name=None)]
        )

        # ── Salva dev_status_semanal e dev_iatas_semanal ───────────────
        for tabela in ["dev_status_semanal", "dev_iatas_semanal"]:
            cur.execute(f"DELETE FROM {tabela} WHERE nome_arquivo = %s", [nome_arq])

        status_agg = (
            df.groupby(["status", "estado_dest", "cliente"])
            .size().reset_index(name="qtd")
        )
        status_agg["semana"]           = semana
        status_agg["ano"]              = ano
        status_agg["data_referencia"]  = data_ref
        status_agg["nome_arquivo"]     = nome_arq
        status_agg["data_importacao"]  = agora
        status_agg["cliente_fantasia"] = None
        status_agg = status_agg.rename(columns={"estado_dest": "estado"})
        colunas_status = [
            "estado", "status", "semana", "ano", "data_referencia", "cliente",
            "cliente_fantasia", "qtd", "nome_arquivo", "data_importacao"
        ]
        execute_values(cur,
            f"INSERT INTO dev_status_semanal ({','.join(colunas_status)}) VALUES %s",
            [tuple(_val(v) for v in row)
             for row in status_agg[colunas_status].itertuples(index=False, name=None)]
        )

        iata_agg = (
            df[df["pre_entrega"].notna()]
            .groupby(["pre_entrega", "estado_dest"])
            .size().reset_index(name="qtd")
        )
        iata_agg["semana"]           = semana
        iata_agg["ano"]              = ano
        iata_agg["data_referencia"]  = data_ref
        iata_agg["nome_arquivo"]     = nome_arq
        iata_agg["data_importacao"]  = agora
        iata_agg["cliente_fantasia"] = None
        iata_agg = iata_agg.rename(columns={"pre_entrega": "ponto_operacao", "estado_dest": "estado"})
        colunas_iata = [
            "ponto_operacao", "estado", "semana", "ano", "data_referencia",
            "cliente_fantasia", "qtd", "nome_arquivo", "data_importacao"
        ]
        execute_values(cur,
            f"INSERT INTO dev_iatas_semanal ({','.join(colunas_iata)}) VALUES %s",
            [tuple(_val(v) for v in row)
             for row in iata_agg[colunas_iata].itertuples(index=False, name=None)]
        )

        # ── Salva p90_semanal ──────────────────────────────────────────
        cur.execute("DELETE FROM p90_semanal WHERE nome_arquivo = %s", [nome_arq])
        df_p90_src = df[df["status"] == "Recebido de devolução"].copy()
        if not df_p90_src.empty:
            df_p90_src["estado_p90"] = df_p90_src["estado_dest"].fillna(df_p90_src["estado"])
            df_p90_src = df_p90_src[df_p90_src["dias_dev"] >= 0].dropna(subset=["estado_p90", "dias_dev"])
            if not df_p90_src.empty:
                p90_agg = (
                    df_p90_src.groupby(["estado_p90", "cliente"])
                    .agg(
                        p90_dias    = ("dias_dev", lambda x: round(float(np.percentile(x, 90)), 1)),
                        qtd_pedidos = ("dias_dev", "count")
                    )
                    .reset_index()
                    .rename(columns={"estado_p90": "estado"})
                )
                p90_agg["semana"]          = semana
                p90_agg["ano"]             = ano
                p90_agg["data_referencia"] = data_ref
                p90_agg["nome_arquivo"]    = nome_arq
                p90_agg["data_importacao"] = agora
                colunas_p90 = [
                    "estado", "semana", "ano", "cliente", "p90_dias",
                    "qtd_pedidos", "data_referencia", "nome_arquivo", "data_importacao"
                ]
                execute_values(cur,
                    f"INSERT INTO p90_semanal ({','.join(colunas_p90)}) VALUES %s",
                    [tuple(_val(v) for v in row)
                     for row in p90_agg[colunas_p90].itertuples(index=False, name=None)]
                )

        # ── Salva dev_sla_semanal, dev_motivos_semanal, dev_dsp_sem3tent ─
        for tabela in ["dev_sla_semanal", "dev_motivos_semanal", "dev_dsp_sem3tent"]:
            cur.execute(f"DELETE FROM {tabela} WHERE nome_arquivo = %s", [nome_arq])

        df_mon_full["waybill"] = df_mon_full["waybill"].astype(str).str.strip()

        df_entregues = df_mon_full[df_mon_full["assinatura"].notna()].copy() if "assinatura" in df_mon_full.columns else pd.DataFrame()
        if not df_entregues.empty:
            df_entregues["dias"] = (
                (df_entregues["assinatura"] - df_entregues["data_criacao"]).dt.total_seconds() / 86400
            )
            df_entregues["prazo"]    = df_entregues["prazo_dias"].fillna(7) if "prazo_dias" in df_entregues.columns else 7
            df_entregues["no_prazo"] = df_entregues["dias"] <= df_entregues["prazo"]
            sla_agg = (
                df_entregues.groupby(["estado_dest", "cliente_mon", "cliente_fantasia"])
                .agg(qtd_total=("waybill", "count"), qtd_no_prazo=("no_prazo", "sum"))
                .reset_index()
                .rename(columns={"estado_dest": "estado", "cliente_mon": "cliente"})
            )
            sla_agg["data_referencia"] = data_ref
            sla_agg["nome_arquivo"]    = nome_arq
            sla_agg["data_importacao"] = agora
            colunas_sla = ["estado", "data_referencia", "cliente", "cliente_fantasia", "qtd_total", "qtd_no_prazo", "nome_arquivo", "data_importacao"]
            execute_values(cur,
                f"INSERT INTO dev_sla_semanal ({','.join(colunas_sla)}) VALUES %s",
                [tuple(_val(v) for v in row)
                 for row in sla_agg[colunas_sla].itertuples(index=False, name=None)]
            )

        df_motivos = df_mon_full[df_mon_full["motivo"].notna()].copy() if "motivo" in df_mon_full.columns else pd.DataFrame()
        if not df_motivos.empty:
            motivos_agg = (
                df_motivos.groupby(["estado_dest", "motivo", "cliente_mon", "cliente_fantasia"])
                .size().reset_index(name="qtd")
                .rename(columns={"estado_dest": "estado", "cliente_mon": "cliente"})
            )
            motivos_agg["data_referencia"] = data_ref
            motivos_agg["nome_arquivo"]    = nome_arq
            motivos_agg["data_importacao"] = agora
            colunas_mot = ["estado", "motivo", "cliente", "cliente_fantasia", "data_referencia", "qtd", "nome_arquivo", "data_importacao"]
            execute_values(cur,
                f"INSERT INTO dev_motivos_semanal ({','.join(colunas_mot)}) VALUES %s",
                [tuple(_val(v) for v in row)
                 for row in motivos_agg[colunas_mot].itertuples(index=False, name=None)]
            )

        cols_dsp = ["motivo", "tent1", "tent3", "assinatura"]
        if all(c in df_mon_full.columns for c in cols_dsp):
            dsp_sem3 = df_mon_full[
                df_mon_full["motivo"].notna() &
                df_mon_full["tent1"].notna() &
                df_mon_full["tent3"].isna() &
                df_mon_full["assinatura"].isna()
            ].copy()
            if not dsp_sem3.empty:
                dsp_agg = (
                    dsp_sem3.groupby(["ponto_entrada", "estado_dest", "motivo", "cliente_mon", "cliente_fantasia"])
                    .size().reset_index(name="qtd")
                    .rename(columns={"estado_dest": "estado", "cliente_mon": "cliente"})
                )
                dsp_agg["data_referencia"] = data_ref
                dsp_agg["nome_arquivo"]    = nome_arq
                dsp_agg["data_importacao"] = agora
                colunas_dsp = ["ponto_entrada", "estado", "motivo", "cliente", "cliente_fantasia", "data_referencia", "qtd", "nome_arquivo", "data_importacao"]
                execute_values(cur,
                    f"INSERT INTO dev_dsp_sem3tent ({','.join(colunas_dsp)}) VALUES %s",
                    [tuple(_val(v) for v in row)
                     for row in dsp_agg[colunas_dsp].itertuples(index=False, name=None)]
                )

        conn.commit()
        cur.close()

    limpar_historico_antigo()
    return len(df_save)


# ================================
# 🚛 COLETAS — CARREGAMENTO/DESCARREGAMENTO
# ================================
def _coletas_colunas_base(df):
    """Renomeia colunas e converte tipos comuns para importações de coletas."""
    df = df.iloc[:, :19]
    df.columns = [
        "num_registro", "placa", "carregador", "rede_carregador",
        "endereco_carga", "tempo_carga", "secao_destino",
        "descarregador", "rede_descarregador", "endereco_descarga",
        "tempo_descarga", "sacos_carregados", "sacos_descarregados",
        "dif_sacos", "pacotes_carregados", "pacotes_descarregados",
        "dif_pacotes", "modo_operacao", "tipo_veiculo"
    ]
    df["tempo_carga"]    = pd.to_datetime(df["tempo_carga"],    errors="coerce")
    df["tempo_descarga"] = pd.to_datetime(df["tempo_descarga"], errors="coerce")
    for col in ["sacos_carregados", "sacos_descarregados", "dif_sacos",
                "pacotes_carregados", "pacotes_descarregados", "dif_pacotes"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df


def _salvar_coletas(df, arquivo, data_ref, tipo):
    df["tipo"]            = tipo
    df["data_referencia"] = data_ref
    df["nome_arquivo"]    = arquivo.name
    df["data_importacao"] = datetime.now(timezone.utc)

    colunas = [
        "num_registro", "placa", "carregador", "rede_carregador",
        "tempo_carga", "secao_destino", "descarregador", "rede_descarregador",
        "tempo_descarga", "sacos_carregados", "sacos_descarregados", "dif_sacos",
        "pacotes_carregados", "pacotes_descarregados", "dif_pacotes",
        "modo_operacao", "tipo_veiculo", "tipo",
        "data_referencia", "nome_arquivo", "data_importacao"
    ]

    with _conn("DATABASE_URL_COLETAS") as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM coletas WHERE nome_arquivo = %s AND tipo = %s",
            [arquivo.name, tipo]
        )
        values = [
            tuple(None if pd.isna(v) else v for v in row)
            for row in df[colunas].itertuples(index=False, name=None)
        ]
        execute_values(cur, f"INSERT INTO coletas ({','.join(colunas)}) VALUES %s", values)
        conn.commit()
        cur.close()
    return len(df)


def importar_coletas(arquivo, data_ref):
    """Importa descarregamentos recebidos em SP-RR-001 (Perus)."""
    df = xlsx_para_dataframe(arquivo)
    if df.empty:
        return 0

    df = _coletas_colunas_base(df)

    # Filtro: descarregado em SP-RR-001
    df = df[
        (df["rede_descarregador"] == "SP-RR-001") &
        (df["descarregador"].notna()) &
        (df["endereco_descarga"].notna()) &
        (df["tempo_descarga"].notna())
    ]

    if df.empty:
        return 0

    return _salvar_coletas(df, arquivo, data_ref, "descarregamento")


def importar_coletas_saida(arquivo, data_ref):
    """Importa carregamentos que saem de SP-RR-001 (Perus) para outras bases."""
    df = xlsx_para_dataframe(arquivo)
    if df.empty:
        return 0

    df = _coletas_colunas_base(df)

    # Filtro: carregado em SP-RR-001, destino ≠ SP-RR-001
    df = df[
        (df["rede_carregador"] == "SP-RR-001") &
        (df["secao_destino"] != "SP-RR-001") &
        (df["secao_destino"].notna()) &
        (df["tempo_carga"].notna())
    ]

    if df.empty:
        return 0

    return _salvar_coletas(df, arquivo, data_ref, "saida")


# ================================
# 👥 PRESENÇA / DIÁRIO DE BORDO
# ================================
def importar_presenca(arquivo):
    df_raw = xlsx_para_dataframe(arquivo, header=None)

    if df_raw.empty:
        return 0

    nome_arquivo = arquivo.name
    data_importacao = datetime.now(timezone.utc)

    rows_turno  = []
    rows_diario = []

    data_atual = None

    for _, row in df_raw.iterrows():
        # Coluna 0 é a data (merged cell — só vem preenchida na linha T1)
        val_data = row.iloc[0] if len(row) > 0 else None
        if pd.notna(val_data) and val_data != "":
            try:
                data_atual = pd.to_datetime(val_data).date()
            except Exception as e:
                print(f"⚠️ Linha ignorada (data inválida): {e}")
                continue  # linha de cabeçalho ou inválida

        if data_atual is None:
            continue

        turno = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ""
        if turno not in ("T1", "T2", "T3"):
            continue

        def _int(idx):
            v = row.iloc[idx] if len(row) > idx else None
            try:
                return int(float(v)) if pd.notna(v) else None
            except Exception:
                return None

        def _float(idx):
            v = row.iloc[idx] if len(row) > idx else None
            try:
                return float(v) if pd.notna(v) else None
            except Exception:
                return None

        semana = str(pd.Timestamp(data_atual).isocalendar()[1]).zfill(2)
        ano    = int(pd.Timestamp(data_atual).year)

        rows_turno.append((
            data_atual,
            semana,
            ano,
            turno,
            _int(2),    # produzido_turno
            _int(6),    # presenca_turno
            _int(12),   # presenca_total (só T3, None nos outros — OK)
            _int(3),    # anjun
            _int(4),    # temporarios
            _int(5),    # diaristas_presenciais
            _int(7),    # faltas_anjun
            _int(8),    # faltas_temporarios
            _float(9),  # perc_falta
            _float(10), # custo_diaristas
            _float(11), # custo_por_pedido
            nome_arquivo,
            data_importacao,
        ))

        if turno == "T3":
            rows_diario.append((
                data_atual,
                semana,
                ano,
                _int(13),  # vol_tfk
                _int(14),  # vol_shein
                _int(15),  # vol_d2d
                _int(16),  # vol_kwai
                _int(17),  # vol_b2c
                nome_arquivo,
                data_importacao,
            ))

    if not rows_turno:
        return 0

    with _conn("DATABASE_URL_OPERACIONAL") as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM presenca_turno  WHERE nome_arquivo = %s", [nome_arquivo])
        cur.execute("DELETE FROM presenca_diaria WHERE nome_arquivo = %s", [nome_arquivo])
        execute_values(cur, """
            INSERT INTO presenca_turno (
                data, semana, ano, turno,
                produzido_turno, presenca_turno, presenca_total,
                anjun, temporarios, diaristas_presenciais,
                faltas_anjun, faltas_temporarios, perc_falta,
                custo_diaristas, custo_por_pedido,
                nome_arquivo, data_importacao
            ) VALUES %s
        """, rows_turno)
        if rows_diario:
            execute_values(cur, """
                INSERT INTO presenca_diaria (
                    data, semana, ano,
                    vol_tfk, vol_shein, vol_d2d, vol_kwai, vol_b2c,
                    nome_arquivo, data_importacao
                ) VALUES %s
            """, rows_diario)
        conn.commit()
        cur.close()

    return len(rows_turno)
