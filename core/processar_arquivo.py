import io
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from psycopg2.extras import execute_values

logger = logging.getLogger(__name__)
from core.database import (
    executar_historico,
    executar_devolucoes,
    executar_operacional,
    executar_processamento,
    _conn,
)


def _safe_int(v):
    try:
        return int(float(v)) if pd.notna(v) else None
    except Exception:
        return None


def _safe_float(v):
    try:
        return float(v) if pd.notna(v) else None
    except Exception:
        return None


def _val(v):
    if hasattr(v, '__class__') and v.__class__.__name__ == 'NaTType':
        return None
    try:
        return None if pd.isna(v) else v
    except Exception:
        return v


def _classificar_status_sla(row):
    if pd.isna(row["saida_hub1"]):
        return "sem_saida"
    elif row["tempo_horas"] <= 24:
        return "dentro_sla"
    else:
        return "fora_sla"


def _classificar_dispositivo(op):
    op = str(op).strip().upper()
    if "PERUS01" in op:
        return "Sorter Oval"
    elif "PERUS02" in op:
        return "Sorter Linear"
    else:
        return "Cubometro"


def _classificar_turno_e_data(dt):
    minuto_total = dt.hour * 60 + dt.minute
    if 330 <= minuto_total <= 829:
        return "T1", dt.date()
    elif 830 <= minuto_total <= 1319:
        return "T2", dt.date()
    else:
        data_op = (dt - pd.Timedelta(days=1)).date() if dt.hour < 6 else dt.date()
        return "T3", data_op


def _classificar_faixa_backlog(h):
    if pd.isna(h) or h < 0:
        return None
    if h <= 24:
        return "1 dia"
    if h <= 120:
        return "1-5 dias"
    if h <= 240:
        return "5-10 dias"
    if h <= 480:
        return "10-20 dias"
    if h <= 720:
        return "20-30 dias"
    return "30+ dias"


def _data_do_waybill(waybill):
    try:
        w = str(waybill).strip()
        return pd.Timestamp(int("20" + w[2:4]), int(w[4:6]), int(w[6:8]))
    except Exception:
        return pd.NaT


# ================================
# ⚡ LEITURA RÁPIDA: XLSX → Parquet em memória
# ================================
def xlsx_para_dataframe(arquivo, engine="calamine", **kwargs):
    """
    Lê XLSX com calamine (Rust, ~10x mais rápido que openpyxl),
    converte para Parquet em memória e retorna DataFrame columnar.
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
    # AY=50 saida_hub2 | BG=58 saida_hub3 | BM=64 inbound_ponto | BT=71 assinatura
    df = xlsx_para_dataframe(
        arquivo,
        usecols=[0, 11, 12, 21, 24, 25, 41, 42, 43, 48, 50, 56, 58, 64, 71]
    )
    linhas_lidas = len(df)

    df.columns = [
        "waybill", "estado", "cidade", "cliente",
        "pre_entrega", "ponto_entrada",
        "entrada_hub1", "saida_hub1", "proximo_ponto",
        "entrada_hub2", "saida_hub2",
        "entrada_hub3", "saida_hub3",
        "inbound_ponto", "assinatura"
    ]

    df["waybill"] = df["waybill"].astype(str).str.strip()
    df = df[df["waybill"].str.lower() != "nan"]

    for col in ["entrada_hub1", "saida_hub1",
                "entrada_hub2", "saida_hub2",
                "entrada_hub3", "saida_hub3",
                "inbound_ponto", "assinatura"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")

    # Backlog real: entrou no hub1, não saiu, não avançou na cadeia e não foi entregue
    df_backlog = df[
        df["entrada_hub1"].notna() &
        df["saida_hub1"].isna() &
        df["entrada_hub2"].isna() &
        df["saida_hub2"].isna() &
        df["entrada_hub3"].isna() &
        df["saida_hub3"].isna() &
        df["inbound_ponto"].isna() &
        df["assinatura"].isna()
    ].copy()

    linhas_backlog = len(df_backlog)

    if df_backlog.empty:
        return {"linhas_lidas": linhas_lidas, "filtradas": 0, "registros": 0,
                "detalhe": "Nenhum pedido em backlog encontrado"}

    agora = pd.to_datetime(data_referencia)

    df_backlog["horas_backlog_snapshot"] = (
        (agora - df_backlog["entrada_hub1"]).dt.total_seconds() / 3600
    )

    df_backlog["faixa_backlog_snapshot"] = df_backlog["horas_backlog_snapshot"].apply(_classificar_faixa_backlog)
    df_backlog["data_referencia"]        = agora.date()
    df_backlog["data_importacao"]        = datetime.now(timezone.utc)
    df_backlog["nome_arquivo"]           = arquivo.name
    df_backlog["proximo_ponto"]          = df_backlog["proximo_ponto"].fillna("Sem informação")

    _persistir_backlog(df_backlog, arquivo, agora)
    limpar_historico_antigo()

    resumo = df_backlog.groupby(["estado", "cliente", "faixa_backlog_snapshot"]).size()
    grupos = len(resumo)
    return {"linhas_lidas": linhas_lidas, "filtradas": linhas_backlog,
            "registros": linhas_backlog, "grupos": grupos,
            "detalhe": f"{linhas_lidas:,} lidas → {linhas_backlog:,} em backlog ({grupos:,} grupos estado/cliente/faixa)"}


def _persistir_backlog(df_backlog, arquivo, agora):
    """Persiste backlog_atual e histórico após transformação."""
    _upsert_backlog_atual(df_backlog)
    _inserir_historico(df_backlog, arquivo, agora)


def _upsert_backlog_atual(df_backlog):
    """
    Substitui backlog_atual por resumo agregado (estado/cliente/pre_entrega/
    proximo_ponto/faixa) — ocupa ~99% menos espaço que linha por linha.
    Download de waybills continua via tabela `pedidos`.
    """
    df_agg = (
        df_backlog.groupby(
            ["estado", "cliente", "pre_entrega", "proximo_ponto", "faixa_backlog_snapshot"],
            dropna=False
        )
        .agg(
            qtd                   = ("waybill",               "count"),
            horas_min             = ("horas_backlog_snapshot", "min"),
            horas_max             = ("horas_backlog_snapshot", "max"),
            horas_media           = ("horas_backlog_snapshot", "mean"),
            entrada_hub1_mais_ant = ("entrada_hub1",           "min"),
        )
        .reset_index()
    )
    df_agg["data_referencia"] = df_backlog["data_referencia"].iloc[0]
    df_agg["data_importacao"] = df_backlog["data_importacao"].iloc[0]

    colunas = [
        "estado", "cliente", "pre_entrega", "proximo_ponto", "faixa_backlog_snapshot",
        "qtd", "horas_min", "horas_max", "horas_media",
        "entrada_hub1_mais_ant", "data_referencia", "data_importacao"
    ]

    with _conn("DATABASE_URL_BACKLOG") as conn:
        cur = conn.cursor()
        cur.execute("TRUNCATE TABLE backlog_atual")
        execute_values(
            cur,
            f"INSERT INTO backlog_atual ({','.join(colunas)}) VALUES %s",
            [tuple(_val(v) for v in row)
             for row in df_agg[colunas].itertuples(index=False, name=None)]
        )
        conn.commit()
        cur.close()


def _inserir_historico(df_backlog, arquivo, agora):
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

    colunas_resumo = [
        "data_referencia", "estado", "cliente", "pre_entrega",
        "proximo_ponto", "faixa_backlog_snapshot", "qtd",
        "nome_arquivo", "data_importacao"
    ]
    colunas_bruto = [
        "waybill", "cliente", "estado", "cidade", "pre_entrega", "proximo_ponto",
        "entrada_hub1", "horas_backlog_snapshot", "faixa_backlog_snapshot",
        "data_referencia", "data_importacao", "nome_arquivo"
    ]

    with _conn("DATABASE_URL_HISTORICO") as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM pedidos_resumo WHERE nome_arquivo = %s", [arquivo.name])
        execute_values(cur,
            f"INSERT INTO pedidos_resumo ({','.join(colunas_resumo)}) VALUES %s",
            [tuple(_val(v) for v in row)
             for row in df_resumo[colunas_resumo].itertuples(index=False, name=None)]
        )
        cur.execute("DELETE FROM pedidos WHERE data_referencia = %s", [agora.date()])
        cur.execute("DELETE FROM pedidos WHERE data_referencia < CURRENT_DATE - INTERVAL '7 days'")
        execute_values(cur,
            f"INSERT INTO pedidos ({','.join(colunas_bruto)}) VALUES %s",
            [tuple(_val(v) for v in row)
             for row in df_backlog[colunas_bruto].itertuples(index=False, name=None)]
        )
        conn.commit()
        cur.close()


def _transformar_produtividade(df):
    """Filtra, classifica dispositivo, turno/data e agrega por hora."""
    df = df[df["data_hora"].notna()].copy()
    df["data_hora"] = pd.to_datetime(df["data_hora"], errors="coerce")
    df = df[df["data_hora"].notna()]
    mask_remover = (
        df["operador"].astype(str).str.upper().str.contains("DEVOL", na=False) |
        df["operador"].astype(str).str.upper().str.startswith("MG", na=False)
    )
    df = df[~mask_remover]
    if df.empty:
        return df
    df["dispositivo"] = df["operador"].apply(_classificar_dispositivo)
    turnos_datas = df["data_hora"].apply(
        lambda dt: pd.Series(_classificar_turno_e_data(dt), index=["turno", "data"])
    )
    df[["turno", "data"]] = turnos_datas
    df["hora"] = df["data_hora"].dt.hour
    return (
        df.groupby(["cliente", "data", "hora", "turno", "dispositivo"])
        .size()
        .reset_index(name="volumes")
    )


def _ler_produtividade(arquivo):
    df = xlsx_para_dataframe(arquivo, usecols=[3, 8, 20])
    df.columns = ["cliente", "data_hora", "operador"]
    return df


def importar_produtividade(arquivo):
    df = _ler_produtividade(arquivo)
    if df.empty:
        return {"registros": 0, "detalhe": "Arquivo vazio"}
    linhas = len(df)
    df_agg = _transformar_produtividade(df)
    if df_agg.empty:
        return {"registros": 0, "detalhe": f"{linhas:,} lidas → 0 após filtros"}
    df_agg["nome_arquivo"]    = arquivo.name
    df_agg["data_importacao"] = datetime.now(timezone.utc)
    _persistir_produtividade(df_agg, arquivo.name)
    limpar_historico_antigo()
    grupos = len(df_agg)
    return {"registros": grupos, "detalhe": f"{linhas:,} lidas → {grupos:,} grupos cliente/data/hora/turno/dispositivo"}


def _persistir_produtividade(df_agg, nome_arquivo):
    colunas = ["cliente", "data", "hora", "turno", "dispositivo", "volumes", "nome_arquivo", "data_importacao"]
    values  = [tuple(_val(v) for v in row)
               for row in df_agg[colunas].itertuples(index=False, name=None)]
    with _conn("DATABASE_URL_OPERACIONAL") as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM produtividade WHERE nome_arquivo = %s", [nome_arquivo])
        execute_values(cur, f"INSERT INTO produtividade ({','.join(colunas)}) VALUES %s", values)
        conn.commit()
        cur.close()


def _agregar_tempo_processamento(df):
    return df.groupby(["estado", "ponto_entrada", "hiata", "cliente", "data"]).agg(
        qtd_total      = ("waybill",     "count"),
        qtd_dentro_sla = ("status",      lambda x: (x == "dentro_sla").sum()),
        qtd_fora_sla   = ("status",      lambda x: (x == "fora_sla").sum()),
        qtd_sem_saida  = ("status",      lambda x: (x == "sem_saida").sum()),
        tempo_medio_h  = ("tempo_horas", lambda x: x.dropna().mean() if x.dropna().any() else None)
    ).reset_index()


def _transformar_tempo_processamento(df):
    """Aplica filtros, calcula tempo_horas, status SLA e agrega."""
    df["entrada_hub1"] = pd.to_datetime(df["entrada_hub1"], errors="coerce")
    df["saida_hub1"]   = pd.to_datetime(df["saida_hub1"],   errors="coerce")
    df = df[df["entrada_hub1"].notna()].copy()
    df["data"]        = df["entrada_hub1"].dt.date
    df["tempo_horas"] = (df["saida_hub1"] - df["entrada_hub1"]).dt.total_seconds() / 3600
    df = df[(df["tempo_horas"].isna()) | ((df["tempo_horas"] >= 0) & (df["tempo_horas"] <= 240))]
    df["hiata"]  = df["hiata"].astype(str).str.strip().str.upper()
    df["status"] = df.apply(_classificar_status_sla, axis=1)
    return _agregar_tempo_processamento(df)


def importar_tempo_processamento(arquivo):
    df = xlsx_para_dataframe(arquivo, usecols=[0, 11, 21, 24, 25, 41, 42, 43])
    df.columns = ["waybill", "estado", "cliente", "pre_entrega", "ponto_entrada",
                  "entrada_hub1", "saida_hub1", "hiata"]
    if df.empty:
        return {"registros": 0, "detalhe": "Arquivo vazio"}
    linhas = len(df)
    agg = _transformar_tempo_processamento(df)
    agg["data_snapshot"]   = datetime.now(timezone.utc).date()
    agg["nome_arquivo"]    = arquivo.name
    agg["data_importacao"] = datetime.now(timezone.utc)
    _persistir_tempo_processamento(agg, arquivo.name)
    n_percentis = 0
    try:
        perc = _calcular_percentis_operacao(df, arquivo.name)
        if not perc.empty:
            _persistir_percentis_operacao(perc, arquivo.name)
            n_percentis = len(perc)
    except Exception as e:
        logger.warning("Percentis operacao nao calculados para %s: %s", arquivo.name, e)
    limpar_historico_antigo()
    grupos = len(agg)
    perc_info = (
        f" | {n_percentis:,} grupos p50/p80/p90"
        if n_percentis
        else " | sem saída_hub preenchida → percentis não calculados"
    )
    return {"registros": grupos, "detalhe": f"{linhas:,} lidas → {grupos:,} grupos estado/hiata/cliente/data{perc_info}"}


def _persistir_tempo_processamento(agg, nome_arquivo):
    colunas = [
        "estado", "ponto_entrada", "hiata", "cliente", "data",
        "data_snapshot", "qtd_total", "qtd_dentro_sla", "qtd_fora_sla",
        "qtd_sem_saida", "tempo_medio_h", "nome_arquivo", "data_importacao"
    ]
    values = [tuple(_val(v) for v in row)
              for row in agg[colunas].itertuples(index=False, name=None)]
    with _conn("DATABASE_URL_PROCESSAMENTO") as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM tempo_processamento WHERE nome_arquivo = %s", [nome_arquivo])
        execute_values(cur, f"INSERT INTO tempo_processamento ({','.join(colunas)}) VALUES %s", values)
        conn.commit()
        cur.close()


def _calcular_percentis_operacao(df_raw, nome_arquivo):
    """Calcula P50/P80/P90 de tempo de hub (horas) por estado/cliente/data a partir de waybills individuais."""
    df = df_raw.copy()
    df["entrada_hub1"] = pd.to_datetime(df["entrada_hub1"], errors="coerce")
    df["saida_hub1"]   = pd.to_datetime(df["saida_hub1"],   errors="coerce")
    df = df[df["entrada_hub1"].notna() & df["saida_hub1"].notna()].copy()
    if df.empty:
        return pd.DataFrame()
    df["data"]        = df["entrada_hub1"].dt.date
    df["tempo_horas"] = (df["saida_hub1"] - df["entrada_hub1"]).dt.total_seconds() / 3600
    df = df[(df["tempo_horas"] >= 0) & (df["tempo_horas"] <= 240)]
    if df.empty:
        return pd.DataFrame()
    agg = (
        df.groupby(["estado", "cliente", "data"])["tempo_horas"]
        .agg(
            p50_horas   = lambda x: round(float(np.percentile(x, 50)), 2),
            p80_horas   = lambda x: round(float(np.percentile(x, 80)), 2),
            p90_horas   = lambda x: round(float(np.percentile(x, 90)), 2),
            qtd_pedidos = "count",
        )
        .reset_index()
    )
    agg["nome_arquivo"]    = nome_arquivo
    agg["data_importacao"] = datetime.now(timezone.utc)
    return agg


def _persistir_percentis_operacao(agg, nome_arquivo):
    colunas = [
        "estado", "cliente", "data", "p50_horas", "p80_horas", "p90_horas",
        "qtd_pedidos", "nome_arquivo", "data_importacao"
    ]
    values = [tuple(_val(v) for v in row)
              for row in agg[colunas].itertuples(index=False, name=None)]
    with _conn("DATABASE_URL_PROCESSAMENTO") as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM percentis_operacao WHERE nome_arquivo = %s", [nome_arquivo])
        execute_values(cur, f"INSERT INTO percentis_operacao ({','.join(colunas)}) VALUES %s", values)
        conn.commit()
        cur.close()


def _extrair_data_criacao(waybill):
    try:
        w = str(waybill).strip()
        return pd.Timestamp(int("20" + w[2:4]), int(w[4:6]), int(w[6:8]))
    except Exception:
        return None


def _persistir_p90_arquivo(agg, nome_arquivo):
    colunas = [
        "estado", "semana", "ano", "cliente", "p50_dias", "p80_dias", "p90_dias",
        "qtd_pedidos", "data_referencia", "nome_arquivo", "data_importacao"
    ]
    values = [tuple(_val(v) for v in row)
              for row in agg[colunas].itertuples(index=False, name=None)]
    with _conn("DATABASE_URL_DEVOLUCOES") as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM p90_semanal WHERE nome_arquivo = %s", [nome_arquivo])
        execute_values(cur, f"INSERT INTO p90_semanal ({','.join(colunas)}) VALUES %s", values)
        conn.commit()
        cur.close()


def _transformar_p90(df, data_ref):
    """Filtra, extrai data_criacao, calcula dias e agrega p90."""
    df = df[df["status"] == "Recebido de devolução"].copy()
    if df.empty:
        return df
    df["data_operacao"] = pd.to_datetime(df["data_operacao"], errors="coerce")
    df = df[df["data_operacao"].notna()]
    df["data_criacao"] = df["waybill"].apply(_extrair_data_criacao)
    df = df[df["data_criacao"].notna()]
    df["dias"] = (df["data_operacao"] - df["data_criacao"]).dt.days
    df = df[df["dias"] >= 0]
    if df.empty:
        return df
    ref_ts = pd.Timestamp(data_ref)
    df["semana"] = ref_ts.strftime("w%V")
    df["ano"]    = int(ref_ts.year)
    return (
        df.groupby(["estado", "semana", "ano", "cliente"])
        .agg(
            p50_dias    = ("dias", lambda x: round(float(np.percentile(x, 50)), 1)),
            p80_dias    = ("dias", lambda x: round(float(np.percentile(x, 80)), 1)),
            p90_dias    = ("dias", lambda x: round(float(np.percentile(x, 90)), 1)),
            qtd_pedidos = ("dias", "count")
        )
        .reset_index()
    )


def _ler_p90(arquivo):
    df = xlsx_para_dataframe(arquivo)
    if df.empty:
        return df
    df.columns = [
        "waybill", "status", "tipo_operacao", "cliente",
        "data_operacao", "proximo_ponto", "operador",
        "ponto_operacao", "estado", "regiao"
    ]
    return df


# ================================
# 📊 DEVOLUÇÃO — P90
# ================================
def importar_p90(arquivo, data_ref):
    df = _ler_p90(arquivo)
    if df.empty:
        return {"registros": 0, "detalhe": "Arquivo vazio"}
    linhas = len(df)
    agg = _transformar_p90(df, data_ref)
    if agg.empty:
        return {"registros": 0, "detalhe": f"{linhas:,} lidas → 0 devoluções encontradas"}
    agg["data_referencia"] = data_ref
    agg["nome_arquivo"]    = arquivo.name
    agg["data_importacao"] = datetime.now(timezone.utc)
    _persistir_p90_arquivo(agg, arquivo.name)
    limpar_historico_antigo()
    grupos = len(agg)
    return {"registros": grupos, "detalhe": f"{linhas:,} lidas → {grupos:,} grupos estado/cliente"}


def _agregar_status_iata_folha(df, semana, ano, data_ref, nome_arquivo, agora):
    """Agrega status e iata a partir da folha de devolução."""
    status_agg = (
        df.groupby(["status", "estado", "cliente"])
        .size().reset_index(name="qtd")
    )
    status_agg["semana"]           = semana
    status_agg["ano"]              = ano
    status_agg["data_referencia"]  = data_ref
    status_agg["nome_arquivo"]     = nome_arquivo
    status_agg["data_importacao"]  = agora
    status_agg["cliente_fantasia"] = None

    iata_agg = (
        df.groupby(["ponto_operacao", "estado"])
        .size().reset_index(name="qtd")
    )
    iata_agg["semana"]           = semana
    iata_agg["ano"]              = ano
    iata_agg["data_referencia"]  = data_ref
    iata_agg["nome_arquivo"]     = nome_arquivo
    iata_agg["data_importacao"]  = agora
    iata_agg["cliente_fantasia"] = None
    return status_agg, iata_agg


def _persistir_devolucoes(status_agg, iata_agg, nome_arquivo):
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
            cur.execute(f"DELETE FROM {tabela} WHERE nome_arquivo = %s", [nome_arquivo])
        execute_values(cur,
            f"INSERT INTO dev_status_semanal ({','.join(colunas_status)}) VALUES %s",
            [tuple(_val(v) for v in row)
             for row in status_agg[colunas_status].itertuples(index=False, name=None)]
        )
        execute_values(cur,
            f"INSERT INTO dev_iatas_semanal ({','.join(colunas_iata)}) VALUES %s",
            [tuple(_val(v) for v in row)
             for row in iata_agg[colunas_iata].itertuples(index=False, name=None)]
        )
        conn.commit()
        cur.close()


# ================================
# 🔁 DEVOLUÇÃO (arquivo Folha_de_registro)
# ================================
def importar_devolucoes(arquivo, data_ref):
    df = xlsx_para_dataframe(arquivo)
    if df.empty:
        return {"registros": 0, "detalhe": "Arquivo vazio"}
    linhas = len(df)
    df.columns = [
        "waybill", "status", "tipo_operacao", "cliente",
        "data_operacao", "proximo_ponto", "operador",
        "ponto_operacao", "estado", "regiao"
    ]
    data_ref_ts = pd.Timestamp(data_ref)
    semana = data_ref_ts.strftime("w%V")
    ano    = int(data_ref_ts.year)
    agora  = datetime.now(timezone.utc)
    status_agg, iata_agg = _agregar_status_iata_folha(df, semana, ano, data_ref, arquivo.name, agora)
    _persistir_devolucoes(status_agg, iata_agg, arquivo.name)
    limpar_historico_antigo()
    grupos = len(status_agg) + len(iata_agg)
    return {"registros": grupos, "detalhe": f"{linhas:,} lidas → {grupos:,} grupos status/iata"}


# ================================
# 📊 DEVOLUÇÃO - MONITORAMENTO (arquivo monitoramento_da_pontualidade)
# ================================
def _agregar_sla(df, col_estado, col_cliente, data_ref, nome_arquivo, agora):
    """Agrega SLA de entrega a partir de df com assinatura/data_criacao/prazo_dias."""
    df_ent = df[df["assinatura"].notna()].copy()
    if df_ent.empty:
        return pd.DataFrame()
    df_ent["dias"]     = (df_ent["assinatura"] - df_ent["data_criacao"]).dt.total_seconds() / 86400
    df_ent["prazo"]    = df_ent["prazo_dias"].fillna(7) if "prazo_dias" in df_ent.columns else 7
    df_ent["no_prazo"] = df_ent["dias"] <= df_ent["prazo"]
    agg = (
        df_ent.groupby([col_estado, col_cliente, "cliente_fantasia"], dropna=False)
        .agg(qtd_total=("waybill", "count"), qtd_no_prazo=("no_prazo", "sum"))
        .reset_index()
        .rename(columns={col_estado: "estado", col_cliente: "cliente"})
    )
    agg["data_referencia"] = data_ref
    agg["nome_arquivo"]    = nome_arquivo
    agg["data_importacao"] = agora
    return agg


def _agregar_motivos(df, col_estado, col_cliente, data_ref, nome_arquivo, agora):
    """Agrega motivos de devolução."""
    df_mot = df[df["motivo"].notna()].copy()
    if df_mot.empty:
        return pd.DataFrame()
    agg = (
        df_mot.groupby([col_estado, "motivo", col_cliente, "cliente_fantasia"], dropna=False)
        .size().reset_index(name="qtd")
        .rename(columns={col_estado: "estado", col_cliente: "cliente"})
    )
    agg["data_referencia"] = data_ref
    agg["nome_arquivo"]    = nome_arquivo
    agg["data_importacao"] = agora
    return agg


def _salvar_dev_resumo(cur, df_save, nome_arq, agora, data_ref):
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
    colunas = ["semana", "ano", "data_referencia", "status",
               "cliente", "estado_dest", "motivo", "qtd",
               "nome_arquivo", "data_importacao"]
    execute_values(cur,
        f"INSERT INTO dev_resumo ({','.join(colunas)}) VALUES %s",
        [tuple(_val(v) for v in row)
         for row in df_resumo_dev[colunas].itertuples(index=False, name=None)]
    )


def _salvar_status_iata(cur, df, semana, ano, data_ref, nome_arq, agora):
    for tabela in ["dev_status_semanal", "dev_iatas_semanal"]:
        cur.execute(f"DELETE FROM {tabela} WHERE data_referencia = %s", [data_ref])
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


def _salvar_sla_motivos_dsp(cur, df_mon_full, data_ref, nome_arq, agora):
    for tabela in ["dev_sla_semanal", "dev_motivos_semanal", "dev_dsp_sem3tent"]:
        cur.execute(f"DELETE FROM {tabela} WHERE data_referencia = %s", [data_ref])
    sla_agg     = _agregar_sla(df_mon_full, "estado_dest", "cliente_mon", data_ref, nome_arq, agora)
    motivos_agg = _agregar_motivos(df_mon_full, "estado_dest", "cliente_mon", data_ref, nome_arq, agora)
    dsp_agg     = _agregar_dsp_sem3tent(df_mon_full, "estado_dest", "cliente_mon", data_ref, nome_arq, agora)
    colunas_sla = ["estado", "data_referencia", "cliente", "cliente_fantasia", "qtd_total", "qtd_no_prazo", "nome_arquivo", "data_importacao"]
    colunas_mot = ["estado", "motivo", "cliente", "cliente_fantasia", "data_referencia", "qtd", "nome_arquivo", "data_importacao"]
    colunas_dsp = ["ponto_entrada", "estado", "motivo", "cliente", "cliente_fantasia", "data_referencia", "qtd", "nome_arquivo", "data_importacao"]
    if not sla_agg.empty:
        execute_values(cur,
            f"INSERT INTO dev_sla_semanal ({','.join(colunas_sla)}) VALUES %s",
            [tuple(_val(v) for v in row) for row in sla_agg[colunas_sla].itertuples(index=False, name=None)]
        )
    if not motivos_agg.empty:
        execute_values(cur,
            f"INSERT INTO dev_motivos_semanal ({','.join(colunas_mot)}) VALUES %s",
            [tuple(_val(v) for v in row) for row in motivos_agg[colunas_mot].itertuples(index=False, name=None)]
        )
    if not dsp_agg.empty:
        execute_values(cur,
            f"INSERT INTO dev_dsp_sem3tent ({','.join(colunas_dsp)}) VALUES %s",
            [tuple(_val(v) for v in row) for row in dsp_agg[colunas_dsp].itertuples(index=False, name=None)]
        )


def _salvar_p90(cur, df, semana, ano, data_ref, nome_arq, agora):
    """Agrega e persiste p90_semanal a partir de dev_detalhado. Recebe cursor aberto."""
    cur.execute("DELETE FROM p90_semanal WHERE data_referencia = %s", [data_ref])
    df_src = df[df["status"] == "Recebido de devolução"].copy()
    if df_src.empty:
        return
    df_src["estado_p90"] = df_src["estado_dest"].fillna(df_src["estado"])
    df_src = df_src[df_src["dias_dev"] >= 0].dropna(subset=["estado_p90", "dias_dev"])
    if df_src.empty:
        return
    p90_agg = (
        df_src.groupby(["estado_p90", "cliente"])
        .agg(
            p50_dias    = ("dias_dev", lambda x: round(float(np.percentile(x, 50)), 1)),
            p80_dias    = ("dias_dev", lambda x: round(float(np.percentile(x, 80)), 1)),
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
        "estado", "semana", "ano", "cliente", "p50_dias", "p80_dias", "p90_dias",
        "qtd_pedidos", "data_referencia", "nome_arquivo", "data_importacao"
    ]
    execute_values(cur,
        f"INSERT INTO p90_semanal ({','.join(colunas_p90)}) VALUES %s",
        [tuple(_val(v) for v in row)
         for row in p90_agg[colunas_p90].itertuples(index=False, name=None)]
    )


def _agregar_dsp_sem3tent(df, col_estado, col_cliente, data_ref, nome_arquivo, agora):
    """Agrega DSPs sem 3 tentativas."""
    cols_req = ["motivo", "tent1", "tent3", "assinatura"]
    if not all(c in df.columns for c in cols_req):
        return pd.DataFrame()
    dsp = df[
        df["motivo"].notna() & df["tent1"].notna() &
        df["tent3"].isna()   & df["assinatura"].isna()
    ].copy()
    if dsp.empty:
        return pd.DataFrame()
    agg = (
        dsp.groupby(["ponto_entrada", col_estado, "motivo", col_cliente, "cliente_fantasia"], dropna=False)
        .size().reset_index(name="qtd")
        .rename(columns={col_estado: "estado", col_cliente: "cliente"})
    )
    agg["data_referencia"] = data_ref
    agg["nome_arquivo"]    = nome_arquivo
    agg["data_importacao"] = agora
    return agg


def _ler_monitoramento_simples(arquivo):
    """Lê e prepara o DataFrame de monitoramento pontual (sem join com folha)."""
    df = xlsx_para_dataframe(
        arquivo,
        usecols=[0, 4, 8, 11, 21, 22, 25, 33, 66, 67, 68, 71, 73]
    )
    if df.empty:
        return df
    df.columns = [
        "waybill", "status", "motivo", "estado", "cliente",
        "cliente_fantasia", "ponto_entrada", "data_criacao",
        "tent1", "tent2", "tent3", "assinatura", "prazo_dias"
    ]
    for col in ["tent1", "tent2", "tent3", "assinatura", "data_criacao"]:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df["cliente_fantasia"] = df["cliente_fantasia"].fillna("Shein Nacional")
    return df


def importar_devolucao_monitoramento(arquivo, data_ref):
    df = _ler_monitoramento_simples(arquivo)
    if df.empty:
        return {"registros": 0, "detalhe": "Arquivo vazio"}
    linhas = len(df)
    agora       = datetime.now(timezone.utc)
    sla_agg     = _agregar_sla(df, "estado", "cliente", data_ref, arquivo.name, agora)
    motivos_agg = _agregar_motivos(df, "estado", "cliente", data_ref, arquivo.name, agora)
    dsp_agg     = _agregar_dsp_sem3tent(df, "estado", "cliente", data_ref, arquivo.name, agora)
    with _conn("DATABASE_URL_DEVOLUCOES") as conn:
        cur = conn.cursor()
        _salvar_sla_motivos_dsp(cur, df, data_ref, arquivo.name, agora)
        conn.commit()
        cur.close()
    limpar_historico_antigo()
    grupos = len(sla_agg) + len(motivos_agg) + len(dsp_agg)
    return {"registros": grupos, "detalhe": f"{linhas:,} lidas → {grupos:,} grupos sla/motivos/dsp"}


def _ler_monitoramento(arquivo_monitor):
    """Lê o arquivo de monitoramento e retorna (df_mon_full, df_mon) prontos para uso."""
    with io.BytesIO(arquivo_monitor.read()) as buf:
        df_raw = xlsx_para_dataframe(buf)
    arquivo_monitor.seek(0)

    cols_full = [0, 4, 8, 11, 12, 21, 22, 24, 25, 33, 66, 67, 68, 71, 73]
    cols_full = [c for c in cols_full if c < len(df_raw.columns)]
    df_mon_full = df_raw.iloc[:, cols_full].copy()
    df_mon_full.columns = [
        "waybill", "status_mon", "motivo", "estado_dest", "cidade_dest",
        "cliente_mon", "cliente_fantasia", "pre_entrega", "ponto_entrada", "data_criacao",
        "tent1", "tent2", "tent3", "assinatura", "prazo_dias"
    ][:len(cols_full)]
    for col in ["tent1", "tent2", "tent3", "assinatura", "data_criacao"]:
        if col in df_mon_full.columns:
            df_mon_full[col] = pd.to_datetime(df_mon_full[col], errors="coerce")
    df_mon_full["waybill"] = df_mon_full["waybill"].astype(str).str.strip()
    if "cliente_fantasia" in df_mon_full.columns:
        df_mon_full["cliente_fantasia"] = df_mon_full["cliente_fantasia"].fillna("Shein Nacional")

    merge_cols = [c for c in ["waybill", "status_mon", "motivo", "estado_dest", "cidade_dest",
                               "cliente_mon", "pre_entrega", "ponto_entrada", "data_criacao"]
                  if c in df_mon_full.columns]
    df_mon = df_mon_full[merge_cols].copy()
    return df_mon_full, df_mon


def _preparar_df_detalhado(df_dev, df_mon, data_ref, nome_arq, agora):
    """Faz merge, calcula dias_dev, preenche data_criacao ausente e adiciona metadados."""
    df = df_dev.merge(df_mon, on="waybill", how="left")
    df["dias_dev"] = (df["data_operacao"] - df["data_criacao"]).dt.days

    sem_criacao = df["data_criacao"].isna()
    if sem_criacao.any():
        df.loc[sem_criacao, "data_criacao"] = df.loc[sem_criacao, "waybill"].apply(_data_do_waybill)
        df.loc[sem_criacao, "dias_dev"] = (
            (df.loc[sem_criacao, "data_operacao"] - df.loc[sem_criacao, "data_criacao"]).dt.days
        )

    df = df[df["dias_dev"].isna() | (df["dias_dev"] >= 0)]

    ref_ts = pd.Timestamp(data_ref)
    df["semana"]          = ref_ts.strftime("w%V")
    df["ano"]             = int(ref_ts.year)
    df["data_referencia"] = data_ref
    df["nome_arquivo"]    = nome_arq
    df["data_importacao"] = agora
    return df


# ================================
# 📦 PACOTES GRANDES (AJG)
# ================================
def importar_pacotes_grandes(arquivo, data_ref=None):
    df = xlsx_para_dataframe(arquivo)
    if df.empty:
        return {"registros": 0, "detalhe": "Arquivo vazio"}
    linhas = len(df)

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
        tuple(_val(v) for v in row)
        for row in df[colunas].itertuples(index=False, name=None)
    ]

    with _conn("DATABASE_URL_OPERACIONAL") as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM pacotes_grandes WHERE nome_arquivo = %s", [arquivo.name])
        execute_values(cur, f"INSERT INTO pacotes_grandes ({','.join(colunas)}) VALUES %s", values)
        conn.commit()
        cur.close()
    return {"registros": linhas, "detalhe": f"{linhas:,} pacotes grandes importados"}
# ================================
# 📊 DEVOLUÇÃO ENRIQUECIDA (Folha + Monitoramento)
# ================================
def _ler_folha_devolucao(arquivo_folha):
    """Lê e prepara a folha de registro de devoluções."""
    with io.BytesIO(arquivo_folha.read()) as buf:
        df_dev = xlsx_para_dataframe(buf)
    arquivo_folha.seek(0)
    df_dev = df_dev.iloc[:, :10]
    df_dev.columns = [
        "waybill", "status", "tipo_operacao", "cliente",
        "data_operacao", "proximo_ponto", "operador",
        "ponto_operacao", "estado", "regiao"
    ]
    df_dev["data_operacao"] = pd.to_datetime(df_dev["data_operacao"], errors="coerce")
    df_dev["waybill"] = df_dev["waybill"].astype(str).str.strip()
    return df_dev


def _persistir_enriquecida(cur, df_save, colunas_det, df, df_mon_full,
                            semana, ano, data_ref, nome_arq, agora):
    """Persiste todos os dados da devolução enriquecida num cursor já aberto."""
    cur.execute("DELETE FROM dev_detalhado WHERE data_referencia = %s", [data_ref])
    execute_values(cur,
        f"INSERT INTO dev_detalhado ({','.join(colunas_det)}) VALUES %s",
        [tuple(_val(v) for v in row) for row in df_save.itertuples(index=False, name=None)]
    )
    _salvar_dev_resumo(cur, df_save, nome_arq, agora, data_ref)
    _salvar_status_iata(cur, df, semana, ano, data_ref, nome_arq, agora)
    _salvar_p90(cur, df, semana, ano, data_ref, nome_arq, agora)
    _salvar_sla_motivos_dsp(cur, df_mon_full, data_ref, nome_arq, agora)


def importar_devolucao_enriquecida(arquivo_folha, arquivo_monitor, data_ref):
    df_dev = _ler_folha_devolucao(arquivo_folha)
    df_mon_full, df_mon = _ler_monitoramento(arquivo_monitor)
    linhas_folha = len(df_dev)
    linhas_mon   = len(df_mon_full)
    ref_ts   = pd.Timestamp(data_ref)
    semana   = ref_ts.strftime("w%V")
    ano      = int(ref_ts.year)
    nome_arq = f"{arquivo_folha.name}+{arquivo_monitor.name}"
    agora    = datetime.now(timezone.utc)
    df = _preparar_df_detalhado(df_dev, df_mon, data_ref, nome_arq, agora)
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
    with _conn("DATABASE_URL_DEVOLUCOES") as conn:
        cur = conn.cursor()
        _persistir_enriquecida(cur, df_save, colunas_det, df, df_mon_full,
                               semana, ano, data_ref, nome_arq, agora)
        conn.commit()
        cur.close()
    limpar_historico_antigo()
    return {"registros": len(df_save), "detalhe": f"Folha: {linhas_folha:,} lidas | Monitor: {linhas_mon:,} lidas → {len(df_save):,} registros detalhados"}


# ================================
# 🛍️ SHEIN — BACKLOG COMPLETO
# ================================
def _bulk_insert(tabela, colunas, df):
    """Insert em lote via execute_values no banco de devoluções."""
    valores = [
        tuple(_val(v) for v in row)
        for row in df[colunas].itertuples(index=False, name=None)
    ]
    if not valores:
        return
    sql = f"INSERT INTO {tabela} ({','.join(colunas)}) VALUES %s"
    with _conn("DATABASE_URL_DEVOLUCOES") as conn:
        cur = conn.cursor()
        try:
            execute_values(cur, sql, valores)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()


def importar_shein_backlog(arq_insucesso, arq_folha, arq_monitoramento, data_ref):
    """
    Processa o backlog Shein cruzando três fontes:
      - Insucesso LM (shpp_no): lista de AJs em aberto enviada pela Shein
      - Folha de Devolução: status atual de cada AJ no Express
      - Monitoramento de Pontualidade: motivos, estados e SLA

    Segmentação automática pelo campo cliente no Monitoramento:
      sheind2d → D2D | szanjun → Internacional | shein → Nacional

    Tabelas gravadas (DATABASE_URL_DEVOLUCOES):
      dev_shein_backlog, dev_shein_sla, dev_shein_motivos, dev_shein_aging
    """
    COL_WB_FOLHA  = "运单号(Número do Waybill)"
    COL_ST_FOLHA  = "运单状态(Status do Pacote)"
    COL_OP_FOLHA  = "操作时间(tempo de operação)"

    COL_WB_MON    = "运单号(Número do Waybill)"
    COL_CLI_MON   = "客户名称(Nome do cliente)"
    COL_MOTIVO    = "问题件原因(Motivo da Ocorrência)"

    COL_WB_LM     = "shpp_no"
    COL_D2D       = "is_d2d"
    COL_AGING_DAY = "aging_day"
    COL_AGING_RNG = "aging_range"
    COL_DATA_INI  = "return_initiaded_data"

    STATUS_CONCLUIDO        = {"Recebido de devolução"}
    STATUS_REMOVER_BACKLOG  = {"Recebido de devolução", "Pedido entregue"}

    agora    = datetime.now(timezone.utc)
    nome_arq = arq_insucesso.name

    # ── 1. Leitura ────────────────────────────────────────────────────────
    df_lm  = pd.read_excel(io.BytesIO(arq_insucesso.read()))
    df_fol = pd.read_excel(io.BytesIO(arq_folha.read()))
    df_mon = pd.read_excel(io.BytesIO(arq_monitoramento.read()))

    df_lm[COL_WB_LM]    = df_lm[COL_WB_LM].astype(str).str.strip()
    df_fol[COL_WB_FOLHA] = df_fol[COL_WB_FOLHA].astype(str).str.strip()
    df_mon[COL_WB_MON]  = df_mon[COL_WB_MON].astype(str).str.strip()

    ajs_lm = set(df_lm[COL_WB_LM].dropna())

    # ── 2. Filtrar pelos AJs do LM ────────────────────────────────────────
    df_fol_shein = df_fol[df_fol[COL_WB_FOLHA].isin(ajs_lm)].copy()
    df_mon_shein = df_mon[df_mon[COL_WB_MON].isin(ajs_lm)].copy()

    # ── 3. Segmentação ────────────────────────────────────────────────────
    mapa_segmento_mon = {}
    for _, row in df_mon_shein[[COL_WB_MON, COL_CLI_MON]].iterrows():
        wb  = row[COL_WB_MON]
        cli = str(row[COL_CLI_MON]).strip().lower() if pd.notna(row[COL_CLI_MON]) else ""
        if cli == "sheind2d":
            mapa_segmento_mon[wb] = "D2D"
        elif cli == "szanjun":
            mapa_segmento_mon[wb] = "Internacional"
        elif cli == "shein":
            mapa_segmento_mon[wb] = "Nacional"
        else:
            mapa_segmento_mon[wb] = "Outros"

    mapa_d2d_lm = dict(zip(df_lm[COL_WB_LM], df_lm[COL_D2D].astype(str).str.strip()))

    def _segmento(wb):
        if wb in mapa_segmento_mon:
            return mapa_segmento_mon[wb]
        return "D2D" if mapa_d2d_lm.get(wb, "No") == "Yes" else "Nacional"

    df_lm["segmento"] = df_lm[COL_WB_LM].map(_segmento)

    # ── 4. dev_shein_backlog ──────────────────────────────────────────────
    if not df_fol_shein.empty and COL_ST_FOLHA in df_fol_shein.columns:
        sort_col = COL_OP_FOLHA if COL_OP_FOLHA in df_fol_shein.columns else df_fol_shein.columns[0]
        df_fol_ultimo = (
            df_fol_shein
            .sort_values(sort_col, ascending=False)
            .drop_duplicates(subset=[COL_WB_FOLHA])
            [[COL_WB_FOLHA, COL_ST_FOLHA]]
            .rename(columns={COL_WB_FOLHA: "waybill", COL_ST_FOLHA: "status_folha"})
        )
    else:
        df_fol_ultimo = pd.DataFrame(columns=["waybill", "status_folha"])

    df_backlog = df_lm[[COL_WB_LM, COL_D2D, COL_AGING_DAY,
                         COL_AGING_RNG, COL_DATA_INI, "segmento"]].copy()
    df_backlog = df_backlog.rename(columns={
        COL_WB_LM:     "waybill",
        COL_D2D:       "is_d2d",
        COL_AGING_DAY: "aging_day",
        COL_AGING_RNG: "aging_range",
        COL_DATA_INI:  "return_initiaded_data",
    })
    df_backlog = df_backlog.merge(df_fol_ultimo, on="waybill", how="left")
    df_backlog["data_referencia"] = data_ref
    df_backlog["data_importacao"] = agora
    df_backlog["nome_arquivo"]    = nome_arq

    df_backlog_ativo = df_backlog[
        ~df_backlog["status_folha"].isin(STATUS_REMOVER_BACKLOG)
    ].copy()

    # ── 5. dev_shein_sla ──────────────────────────────────────────────────
    df_sla_rows = []
    for segmento, grp in df_backlog.groupby("segmento"):
        total      = len(grp)
        concluidos = int(grp["status_folha"].isin(STATUS_CONCLUIDO).sum())
        df_sla_rows.append({
            "segmento":        segmento,
            "qtd_total":       total,
            "qtd_concluido":   concluidos,
            "qtd_pendente":    total - concluidos,
            "pct_sla":         round(concluidos / total * 100, 2) if total > 0 else 0,
            "data_referencia": data_ref,
            "data_importacao": agora,
            "nome_arquivo":    nome_arq,
        })
    df_sla = pd.DataFrame(df_sla_rows)

    # ── 6. dev_shein_motivos ──────────────────────────────────────────────
    if not df_mon_shein.empty and COL_MOTIVO in df_mon_shein.columns:
        df_mon_shein["segmento"] = df_mon_shein[COL_WB_MON].map(_segmento)
        df_mot = (
            df_mon_shein
            .groupby(["segmento", COL_MOTIVO])
            .size()
            .reset_index(name="qtd")
            .rename(columns={COL_MOTIVO: "motivo"})
        )
        df_mot["motivo"] = df_mot["motivo"].fillna("Pacote cancelado")
        df_mot["motivo"] = df_mot["motivo"].replace("0", "Sem falha de entrega")
        df_mot["data_referencia"] = data_ref
        df_mot["data_importacao"] = agora
        df_mot["nome_arquivo"]    = nome_arq
    else:
        df_mot = pd.DataFrame(columns=["segmento", "motivo", "qtd",
                                        "data_referencia", "data_importacao", "nome_arquivo"])

    # ── 7. dev_shein_aging ────────────────────────────────────────────────
    df_aging = (
        df_lm.groupby(["segmento", COL_AGING_RNG])
        .size()
        .reset_index(name="qtd")
        .rename(columns={COL_AGING_RNG: "aging_range"})
    )
    df_aging["data_referencia"] = data_ref
    df_aging["data_importacao"] = agora
    df_aging["nome_arquivo"]    = nome_arq

    # ── 8. Persistir ──────────────────────────────────────────────────────
    total_gravado = 0

    executar_devolucoes("DELETE FROM dev_shein_backlog WHERE nome_arquivo = %s", [nome_arq])
    if not df_backlog_ativo.empty:
        cols_bk = ["waybill", "segmento", "is_d2d", "aging_day", "aging_range",
                   "return_initiaded_data", "status_folha",
                   "data_referencia", "data_importacao", "nome_arquivo"]
        _bulk_insert("dev_shein_backlog", cols_bk, df_backlog_ativo[cols_bk])
        total_gravado += len(df_backlog_ativo)

    executar_devolucoes("DELETE FROM dev_shein_sla WHERE nome_arquivo = %s", [nome_arq])
    if not df_sla.empty:
        cols_sla = ["segmento", "qtd_total", "qtd_concluido", "qtd_pendente", "pct_sla",
                    "data_referencia", "data_importacao", "nome_arquivo"]
        _bulk_insert("dev_shein_sla", cols_sla, df_sla[cols_sla])
        total_gravado += len(df_sla)

    executar_devolucoes("DELETE FROM dev_shein_motivos WHERE nome_arquivo = %s", [nome_arq])
    if not df_mot.empty:
        cols_mot = ["segmento", "motivo", "qtd",
                    "data_referencia", "data_importacao", "nome_arquivo"]
        _bulk_insert("dev_shein_motivos", cols_mot, df_mot[cols_mot])
        total_gravado += len(df_mot)

    executar_devolucoes("DELETE FROM dev_shein_aging WHERE nome_arquivo = %s", [nome_arq])
    if not df_aging.empty:
        cols_ag = ["segmento", "aging_range", "qtd",
                   "data_referencia", "data_importacao", "nome_arquivo"]
        _bulk_insert("dev_shein_aging", cols_ag, df_aging[cols_ag])
        total_gravado += len(df_aging)

    return {
        "registros": total_gravado,
        "detalhe": (
            f"LM: {len(df_lm)} AJs | "
            f"Backlog ativo: {len(df_backlog_ativo)} | "
            f"Match Folha: {len(df_fol_shein)} | "
            f"Match Monitoramento: {len(df_mon_shein)}"
        ),
    }


# ================================
# 🚛 COLETAS — CARREGAMENTO/DESCARREGAMENTO
# ================================
def _coletas_colunas_base(df):
    """Renomeia as 19 colunas do arquivo Monitoramento_de_dados_de_caminhões."""
    df = df.iloc[:, :19].copy()
    df.columns = [
        "num_registro",           # A
        "placa",                  # B
        "carregador",             # C
        "rede_carregador",        # D ← filtro saída: SP-RR-001
        "endereco_carga",         # E
        "tempo_carregamento",     # F
        "secao_destino",          # G
        "descarregador",          # H
        "rede_descarregador",     # I ← filtro descarregamento: SP-RR-001 ou ANJUN
        "endereco_descarga",      # J
        "tempo_descarga",         # K
        "sacos_carregados",       # L
        "sacos_descarregados",    # M
        "dif_sacos",              # N
        "pacotes_carregados",     # O
        "pacotes_descarregados",  # P
        "dif_pacotes",            # Q
        "modo_operacao",          # R
        "tipo_veiculo",           # S
    ]
    df["tempo_carregamento"] = pd.to_datetime(df["tempo_carregamento"], errors="coerce")
    df["tempo_descarga"]     = pd.to_datetime(df["tempo_descarga"],     errors="coerce")
    for col in ["sacos_carregados", "sacos_descarregados", "dif_sacos",
                "pacotes_carregados", "pacotes_descarregados", "dif_pacotes"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df


def _salvar_coletas(df, arquivo, data_ref, tipo):
    df = df.copy()
    df["tipo"]            = tipo
    df["data_referencia"] = data_ref
    df["nome_arquivo"]    = arquivo.name
    df["data_importacao"] = datetime.now(timezone.utc)

    colunas = [
        "num_registro", "placa", "carregador", "rede_carregador",
        "tempo_carregamento", "secao_destino",
        "descarregador", "rede_descarregador", "tempo_descarga",
        "sacos_carregados", "sacos_descarregados", "dif_sacos",
        "pacotes_carregados", "pacotes_descarregados", "dif_pacotes",
        "modo_operacao", "tipo_veiculo",
        "tipo", "data_referencia", "nome_arquivo", "data_importacao"
    ]

    with _conn("DATABASE_URL_COLETAS") as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM coletas WHERE nome_arquivo = %s AND tipo = %s",
            [arquivo.name, tipo]
        )
        values = [
            tuple(_val(v) for v in row)
            for row in df[colunas].itertuples(index=False, name=None)
        ]
        execute_values(cur, f"INSERT INTO coletas ({','.join(colunas)}) VALUES %s", values)
        conn.commit()
        cur.close()
    return len(df)


def importar_coletas(arquivo, data_ref):
    """Descarregamento recebido em Perus: col I (rede_descarregador) = SP-RR-001 ou ANJUN."""
    df = xlsx_para_dataframe(arquivo)
    if df.empty:
        return {"registros": 0, "detalhe": "Arquivo vazio"}
    linhas = len(df)
    df = _coletas_colunas_base(df)
    df = df[df["rede_descarregador"].isin(["SP-RR-001", "ANJUN"])].copy()
    if df.empty:
        return {"registros": 0, "detalhe": f"{linhas:,} lidas → 0 com rede_descarregador=SP-RR-001/ANJUN"}
    qtd = _salvar_coletas(df, arquivo, data_ref, "descarregamento")
    return {"registros": qtd, "detalhe": f"{linhas:,} lidas → {qtd:,} veículos descarregados em Perus"}


def importar_coletas_saida(arquivo, data_ref):
    """Saída de Perus para outras bases: col D (rede_carregador) = SP-RR-001."""
    df = xlsx_para_dataframe(arquivo)
    if df.empty:
        return {"registros": 0, "detalhe": "Arquivo vazio"}
    linhas = len(df)
    df = _coletas_colunas_base(df)
    df = df[df["rede_carregador"] == "SP-RR-001"].copy()
    if df.empty:
        return {"registros": 0, "detalhe": f"{linhas:,} lidas → 0 com rede_carregador=SP-RR-001"}
    qtd = _salvar_coletas(df, arquivo, data_ref, "saida")
    return {"registros": qtd, "detalhe": f"{linhas:,} lidas → {qtd:,} veículos saídos de Perus"}


# ================================
# 📦 COLETAS — ITENS GRANDES
# ================================
def importar_coletas_grandes(arquivo, data_ref):
    """
    Importa Registro_de_coleta_de_itens_grandes.
    10 colunas: tempo_coleta, cliente, waybill_anjun, waybill_escaneado,
                coletador, ponto_responsavel, estado_origem,
                num_registro_carro, placa, motorista
    """
    df = xlsx_para_dataframe(arquivo)
    if df.empty:
        return {"registros": 0, "detalhe": "Arquivo vazio"}
    linhas = len(df)
    df = df.iloc[:, :10].copy()
    df.columns = [
        "tempo_coleta", "cliente", "waybill_anjun", "waybill_escaneado",
        "coletador", "ponto_responsavel", "estado_origem",
        "num_registro_carro", "placa", "motorista"
    ]
    df["tempo_coleta"]    = pd.to_datetime(df["tempo_coleta"], errors="coerce")
    df["data_referencia"] = data_ref
    df["nome_arquivo"]    = arquivo.name
    df["data_importacao"] = datetime.now(timezone.utc)

    colunas = [
        "tempo_coleta", "cliente", "waybill_anjun", "waybill_escaneado",
        "coletador", "ponto_responsavel", "estado_origem",
        "num_registro_carro", "placa", "motorista",
        "data_referencia", "nome_arquivo", "data_importacao"
    ]
    with _conn("DATABASE_URL_COLETAS") as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM coletas_grandes WHERE nome_arquivo = %s", [arquivo.name])
        values = [
            tuple(_val(v) for v in row)
            for row in df[colunas].itertuples(index=False, name=None)
        ]
        execute_values(cur, f"INSERT INTO coletas_grandes ({','.join(colunas)}) VALUES %s", values)
        conn.commit()
        cur.close()
    return {"registros": linhas, "detalhe": f"{linhas:,} waybills de itens grandes importados"}


# ================================
# 📊 COLETAS — MONITORAMENTO FINAL
# ================================
def importar_coleta_final(arquivo, data_ref):
    """
    Importa Monitoramento_de_Dados_de_Coleta_Final.
    13 colunas: data, cliente, pac_a_coletar, pac_coletados, taxa_coleta,
                dif_coleta, pedidos_nao_coletados, falta_bipagem_coleta,
                perda_coleta, pac_carregados, dif_carregamento,
                falta_bipagem_carga, perda_carga
    """
    df = xlsx_para_dataframe(arquivo)
    if df.empty:
        return {"registros": 0, "detalhe": "Arquivo vazio"}
    linhas = len(df)
    df = df.iloc[:, :13].copy()
    df.columns = [
        "data", "cliente",
        "pac_a_coletar", "pac_coletados", "taxa_coleta",
        "dif_coleta", "pedidos_nao_coletados",
        "falta_bipagem_coleta", "perda_coleta",
        "pac_carregados", "dif_carregamento",
        "falta_bipagem_carga", "perda_carga"
    ]
    df = df[df["cliente"].notna()].copy()
    df["data"] = pd.to_datetime(df["data"], errors="coerce")
    for col in ["pac_a_coletar", "pac_coletados", "dif_coleta",
                "pedidos_nao_coletados", "falta_bipagem_coleta", "perda_coleta",
                "pac_carregados", "dif_carregamento", "falta_bipagem_carga", "perda_carga"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    df["taxa_coleta"] = (
        df["taxa_coleta"].astype(str)
        .str.replace("%", "", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
    )
    df["data_referencia"] = data_ref
    df["nome_arquivo"]    = arquivo.name
    df["data_importacao"] = datetime.now(timezone.utc)

    colunas = [
        "data", "cliente",
        "pac_a_coletar", "pac_coletados", "taxa_coleta",
        "dif_coleta", "pedidos_nao_coletados",
        "falta_bipagem_coleta", "perda_coleta",
        "pac_carregados", "dif_carregamento",
        "falta_bipagem_carga", "perda_carga",
        "data_referencia", "nome_arquivo", "data_importacao"
    ]
    with _conn("DATABASE_URL_COLETAS") as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM coleta_final WHERE nome_arquivo = %s", [arquivo.name])
        values = [
            tuple(_val(v) for v in row)
            for row in df[colunas].itertuples(index=False, name=None)
        ]
        execute_values(cur, f"INSERT INTO coleta_final ({','.join(colunas)}) VALUES %s", values)
        conn.commit()
        cur.close()
    qtd = len(df)
    return {"registros": qtd, "detalhe": f"{linhas:,} lidas → {qtd:,} linhas de monitoramento final importadas"}


# ================================
# 🔀 COLETAS — IMPORTAÇÃO AUTOMÁTICA
# ================================
def importar_coletas_auto(arquivo, data_ref):
    """
    Detecta o tipo de arquivo de coletas pelo número de colunas e importa:
    - >= 19 cols → Monitoramento de caminhões (grava descarregamento + saída juntos)
    - >= 13 cols → Monitoramento Final (coleta_final)
    -  >= 10 cols → Itens Grandes (coletas_grandes)
    """
    df = xlsx_para_dataframe(arquivo)
    if df.empty:
        return {"registros": 0, "detalhe": "Arquivo vazio"}

    ncols = df.shape[1]

    if ncols >= 19:
        # Arquivo de caminhões — processa descarregamento E saída na mesma operação
        df_base = _coletas_colunas_base(df)
        linhas  = len(df)

        df_desc = df_base[df_base["rede_descarregador"].isin(["SP-RR-001", "ANJUN"])].copy()
        df_said = df_base[df_base["rede_carregador"] == "SP-RR-001"].copy()

        qtd_desc = _salvar_coletas(df_desc, arquivo, data_ref, "descarregamento") if not df_desc.empty else 0
        qtd_said = _salvar_coletas(df_said, arquivo, data_ref, "saida")           if not df_said.empty else 0

        partes = []
        if qtd_desc: partes.append(f"{qtd_desc:,} descarregamentos")
        if qtd_said: partes.append(f"{qtd_said:,} saídas")
        return {
            "registros": qtd_desc + qtd_said,
            "detalhe":   f"{linhas:,} lidas → {' + '.join(partes) or '0 registros'}",
        }

    elif ncols >= 13:
        arquivo.seek(0)
        return importar_coleta_final(arquivo, data_ref)

    elif ncols >= 10:
        arquivo.seek(0)
        return importar_coletas_grandes(arquivo, data_ref)

    else:
        raise ValueError(f"Formato de arquivo de coletas não reconhecido: {ncols} colunas (esperado ≥ 10)")


def _parse_linha_presenca(row, data_atual, nome_arquivo, data_importacao):
    """Extrai tuplas de presenca_turno e presenca_diaria de uma linha do DataFrame."""
    ts = pd.Timestamp(data_atual)
    semana = ts.strftime("w%V")
    ano    = int(ts.year)
    turno  = str(row.iloc[1]).strip() if len(row) > 1 and pd.notna(row.iloc[1]) else ""

    if turno not in ("T1", "T2", "T3"):
        return None, None

    def _i(idx): return _safe_int(row.iloc[idx] if len(row) > idx else None)
    def _f(idx): return _safe_float(row.iloc[idx] if len(row) > idx else None)

    row_turno = (
        data_atual, semana, ano, turno,
        _i(2), _i(6), _i(12), _i(3), _i(4), _i(5),
        _i(7), _i(8), _f(9), _f(10), _f(11),
        nome_arquivo, data_importacao,
    )
    row_diario = (
        data_atual, semana, ano,
        _i(13), _i(14), _i(15), _i(16), _i(17),
        nome_arquivo, data_importacao,
    ) if turno == "T3" else None

    return row_turno, row_diario


def _persistir_presenca(rows_turno, rows_diario, nome_arquivo):
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


# ================================
# 👥 PRESENÇA / DIÁRIO DE BORDO
# ================================
def importar_presenca(arquivo):
    df_raw = xlsx_para_dataframe(arquivo, header=None)
    if df_raw.empty:
        return 0

    nome_arquivo    = arquivo.name
    data_importacao = datetime.now(timezone.utc)
    rows_turno      = []
    rows_diario     = []
    data_atual      = None

    for _, row in df_raw.iterrows():
        val_data = row.iloc[0] if len(row) > 0 else None
        if pd.notna(val_data) and val_data != "":
            try:
                data_atual = pd.to_datetime(val_data).date()
            except Exception as e:
                print(f"⚠️ Linha ignorada (data inválida): {e}")
                continue

        if data_atual is None:
            continue

        rt, rd = _parse_linha_presenca(row, data_atual, nome_arquivo, data_importacao)
        if rt:
            rows_turno.append(rt)
        if rd:
            rows_diario.append(rd)

    if not rows_turno:
        return {"registros": 0, "detalhe": "Nenhuma linha de turno encontrada"}
    _persistir_presenca(rows_turno, rows_diario, nome_arquivo)
    return {"registros": len(rows_turno), "detalhe": f"{len(rows_turno):,} turnos | {len(rows_diario):,} registros diários"}
