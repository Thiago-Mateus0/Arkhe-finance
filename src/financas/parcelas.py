"""Parcelas futuras (ADR 0012): leitura sobre a fatura, sem alterar tipo nem totais.

Cada linha da fatura é uma parcela ("TÍTULO - Parcela 1/3", ou "Pix no Crédito - NOME - 1/3").
Projeta as que faltam depois da mais recente vista, só para meses depois do último importado.
"""
import re
import sqlite3
from collections import defaultdict
from datetime import date

from .service import HOUSEHOLD

MAX_PARCELAS = 60  # parcelamento de cartão não passa disso; o texto do CSV é não confiável
_PARCELA = re.compile(r"^(?P<titulo>.+?)\s-\s(?:Parcela\s+)?(?P<n>\d{1,3})/(?P<m>\d{1,3})\s*$", re.IGNORECASE)


def _mes_depois(d: date, k: int) -> str:
    i = d.year * 12 + d.month - 1 + k
    return f"{i // 12}-{i % 12 + 1:02d}"


def projetar(conn: sqlite3.Connection) -> dict:
    linhas = conn.execute(
        "SELECT date, description, amount_cents FROM transactions"
        " WHERE household_id=? AND account='nubank_fatura' AND kind='expense'", (HOUSEHOLD,)).fetchall()
    if not linhas:
        return {"meses": [], "total": 0.0}
    horizonte = max(r["date"] for r in linhas)[:7]

    grupos: dict[tuple, list] = defaultdict(list)
    for r in linhas:
        m = _PARCELA.match(" ".join(r["description"].split()))
        if not m or r["amount_cents"] >= 0:
            continue
        n, total = int(m["n"]), int(m["m"])
        if 1 <= n < total <= MAX_PARCELAS:
            grupos[(m["titulo"].upper(), total, r["amount_cents"])].append((n, r["date"], m["titulo"]))

    por_mes: dict[str, list] = defaultdict(list)
    for (_, total, cents), vistas in grupos.items():
        ultima = max(n for n, _, _ in vistas)
        recentes = [(d, t) for n, d, t in vistas if n == ultima]  # compras distintas na mesma parcela
        for d, titulo in recentes:
            for k in range(1, total - ultima + 1):
                mes = _mes_depois(date.fromisoformat(d), k)
                if mes > horizonte:
                    por_mes[mes].append({"titulo": titulo, "centavos": -cents, "parcela": f"{ultima + k}/{total}"})

    meses = [{"mes": mes, "total": sum(i["centavos"] for i in itens) / 100,
              "itens": [{"titulo": i["titulo"], "valor": i["centavos"] / 100, "parcela": i["parcela"]} for i in itens]}
             for mes, itens in sorted(por_mes.items())]
    return {"meses": meses, "total": sum(i["centavos"] for itens in por_mes.values() for i in itens) / 100}
