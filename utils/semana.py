from datetime import datetime, timedelta, date
import html


def semana_para_datas(semana_str: str, ano: int):
    """
    Converte semana ISO (ex: 'w14') + ano para (data_inicio, data_fim).
    Semana ISO começa na segunda-feira e termina no domingo.

    Exemplo:
        semana_para_datas('w14', 2026) -> (date(2026,3,30), date(2026,4,5))
    """
    num = int(semana_str.lower().replace("w", ""))
    jan4 = datetime(ano, 1, 4)
    inicio_ano = jan4 - timedelta(days=jan4.weekday())
    inicio = (inicio_ano + timedelta(weeks=num - 1)).date()
    fim = inicio + timedelta(days=6)
    return inicio, fim


def datas_para_label(inicio, fim):
    """Retorna label legivel: '30/03 - 05/04/2026'"""
    if not isinstance(inicio, (date, datetime)) or not isinstance(fim, (date, datetime)):
        raise TypeError("inicio e fim devem ser objetos date ou datetime")
    return html.escape(f"{inicio.strftime('%d/%m')} \u2013 {fim.strftime('%d/%m/%Y')}")


def semana_atual_iso():
    """Retorna (semana_str, ano) da semana atual. Ex: ('w14', 2026)"""
    iso = datetime.now().isocalendar()
    return f"w{iso[1]:02d}", iso[0]
