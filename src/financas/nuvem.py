"""Postgres hospedado (Supabase, ADR 0025): a mesma API de conexão do SQLite, para o importador.

Quem chama usa as mesmas funções de service.py (gravar_linhas, reclassify, import_csv...). Aqui só muda
o banco: placeholders `?` viram `%s` e a data volta como texto ISO, como no SQLite. A chave de acesso
(SUPABASE_DB_URL) e a casa (ARKHE_HOUSEHOLD_ID) ficam no .env local, nunca no git.
"""
from .pluggy import _ler_env


class ErroNuvem(Exception):
    pass


class PgConn:
    def __init__(self, url: str, household: str):
        import psycopg
        from psycopg.rows import dict_row
        from psycopg.types.string import TextLoader
        self._c = psycopg.connect(url, row_factory=dict_row)
        self._c.adapters.register_loader("date", TextLoader)  # ISO yyyy-mm-dd, igual ao SQLite
        self.household = household

    def execute(self, sql: str, params=()):
        return self._c.execute(sql.replace("?", "%s"), params)

    def executemany(self, sql: str, seq):
        cur = self._c.cursor()
        cur.executemany(sql.replace("?", "%s"), list(seq))
        return cur

    def commit(self) -> None:
        self._c.commit()

    def close(self) -> None:
        self._c.close()


def connect(env: dict | None = None) -> PgConn:
    env = env if env is not None else _ler_env()
    faltam = [k for k in ("SUPABASE_DB_URL", "ARKHE_HOUSEHOLD_ID") if not env.get(k)]
    if faltam:
        raise ErroNuvem(f"Faltam no .env ou no ambiente: {', '.join(faltam)}")
    try:
        import psycopg  # noqa: F401
    except ImportError:
        raise ErroNuvem('Falta o driver do Postgres: pip install -e ".[nuvem]"') from None
    return PgConn(env["SUPABASE_DB_URL"], env["ARKHE_HOUSEHOLD_ID"])


# ---------- migração do banco local (SQLite) para a nuvem (ADR 0025, etapa 5) ----------

_COLS_TX = ("account", "source_id", "date", "amount_cents", "description", "counterparty", "kind", "category",
            "category_locked", "dedupe_key", "source", "external_id", "operation_type")


def resumo(conn) -> dict:
    """Totais para conferir que local e nuvem dizem a mesma coisa: por conta e tipo (qtd e centavos)
    e por categoria nos gastos. Só números, nunca descrição."""
    casa = getattr(conn, "household", "default")
    por_tipo = {(r["account"], r["kind"]): (r["n"], r["c"]) for r in conn.execute(
        "SELECT account, kind, COUNT(*) AS n, COALESCE(SUM(amount_cents),0) AS c FROM transactions"
        " WHERE household_id=? GROUP BY account, kind", (casa,)).fetchall()}
    por_cat = {r["category"]: (r["n"], r["c"]) for r in conn.execute(
        "SELECT category, COUNT(*) AS n, COALESCE(SUM(amount_cents),0) AS c FROM transactions"
        " WHERE household_id=? AND kind='expense' GROUP BY category", (casa,)).fetchall()}
    travadas = conn.execute("SELECT COUNT(*) AS n FROM transactions WHERE household_id=? AND category_locked",
                            (casa,)).fetchone()["n"]
    return {"por_tipo": por_tipo, "por_categoria": por_cat, "travadas": travadas}


def migrar(lite, nuv: "PgConn", simular: bool = False) -> dict:
    """Copia lançamentos, regras, nomes próprios, orçamentos e a marca das regras padrão do SQLite
    local para a casa da nuvem. Não reclassifica: leva o tipo e a categoria exatamente como estão.
    Idempotente (rodar de novo não duplica). Com simular=True nada fica gravado."""
    antes = nuv.execute("SELECT COUNT(*) AS n FROM transactions WHERE household_id=?", (nuv.household,)).fetchone()["n"]
    try:
        tx = [dict(r) for r in lite.execute(f"SELECT {', '.join(_COLS_TX)} FROM transactions WHERE household_id='default'")]
        for t in tx:
            t["category_locked"] = bool(t["category_locked"])
        nuv.executemany(
            f"INSERT INTO transactions (household_id, {', '.join(_COLS_TX)})"
            f" VALUES ({', '.join(['?'] * (len(_COLS_TX) + 1))}) ON CONFLICT (household_id, dedupe_key) DO NOTHING",
            [(nuv.household, *(t[c] for c in _COLS_TX)) for t in tx])

        existentes = {(r["pattern"].lower(), r["category"]) for r in nuv.execute(
            "SELECT pattern, category FROM rules WHERE household_id=?", (nuv.household,)).fetchall()}
        regras = [r for r in lite.execute(
            "SELECT pattern, category, priority FROM rules WHERE household_id='default' ORDER BY id")
            if (r["pattern"].lower(), r["category"]) not in existentes]
        nuv.executemany("INSERT INTO rules (household_id, pattern, category, priority) VALUES (?,?,?,?)",
                        [(nuv.household, r["pattern"], r["category"], r["priority"]) for r in regras])

        nomes = [r["name"] for r in lite.execute("SELECT name FROM own_names WHERE household_id='default'")]
        nuv.executemany("INSERT INTO own_names (household_id, name) VALUES (?,?) ON CONFLICT DO NOTHING",
                        [(nuv.household, n) for n in nomes])
        orc = [(r["category"], r["limit_cents"]) for r in lite.execute(
            "SELECT category, limit_cents FROM budgets WHERE household_id='default'")]
        nuv.executemany("INSERT INTO budgets (household_id, category, limit_cents) VALUES (?,?,?)"
                        " ON CONFLICT (household_id, category) DO UPDATE SET limit_cents=excluded.limit_cents",
                        [(nuv.household, c, v) for c, v in orc])
        if lite.execute("SELECT 1 FROM meta WHERE key='default_rules_seeded'").fetchone():
            nuv.execute("INSERT INTO meta (household_id, key, value) VALUES (?, 'default_rules_seeded', '1')"
                        " ON CONFLICT DO NOTHING", (nuv.household,))
        depois = nuv.execute("SELECT COUNT(*) AS n FROM transactions WHERE household_id=?",
                             (nuv.household,)).fetchone()["n"]
        local, nuvem_ = resumo(lite), resumo(nuv)
        r = {"lancamentos_locais": len(tx), "lancamentos_novos": depois - antes, "regras_novas": len(regras),
             "nomes": len(nomes), "orcamentos": len(orc), "conferido": local == nuvem_,
             "simulacao": simular}
        if simular or not r["conferido"]:
            nuv._c.rollback()
        else:
            nuv.commit()
        return r
    except Exception:
        nuv._c.rollback()
        raise
