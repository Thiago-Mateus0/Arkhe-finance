"""Assinaturas (P5): leitura da categoria "Assinaturas". O usuário diz o que é assinatura (por regra);
o app não adivinha, porque Uber, 99 e Pix para pessoas também se repetem. Não altera tipo nem totais."""
import calendar
import sqlite3
from datetime import date

from .service import HOUSEHOLD

CATEGORIA = "Assinaturas"
JANELA_MESES = 3  # "ativa": com cobrança no mês pedido ou nos 2 anteriores


def _mes_depois(ym: str, k: int) -> str:
    y, m = map(int, ym.split("-"))
    i = y * 12 + m - 1 + k
    return f"{i // 12}-{i % 12 + 1:02d}"


def _mais_um_mes(d: str) -> str:
    y, m, dia = map(int, d.split("-"))
    ym = _mes_depois(f"{y}-{m:02d}", 1)
    ny, nm = map(int, ym.split("-"))
    return date(ny, nm, min(dia, calendar.monthrange(ny, nm)[1])).isoformat()


def listar(conn: sqlite3.Connection, mes: str) -> dict:
    fim = _mes_depois(mes, 1) + "-01"  # exclusivo
    rows = conn.execute(
        "SELECT date, account, amount_cents, description, counterparty FROM transactions"
        " WHERE household_id=? AND kind='expense' AND category=? AND date < ? ORDER BY date",
        (HOUSEHOLD, CATEGORIA, fim)).fetchall()

    total_cents = -sum(r["amount_cents"] for r in rows if r["date"][:7] == mes)
    desde = _mes_depois(mes, -(JANELA_MESES - 1))

    por_nome: dict[str, list] = {}
    for r in rows:
        if r["amount_cents"] >= 0:  # estorno entra no total, não vira assinatura
            continue
        nome = " ".join((r["counterparty"] or r["description"]).split()).upper()
        por_nome.setdefault(nome, []).append(r)

    itens = []
    for nome, cobr in por_nome.items():
        ultima = max(cobr, key=lambda r: r["date"])
        if ultima["date"][:7] < desde:
            continue
        meses = len({r["date"][:7] for r in cobr})
        itens.append({
            "nome": nome,
            "ultima_data": ultima["date"],
            "ultimo_valor": -ultima["amount_cents"] / 100,
            "meses": meses,
            "proxima": _mais_um_mes(ultima["date"]) if meses >= 2 else None,
        })
    itens.sort(key=lambda i: (-i["ultimo_valor"], i["nome"]))
    return {"mes": mes, "total": total_cents / 100, "itens": itens}
