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
