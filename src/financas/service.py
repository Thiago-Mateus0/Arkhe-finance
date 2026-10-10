import json
import os
import sqlite3
from datetime import date
from pathlib import Path

from . import classifier, rules
from .classifier import EXPENSE
from .importer import detect_format, parse_nubank_conta, parse_nubank_fatura

HOUSEHOLD = "default"


def get_rules(conn: sqlite3.Connection) -> list[dict]:
    return [dict(r) for r in conn.execute("SELECT * FROM rules WHERE household_id=?", (HOUSEHOLD,))]


def get_own_names(conn: sqlite3.Connection) -> set[str]:
    """Nomes do banco + FINANCAS_OWN_NAMES (separados por ';'), tudo em maiúsculas."""
    from_db = {r["name"] for r in conn.execute("SELECT name FROM own_names WHERE household_id=?", (HOUSEHOLD,))}
    from_env = {" ".join(n.split()).upper() for n in os.environ.get("FINANCAS_OWN_NAMES", "").split(";") if n.strip()}
    return from_db | from_env


def import_csv(conn: sqlite3.Connection, content: str | bytes) -> dict:
    text = content.decode("utf-8-sig") if isinstance(content, bytes) else content
    fmt = detect_format(text)
    parsed = parse_nubank_conta(text) if fmt == "nubank_conta" else parse_nubank_fatura(text)
    rs = get_rules(conn)
    own = get_own_names(conn)
    inserted = 0
    for p in parsed:
        kind = (classifier.classify_fatura(p.description, p.amount_cents, own) if fmt == "nubank_fatura"
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
    """Recalcula o tipo das linhas de conta e de fatura. Nome próprio, repasse e Pix no crédito
    dependem do conjunto todo (conta e fatura juntas), por isso rodam sempre sobre tudo."""
    own = get_own_names(conn)
    rows = [dict(r) for r in conn.execute(
        "SELECT id, date, source_id, amount_cents, description, counterparty FROM transactions"
        " WHERE household_id=? AND account='nubank_conta'", (HOUSEHOLD,))]
    for r in rows:
        r["kind"] = classifier.classify(r["description"], r["amount_cents"], r["counterparty"], own)
    faturas = [dict(r) for r in conn.execute(
        "SELECT id, date, description, amount_cents FROM transactions WHERE household_id=? AND account='nubank_fatura'",
        (HOUSEHOLD,))]
    for r in faturas:
        r["kind"] = classifier.classify_fatura(r["description"], r["amount_cents"], own)
    classifier.pair_pix_no_credito(rows, faturas)
    classifier.mark_passthrough(rows)
    conn.executemany("UPDATE transactions SET kind=? WHERE id=?", [(r["kind"], r["id"]) for r in rows + faturas])
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


def _month_before(month: str) -> str:
    y, m = map(int, month.split("-"))
    return f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02d}"


def _spending_by_category(conn: sqlite3.Connection, month: str) -> list[sqlite3.Row]:
    return conn.execute(
        "SELECT category, -SUM(amount_cents) AS cents, COUNT(*) AS n FROM transactions"
        " WHERE household_id=? AND date LIKE ? AND kind='expense' GROUP BY category ORDER BY cents DESC",
        (HOUSEHOLD, f"{month}-%"),
    ).fetchall()


def _spending_by_account(conn: sqlite3.Connection, month: str) -> dict[str, int]:
    rows = conn.execute(
        "SELECT account, -SUM(amount_cents) AS cents FROM transactions"
        " WHERE household_id=? AND date LIKE ? AND kind='expense' GROUP BY account",
        (HOUSEHOLD, f"{month}-%")).fetchall()
    return {r["account"]: r["cents"] for r in rows}


def monthly_report(conn: sqlite3.Connection, month: str) -> dict:
    """month = 'YYYY-MM'. Gastos = só kind 'expense'. Inclui o valor do mês anterior por categoria."""
    by_cat = _spending_by_category(conn, month)
    prev = {r["category"]: r["cents"] for r in _spending_by_category(conn, _month_before(month))}
    income = conn.execute(
        "SELECT COALESCE(SUM(amount_cents),0) FROM transactions"
        " WHERE household_id=? AND date LIKE ? AND kind='income'", (HOUSEHOLD, f"{month}-%")).fetchone()[0]
    return {
        "mes": month,
        "gastos_total": sum(r["cents"] for r in by_cat) / 100,
        "gastos_mes_anterior": sum(prev.values()) / 100,
        "gastos_cartao": _spending_by_account(conn, month).get("nubank_fatura", 0) / 100,
        "gastos_conta": _spending_by_account(conn, month).get("nubank_conta", 0) / 100,
        "receitas_total": income / 100,
        "por_categoria": [
            {"categoria": r["category"], "valor": r["cents"] / 100, "qtd": r["n"],
             "mes_anterior": prev.get(r["category"], 0) / 100}
            for r in by_cat
        ],
    }


def set_category(conn: sqlite3.Connection, tx_id: int, category: str, remember: bool = False) -> dict | None:
    """Categoria manual: fica travada (regras não sobrescrevem). 'remember' cria uma regra
    pela contraparte (ou descrição) e a aplica às demais transações não travadas."""
    t = conn.execute("SELECT description, counterparty FROM transactions WHERE id=? AND household_id=?",
                     (tx_id, HOUSEHOLD)).fetchone()
    if t is None:
        return None
    conn.execute("UPDATE transactions SET category=?, category_locked=1 WHERE id=?", (category, tx_id))
    rule_pattern = None
    if remember:
        rule_pattern = (t["counterparty"] or t["description"]).lower()
        conn.execute("INSERT INTO rules (household_id, pattern, category, priority) VALUES (?,?,?,5)",
                     (HOUSEHOLD, rule_pattern, category))
    conn.commit()
    return {"categoria": category, "regra_criada": rule_pattern,
            "recategorizadas": recategorize(conn) if remember else 0}


def list_categories(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT category FROM rules WHERE household_id=? UNION SELECT category FROM transactions"
        " WHERE household_id=?", (HOUSEHOLD, HOUSEHOLD)).fetchall()
    return sorted({r[0] for r in rows} - {rules.UNCATEGORIZED})


def seed_default_rules(conn: sqlite3.Connection) -> dict:
    """Carrega as regras padrão; ignora as que já existem (mesmo padrão e categoria)."""
    defaults = json.loads((Path(__file__).parent / "default_rules.json").read_text(encoding="utf-8"))
    existing = {(r["pattern"].lower(), r["category"]) for r in get_rules(conn)}
    added = 0
    for r in defaults:
        if (r["pattern"].lower(), r["category"]) in existing:
            continue
        conn.execute("INSERT INTO rules (household_id, pattern, category, priority) VALUES (?,?,?,?)",
                     (HOUSEHOLD, r["pattern"], r["category"], r["priority"]))
        added += 1
    conn.commit()
    return {"adicionadas": added, "recategorizadas": recategorize(conn)}


def delete_rule(conn: sqlite3.Connection, rule_id: int) -> bool:
    cur = conn.execute("DELETE FROM rules WHERE id=? AND household_id=?", (rule_id, HOUSEHOLD))
    conn.commit()
    if cur.rowcount:
        recategorize(conn)
    return bool(cur.rowcount)


def _days_in_month(month: str) -> int:
    y, m = map(int, month.split("-"))
    nxt = date(y + (m == 12), 1 if m == 12 else m + 1, 1)
    return (nxt - date(y, m, 1)).days


def daily_report(conn: sqlite3.Connection, month: str) -> dict:
    """Gastos e entradas por dia do mês, mais os gastos diários do mês anterior (para comparar)."""
    def per_day(m: str, kind: str) -> dict[int, int]:
        rows = conn.execute(
            "SELECT CAST(substr(date, 9, 2) AS INTEGER) AS d, SUM(ABS(amount_cents)) AS c FROM transactions"
            " WHERE household_id=? AND date LIKE ? AND kind=? GROUP BY d", (HOUSEHOLD, f"{m}-%", kind)).fetchall()
        return {r["d"]: r["c"] for r in rows}

    spend, income = per_day(month, "expense"), per_day(month, "income")
    prev_spend = per_day(_month_before(month), "expense")
    n = _days_in_month(month)
    return {
        "mes": month,
        "dias": [{"dia": d, "gastos": spend.get(d, 0) / 100, "entradas": income.get(d, 0) / 100}
                 for d in range(1, n + 1)],
        "anterior": [{"dia": d, "gastos": prev_spend.get(d, 0) / 100}
                     for d in range(1, _days_in_month(_month_before(month)) + 1)],
    }


def seed_default_rules_once(conn: sqlite3.Connection) -> bool:
    """Carrega as regras padrão na primeira vez que o banco é usado; depois respeita o que você apagou."""
    if conn.execute("SELECT 1 FROM meta WHERE key='default_rules_seeded'").fetchone():
        return False
    seed_default_rules(conn)
    conn.execute("INSERT INTO meta (key, value) VALUES ('default_rules_seeded', '1')")
    conn.commit()
    return True


# ---------- orçamento (spec: docs/spec/orcamento.md, ADR 0015) ----------

BUDGET_ESTADOS = ("estourou", "atencao", "ok")  # do mais grave ao mais folgado


def _budget_estado(spent_cents: int, limit_cents: int) -> str:
    """Tudo em centavos inteiros, sem arredondar: 80% do limite é spent*5 >= limit*4."""
    if spent_cents > limit_cents:
        return "estourou"
    if spent_cents * 5 >= limit_cents * 4:
        return "atencao"
    return "ok"


def set_budget(conn: sqlite3.Connection, category: str, limit_cents: int) -> None:
    category = category.strip()
    if not category or len(category) > 60:
        raise ValueError("Categoria inválida (vazia ou com mais de 60 caracteres)")
    if category == rules.UNCATEGORIZED:
        raise ValueError("Não dá para orçar 'Sem categoria': classifique os lançamentos antes")
    if limit_cents <= 0:
        raise ValueError("O limite precisa ser maior que zero")
    conn.execute(
        "INSERT INTO budgets (household_id, category, limit_cents) VALUES (?,?,?)"
        " ON CONFLICT (household_id, category) DO UPDATE SET limit_cents=excluded.limit_cents",
        (HOUSEHOLD, category, limit_cents))
    conn.commit()


def delete_budget(conn: sqlite3.Connection, category: str) -> bool:
    cur = conn.execute("DELETE FROM budgets WHERE household_id=? AND category=?", (HOUSEHOLD, category.strip()))
    conn.commit()
    return bool(cur.rowcount)


def budget_status(conn: sqlite3.Connection, month: str) -> dict:
    spent = {r["category"]: r["cents"] for r in _spending_by_category(conn, month)}
    itens = []
    for b in conn.execute("SELECT category, limit_cents FROM budgets WHERE household_id=?", (HOUSEHOLD,)):
        gasto, limite = spent.get(b["category"], 0), b["limit_cents"]
        itens.append({
            "categoria": b["category"], "limite": limite / 100, "gasto": gasto / 100,
            "restante": (limite - gasto) / 100, "percentual": round(gasto * 100 / limite, 1),
            "estado": _budget_estado(gasto, limite), "_ord": (BUDGET_ESTADOS.index(_budget_estado(gasto, limite)), -gasto / limite),
        })
    itens.sort(key=lambda i: i["_ord"])
    for i in itens:
        del i["_ord"]
    return {
        "mes": month,
        "orcado_total": sum(round(i["limite"] * 100) for i in itens) / 100,
        "gasto_nas_categorias": sum(round(i["gasto"] * 100) for i in itens) / 100,
        "itens": itens,
    }


def months_with_data(conn: sqlite3.Connection) -> list[str]:
    """Meses (aaaa-mm) que têm algum lançamento, do mais recente para o mais antigo."""
    rows = conn.execute("SELECT DISTINCT substr(date, 1, 7) AS m FROM transactions WHERE household_id=? ORDER BY m DESC",
                        (HOUSEHOLD,)).fetchall()
    return [r["m"] for r in rows]
