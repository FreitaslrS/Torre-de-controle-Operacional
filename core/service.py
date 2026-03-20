from core.repository import buscar_backlog_periodo, buscar_backlog_atual
import pandas as pd


def tratar_backlog_periodo(data_inicio, data_fim):
    df = buscar_backlog_periodo(data_inicio, data_fim)

    if df.empty:
        return df

    # 🔥 filtra backlog válido
    df = df[df["horas_backlog_snapshot"].notna()]

    # 🔥 deduplicação correta
    df = (
        df.sort_values("data_referencia")
          .drop_duplicates(subset=["waybill"], keep="last")
    )

    return df


def tratar_backlog_atual():
    return buscar_backlog_atual()


# =========================
# 📊 FLUXO BACKLOG
# =========================
def calcular_fluxo_backlog(data_inicio, data_fim):
    df = buscar_backlog_periodo(data_inicio, data_fim)

    if df.empty:
        return pd.DataFrame()

    df = df.sort_values(["waybill", "data_referencia"])

    historico = []

    anterior = set()

    for dia in sorted(df["data_referencia"].unique()):
        df_dia = df[df["data_referencia"] == dia]

        backlog_dia = set(
            df_dia[df_dia["horas_backlog_snapshot"].notna()]["waybill"]
        )

        entrou = backlog_dia - anterior
        saiu = anterior - backlog_dia

        historico.append({
            "data": dia,
            "entrou": len(entrou),
            "saiu": len(saiu)
        })

        anterior = backlog_dia

    return pd.DataFrame(historico)


# =========================
# 🎯 SLA
# =========================
def calcular_sla(data_inicio, data_fim):
    df = buscar_backlog_periodo(data_inicio, data_fim)

    if df.empty:
        return {"24h": 0, "48h": 0, "72h": 0}

    df = (
        df.sort_values("data_referencia")
          .drop_duplicates("waybill", keep="last")
    )

    total = len(df)

    return {
        "24h": len(df[df["horas_backlog_snapshot"] <= 24]) / total if total else 0,
        "48h": len(df[df["horas_backlog_snapshot"] <= 48]) / total if total else 0,
        "72h": len(df[df["horas_backlog_snapshot"] <= 72]) / total if total else 0,
    }