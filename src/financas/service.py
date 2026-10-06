import sqlite3

from . import classifier, rules
from .importer import ParsedRow, parse_nubank_conta

HOUSEHOLD = "default"


def get_rules(conn: sqlite3.Connection) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM rules WHERE household_id=?", (HOUSEHOLD,))]


def get_own_names(conn: sqlite3.Connection) -> set[str]:
    return {r["name"] for r in conn.execute("SELECT name FROM own_names WHERE household_id=?", (HOUSEHOLD,))}


def import_nubank_conta(conn: sqlite3.Connection, content: str | bytes) -> dict:
    parsed: list[ParsedRow] = parse_nubank_conta(content)
    own = get_own_names(conn)
    rs = get_rules(conn)
    rows = [
        {
            "date": p.date, "amount_cents": p.amount_cents, "source_id": p.source_id,
            "description": p.description, "counterparty": p.counterparty, "dedupe_key": p.dedupe_key,
            "kind": classifier.classify(p.description, p.amount_cents, p.counterparty, own),
        }
        for p in parsed
    ]
    classifier.mark_passthrough(rows)
    inserted = 0
    for r in rows:
        cur = conn.execute(
            "INSERT OR IGNORE INTO transactions (household_id, account, source_id, date, amount_cents,"
            " description, counterparty, kind, category, dedupe_key) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (HOUSEHOLD, "nubank_conta", r["source_id"], r["date"], r["amount_cents"], r["description"],
             r["counterparty"], r["kind"], rules.pick_category(r["description"], r["counterparty"], rs),
             r["dedupe_key"]),
        )
        inserted += cur.rowcount
    conn.commit()
    return {"lidas": len(rows), "novas": inserted, "duplicadas": len(rows) - inserted}


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
