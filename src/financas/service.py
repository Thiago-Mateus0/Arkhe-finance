import sqlite3

from . import classifier, rules
from .classifier import EXPENSE
from .importer import detect_format, parse_nubank_conta, parse_nubank_fatura

HOUSEHOLD = "default"


def get_rules(conn: sqlite3.Connection) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM rules WHERE household_id=?", (HOUSEHOLD,))]


def get_own_names(conn: sqlite3.Connection) -> set[str]:
    return {r["name"] for r in conn.execute("SELECT name FROM own_names WHERE household_id=?", (HOUSEHOLD,))}


def import_csv(conn: sqlite3.Connection, content: str | bytes) -> dict:
    text = content.decode("utf-8-sig") if isinstance(content, bytes) else content
    fmt = detect_format(text)
    parsed = parse_nubank_conta(text) if fmt == "nubank_conta" else parse_nubank_fatura(text)
    rs = get_rules(conn)
    inserted = 0
    for p in parsed:
        kind = (classifier.classify_fatura(p.description, p.amount_cents) if fmt == "nubank_fatura"
                else EXPENSE)  # reclassify() define o tipo final das linhas de conta
        cur = conn.execute(
            "INSERT OR IGNORE INTO transactions (household_id, account, source_id, date, amount_cents,"
            " description, counterparty, kind, category, dedupe_key) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (HOUSEHOLD, fmt, p.source_id, p.date, p.amount_cents, p.description, p.counterparty, kind,
             rules.pick_category(p.description, p.counterparty, rs), p.dedupe_key),
        )
        inserted += cur.rowcount
    conn.commit()
    reclassify(conn)
    return {"formato": fmt, "lidas": len(parsed), "novas": inserted, "duplicadas": len(parsed) - inserted}


def reclassify(conn: sqlite3.Connection) -> None:
    """Recalcula o tipo das linhas de conta (nomes próprios e passagem dependem do conjunto todo)."""
    own = get_own_names(conn)
    rows = [dict(r) for r in conn.execute(
        "SELECT id, date, source_id, amount_cents, description, counterparty FROM transactions"
        " WHERE household_id=? AND account='nubank_conta'", (HOUSEHOLD,))]
    for r in rows:
        r["kind"] = classifier.classify(r["description"], r["amount_cents"], r["counterparty"], own)
    classifier.mark_passthrough(rows)
    conn.executemany("UPDATE transactions SET kind=? WHERE id=?", [(r["kind"], r["id"]) for r in rows])
    conn.commit()


def recategorize(conn: sqlite3.Connection) -> int:
    rs = get_rules(conn)
    n = 0
    for t in conn.execute(
        "SELECT id, description, counterparty FROM transactions WHERE household_id=? AND category_locked=0",
        (HOUSEHOLD,),
    ).fetchall():
        conn.execute("UPDATE transactions SET category=? WHERE id=?",
                     (rules.pick_category(t["description"], t["counterparty"], rs), t["id"]))
        n += 1
    conn.commit()
    return n


def monthly_report(conn: sqlite3.Connection, month: str) -> dict:
    """month = 'YYYY-MM'. Gastos = só kind 'expense'."""
    params = (HOUSEHOLD, f"{month}-%")
    by_cat = conn.execute(
        "SELECT category, -SUM(amount_cents) AS cents, COUNT(*) AS n FROM transactions"
        " WHERE household_id=? AND date LIKE ? AND kind='expense' GROUP BY category ORDER BY cents DESC",
        params,
    ).fetchall()
    income = conn.execute(
        "SELECT COALESCE(SUM(amount_cents),0) FROM transactions"
        " WHERE household_id=? AND date LIKE ? AND kind='income'", params).fetchone()[0]
    total = sum(r["cents"] for r in by_cat)
    return {
        "mes": month,
        "gastos_total": total / 100,
        "receitas_total": income / 100,
        "por_categoria": [{"categoria": r["category"], "valor": r["cents"] / 100, "qtd": r["n"]} for r in by_cat],
    }
