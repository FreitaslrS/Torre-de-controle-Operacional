import pandas as pd
from datetime import datetime
from psycopg2.extras import execute_values
from core.database import (
    conectar_backlog,
    executar_backlog,
    consultar_backlog,
    conectar_operacional,
    executar_operacional,
    conectar_historico,
    executar_historico
)
from core.database import conectar_processamento

import os


# ================================
# 🧹 LIMPEZA AUTOMÁTICA — 90 DIAS
# ================================
def limpar_historico_antigo():
    from core.database import (
        executar_operacional,
        executar_processamento,
        executar_historico,
        executar_devolucoes
    )
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


COLUNAS_MAPEAMENTO = {
    "waybill": ["waybill", "awb", "pedido"],
    "cliente": ["cliente"],
    "estado": ["estado", "uf", "estado destino", "destino uf", "州"],
    "cidade": ["cidade", "city", "城市", "destino"],
    "pre_entrega": ["预派送网点", "ponto de pré-entrega", "pre entrega"],
    "proximo_ponto": ["下一站", "proximo ponto", "próximo ponto", "next hub"],
    "entrada_hub1": ["entrada no centro nível 01"],
    "saida_hub1": ["saída do centro nível 01"],
    "entrada_hub2": ["entrada no centro nível 02"],
    "saida_hub2": ["saída do centro nível 02"],
    "entrada_hub3": ["entrada no centro nível 03"],
    "saida_hub3": ["saída do centro nível 03"],
    "data_inbound_ponto": ["网点入库时间", "tempo de inbound"],
    "data_entrega": ["签收时间", "tempo de assinatura"]
}


def encontrar_coluna_mapeada(df, aliases):
    for col in df.columns:
        col_str = str(col)

        for alias in aliases:
            if alias.lower() in col_str.lower():
                return col
    return None


def classificar_faixa(h):
    if pd.isna(h):
        return None
    elif h <= 24:
        return "0-24h"
    elif h <= 48:
        return "24-48h"
    elif h <= 72:
        return "48-72h"
    else:
        return "72h+"

def ajustar_data_operacional(data_hora):
    if pd.isna(data_hora):
        return None
    
    if data_hora.hour < 5 or (data_hora.hour == 5 and data_hora.minute < 30):
        return (data_hora - pd.Timedelta(days=1)).date()
    else:
        return data_hora.date()

def limpar_base():
    executar_historico("""
        DELETE FROM pedidos
        WHERE data_referencia < CURRENT_DATE - INTERVAL '30 days'
    """)

def calcular_base_tempo(row):
    return row["entrada_hub1"]


def preparar_dados(arquivo, data_referencia):
    df = pd.read_excel(arquivo, engine="openpyxl")
    df.columns = df.columns.str.strip()

    dados = pd.DataFrame()

    for coluna_padrao, aliases in COLUNAS_MAPEAMENTO.items():
        col = encontrar_coluna_mapeada(df, aliases)
        dados[coluna_padrao] = df[col] if col else None

    for col in [
        "entrada_hub1","saida_hub1",
        "entrada_hub2","saida_hub2",
        "entrada_hub3","saida_hub3",
        "data_inbound_ponto",   # 🔥 NOVO
        "data_entrega"          # 🔥 NOVO
    ]:
        dados[col] = pd.to_datetime(dados[col], errors="coerce")

    dados["waybill"] = dados["waybill"].astype(str).str.strip()
    dados = dados[(dados["waybill"] != "") & (dados["waybill"].str.lower() != "nan")]

    agora = pd.to_datetime(data_referencia)

    # 🔥 BACKLOG REAL
    mask = (
        dados["entrada_hub1"].notna() &
        dados["entrada_hub2"].isna() &
        dados["entrada_hub3"].isna() &
        dados["saida_hub1"].isna() &
        dados["saida_hub2"].isna() &
        dados["saida_hub3"].isna() &
        dados["data_entrega"].isna()   # 🔥 NOVO
    )

    dados["status"] = "finalizado"
    dados.loc[mask, "status"] = "backlog"

    def classificar_status_avancado(row):

        if pd.notna(row["data_entrega"]):
            return "Entregue"

        if pd.notna(row["entrada_hub3"]):
            return "Hub 3"

        if pd.notna(row["entrada_hub2"]):
            return "Hub 2"

        if pd.notna(row["entrada_hub1"]):
            return "Hub 1"

        return "Sem entrada"

    dados["status_etapa"] = dados.apply(classificar_status_avancado, axis=1)

    # ⏱️ TEMPO
    dados["base_tempo"] = dados.apply(calcular_base_tempo, axis=1)

    # 🔥 CORREÇÃO
    dados = dados[dados["base_tempo"].notna()]

    dados["horas_backlog_snapshot"] = (
        (agora - dados["base_tempo"]).dt.total_seconds() / 3600
    )

    dados["faixa_backlog_snapshot"] = dados["horas_backlog_snapshot"].apply(classificar_faixa)

    dados["data_referencia"] = agora.date()
    dados["data_importacao"] = datetime.now()
    dados["nome_arquivo"] = arquivo.name

    # 🔥 tratar próximo ponto
    dados["proximo_ponto"] = dados["proximo_ponto"].fillna("Sem informação")

    return dados

def validar_backlog(df):

    erros = []

    # ❌ HUB 2 sem HUB 1
    erro_hub2 = df[
        df["entrada_hub2"].notna() &
        df["entrada_hub1"].isna()
    ]
    if not erro_hub2.empty:
        erros.append(f"HUB2 sem HUB1: {len(erro_hub2)}")

    # ❌ HUB 3 sem HUB 2
    erro_hub3 = df[
        df["entrada_hub3"].notna() &
        df["entrada_hub2"].isna()
    ]
    if not erro_hub3.empty:
        erros.append(f"HUB3 sem HUB2: {len(erro_hub3)}")

    # ❌ saída sem entrada
    erro_saida = df[
        df["saida_hub1"].notna() &
        df["entrada_hub1"].isna()
    ]
    if not erro_saida.empty:
        erros.append(f"Saída sem entrada: {len(erro_saida)}")

    # ❌ horas negativas
    erro_tempo = df[df["horas_backlog_snapshot"] < 0]
    if not erro_tempo.empty:
        erros.append(f"Tempo negativo: {len(erro_tempo)}")

    erro_backlog = df[
        (df["status"] == "backlog") &
        (
            df["entrada_hub2"].notna() |
            df["entrada_hub3"].notna()
        )
    ]

    if not erro_backlog.empty:
        erros.append(f"Backlog inválido (já avançou): {len(erro_backlog)}")

    return erros

def inserir_em_massa(df):
    conn = conectar_historico()
    cur = conn.cursor()

    colunas = [
        "waybill",
        "cliente",
        "estado",
        "cidade",
        "pre_entrega",
        "proximo_ponto",
        "entrada_hub1",
        "saida_hub1",
        "entrada_hub2",
        "saida_hub2",
        "entrada_hub3",
        "saida_hub3",
        "data_inbound_ponto",
        "data_entrega",
        "status_etapa",
        "nome_arquivo",
        "data_referencia",
        "data_importacao",
        "horas_backlog_snapshot",
        "faixa_backlog_snapshot",
        "status"
    ]

    df = df[colunas]

    def tratar_valor(v):
        if pd.isna(v):
            return None
        return v

    values = [
        tuple(tratar_valor(v) for v in row)
        for row in df.itertuples(index=False, name=None)
    ]

    execute_values(
        cur,
        f"INSERT INTO pedidos ({','.join(colunas)}) VALUES %s",
        values
    )

    conn.commit()
    cur.close()
    conn.close()


def importar_excel(arquivo, data_referencia):
    import pandas as pd
    from datetime import datetime
    from psycopg2.extras import execute_values
    from core.database import conectar_historico, conectar_backlog, consultar_backlog, executar_historico

    # Lê só colunas necessárias
    df = pd.read_excel(
        arquivo,
        usecols=[0, 11, 12, 21, 24, 25, 41, 42, 43, 48, 56],
        engine="openpyxl"
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
    df_backlog["data_importacao"]        = datetime.now()
    df_backlog["nome_arquivo"]           = arquivo.name
    df_backlog["proximo_ponto"]          = df_backlog["proximo_ponto"].fillna("Sem informação")

    # ── CAMADA 1: backlog_atual (snapshot atual por waybill) ──────────
    existentes     = consultar_backlog("SELECT waybill FROM backlog_atual")
    existentes_set = set(existentes["waybill"]) if not existentes.empty else set()
    novos_set      = set(df_backlog["waybill"])

    removidos = existentes_set - novos_set
    if removidos:
        conn = conectar_backlog()
        cur  = conn.cursor()
        cur.execute("DELETE FROM backlog_atual WHERE waybill = ANY(%s)", (list(removidos),))
        conn.commit(); cur.close(); conn.close()

    conn = conectar_backlog()
    cur  = conn.cursor()
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
    conn.commit(); cur.close(); conn.close()

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
    df_resumo["data_importacao"] = datetime.now()

    conn = conectar_historico()
    cur  = conn.cursor()
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
    executar_historico(
        "DELETE FROM pedidos WHERE data_referencia = %s", [agora.date()]
    )
    executar_historico(
        "DELETE FROM pedidos WHERE data_referencia < CURRENT_DATE - INTERVAL '7 days'"
    )

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

    conn.commit(); cur.close(); conn.close()

    limpar_historico_antigo()
    return len(df_backlog)


def importar_produtividade(arquivo):
    import pandas as pd
    from datetime import datetime
    from psycopg2.extras import execute_values
    from core.database import conectar_operacional, executar_operacional

    # Colunas: D=3 (cliente), I=8 (data_hora), U=20 (operador)
    df = pd.read_excel(arquivo, usecols=[3, 8, 20], engine="openpyxl")
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
    df_agg["data_importacao"] = datetime.now()

    conn = conectar_operacional()
    cur  = conn.cursor()
    cur.execute("DELETE FROM produtividade WHERE nome_arquivo = %s", [arquivo.name])

    colunas = ["cliente", "data", "hora", "turno", "dispositivo", "volumes", "nome_arquivo", "data_importacao"]
    values  = [tuple(None if pd.isna(v) else v for v in row)
               for row in df_agg[colunas].itertuples(index=False, name=None)]

    execute_values(cur, f"INSERT INTO produtividade ({','.join(colunas)}) VALUES %s", values)
    conn.commit()
    cur.close()
    conn.close()

    # View materializada substituída por query direta em buscar_produtividade()
    # Não é mais necessário fazer REFRESH

    limpar_historico_antigo()
    return len(df_agg)


def importar_tempo_processamento(arquivo):
    import pandas as pd
    from datetime import datetime
    from psycopg2.extras import execute_values
    from core.database import conectar_processamento

    # Lê só colunas necessárias
    df = pd.read_excel(
        arquivo,
        usecols=[0, 11, 21, 24, 25, 41, 42, 43],
        engine="openpyxl"
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

    agg["data_snapshot"]   = datetime.now().date()
    agg["nome_arquivo"]    = arquivo.name
    agg["data_importacao"] = datetime.now()

    conn = conectar_processamento()
    cur  = conn.cursor()
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
    conn.close()

    limpar_historico_antigo()
    return len(agg)


# ================================
# 📊 DEVOLUÇÃO — P90
# ================================
def importar_p90(arquivo, data_ref):
    import pandas as pd
    import numpy as np
    from datetime import datetime
    from psycopg2.extras import execute_values
    from core.database import conectar_devolucoes

    df = pd.read_excel(arquivo, engine="openpyxl")

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
        except:
            return None

    df["data_criacao"] = df["waybill"].apply(extrair_data_criacao)
    df = df[df["data_criacao"].notna()]

    # Dias corridos: criação → recebimento devolução
    df["dias"] = (df["data_operacao"] - df["data_criacao"]).dt.days
    df = df[df["dias"] >= 0]

    if df.empty:
        return 0

    # Semana e ano de criação do pedido
    df["semana"] = df["data_criacao"].dt.strftime("w%V")
    df["ano"]    = df["data_criacao"].dt.year

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
    agg["data_importacao"] = datetime.now()

    conn = conectar_devolucoes()
    cur  = conn.cursor()
    cur.execute("DELETE FROM p90_semanal WHERE nome_arquivo = %s", [arquivo.name])

    colunas = [
        "estado", "semana", "ano", "cliente", "p90_dias",
        "qtd_pedidos", "data_referencia", "nome_arquivo", "data_importacao"
    ]
    values = [
        tuple(None if pd.isna(v) else v for v in row)
        for row in agg[colunas].itertuples(index=False, name=None)
    ]

    execute_values(
        cur,
        f"INSERT INTO p90_semanal ({','.join(colunas)}) VALUES %s",
        values
    )

    conn.commit()
    cur.close()
    conn.close()

    limpar_historico_antigo()
    return len(agg)


# ================================
# 🔁 DEVOLUÇÃO (arquivo Folha_de_registro)
# ================================
def importar_devolucoes(arquivo, data_ref):
    import pandas as pd
    from datetime import datetime
    from psycopg2.extras import execute_values
    from core.database import conectar_devolucoes

    df = pd.read_excel(arquivo, engine="openpyxl")

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

    conn = conectar_devolucoes()
    cur  = conn.cursor()

    for tabela in ["dev_status_semanal", "dev_iatas_semanal"]:
        cur.execute(f"DELETE FROM {tabela} WHERE nome_arquivo = %s", [arquivo.name])

    agora = datetime.now()

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

    colunas_status = [
        "estado", "status", "semana", "ano", "data_referencia", "cliente",
        "cliente_fantasia", "qtd", "nome_arquivo", "data_importacao"
    ]
    execute_values(cur,
        f"INSERT INTO dev_status_semanal ({','.join(colunas_status)}) VALUES %s",
        [tuple(None if pd.isna(v) else v for v in row)
         for row in status_agg[colunas_status].itertuples(index=False, name=None)]
    )

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

    colunas_iata = [
        "ponto_operacao", "estado", "semana", "ano", "data_referencia",
        "cliente_fantasia", "qtd", "nome_arquivo", "data_importacao"
    ]
    execute_values(cur,
        f"INSERT INTO dev_iatas_semanal ({','.join(colunas_iata)}) VALUES %s",
        [tuple(None if pd.isna(v) else v for v in row)
         for row in iata_agg[colunas_iata].itertuples(index=False, name=None)]
    )

    conn.commit()
    cur.close()
    conn.close()

    limpar_historico_antigo()
    return len(status_agg) + len(iata_agg)


# ================================
# 📊 DEVOLUÇÃO - MONITORAMENTO (arquivo monitoramento_da_pontualidade)
# ================================
def importar_devolucao_monitoramento(arquivo, data_ref):
    import pandas as pd
    from datetime import datetime
    from psycopg2.extras import execute_values
    from core.database import conectar_devolucoes

    df = pd.read_excel(
        arquivo,
        usecols=[0, 4, 8, 11, 21, 22, 25, 33, 66, 67, 68, 71, 73],
        engine="openpyxl"
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

    conn = conectar_devolucoes()
    cur  = conn.cursor()

    for tabela in ["dev_sla_semanal", "dev_motivos_semanal", "dev_dsp_sem3tent"]:
        cur.execute(f"DELETE FROM {tabela} WHERE nome_arquivo = %s", [arquivo.name])

    agora       = datetime.now()
    sla_agg     = pd.DataFrame()
    motivos_agg = pd.DataFrame()
    dsp_agg     = pd.DataFrame()

    # ── SLA ───────────────────────────────────────────────────────────
    df_entregues = df[df["assinatura"].notna()].copy()
    if not df_entregues.empty:
        df_entregues["dias"] = (
            (df_entregues["assinatura"] - df_entregues["data_criacao"])
            .dt.total_seconds() / 86400
        )
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

        colunas_sla = ["estado", "data_referencia", "cliente", "cliente_fantasia", "qtd_total", "qtd_no_prazo", "nome_arquivo", "data_importacao"]
        execute_values(cur,
            f"INSERT INTO dev_sla_semanal ({','.join(colunas_sla)}) VALUES %s",
            [tuple(None if pd.isna(v) else v for v in row)
             for row in sla_agg[colunas_sla].itertuples(index=False, name=None)]
        )

    # ── Motivos ───────────────────────────────────────────────────────
    df_motivos = df[df["motivo"].notna()].copy()
    if not df_motivos.empty:
        motivos_agg = (
            df_motivos.groupby(["estado", "motivo", "cliente", "cliente_fantasia"])
            .size()
            .reset_index(name="qtd")
        )
        motivos_agg["data_referencia"] = data_ref
        motivos_agg["nome_arquivo"]    = arquivo.name
        motivos_agg["data_importacao"] = agora

        colunas_mot = ["estado", "motivo", "cliente", "cliente_fantasia", "data_referencia", "qtd", "nome_arquivo", "data_importacao"]
        execute_values(cur,
            f"INSERT INTO dev_motivos_semanal ({','.join(colunas_mot)}) VALUES %s",
            [tuple(None if pd.isna(v) else v for v in row)
             for row in motivos_agg[colunas_mot].itertuples(index=False, name=None)]
        )

    # ── DSPs sem 3 tentativas ─────────────────────────────────────────
    dsp_sem3 = df[
        df["motivo"].notna() &
        df["tent1"].notna() &
        df["tent3"].isna() &
        df["assinatura"].isna()
    ].copy()

    if not dsp_sem3.empty:
        dsp_agg = (
            dsp_sem3.groupby(["ponto_entrada", "estado", "motivo", "cliente", "cliente_fantasia"])
            .size()
            .reset_index(name="qtd")
        )
        dsp_agg["data_referencia"] = data_ref
        dsp_agg["nome_arquivo"]    = arquivo.name
        dsp_agg["data_importacao"] = agora

        colunas_dsp = ["ponto_entrada", "estado", "motivo", "cliente", "cliente_fantasia", "data_referencia", "qtd", "nome_arquivo", "data_importacao"]
        execute_values(cur,
            f"INSERT INTO dev_dsp_sem3tent ({','.join(colunas_dsp)}) VALUES %s",
            [tuple(None if pd.isna(v) else v for v in row)
             for row in dsp_agg[colunas_dsp].itertuples(index=False, name=None)]
        )

    conn.commit()
    cur.close()
    conn.close()

    limpar_historico_antigo()
    return len(sla_agg) + len(motivos_agg) + len(dsp_agg)


# ================================
# 📦 PACOTES GRANDES (AJG)
# ================================
def importar_pacotes_grandes(arquivo):
    import pandas as pd
    from datetime import datetime
    from psycopg2.extras import execute_values
    from core.database import conectar_operacional

    df = pd.read_excel(arquivo, engine="openpyxl")

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
    df["semana"]       = df["data_criacao"].dt.strftime("w%V")
    df["ano"]          = df["data_criacao"].dt.year
    df["nome_arquivo"]    = arquivo.name
    df["data_importacao"] = datetime.now()

    conn = conectar_operacional()
    cur  = conn.cursor()
    cur.execute("DELETE FROM pacotes_grandes WHERE nome_arquivo = %s", [arquivo.name])

    colunas = [
        "waybill_mae", "waybill", "cliente", "status", "data_status",
        "estado", "cidade", "pre_entrega", "produto", "peso_kg", "volume_m3",
        "semana", "ano", "nome_arquivo", "data_importacao"
    ]

    values = [
        tuple(None if pd.isna(v) else v for v in row)
        for row in df[colunas].itertuples(index=False, name=None)
    ]

    execute_values(
        cur,
        f"INSERT INTO pacotes_grandes ({','.join(colunas)}) VALUES %s",
        values
    )

    conn.commit()
    cur.close()
    conn.close()

    return len(df)