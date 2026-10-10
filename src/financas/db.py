"""SQLite local. Todo acesso passa por aqui, para trocar por Postgres depois sem mexer na API."""
import os
import sqlite3
from pathlib import Path

DEFAULT_PATH = Path(os.environ.get("FINANCAS_DB", "financas.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY,
    household_id TEXT NOT NULL DEFAULT 'default',
    account TEXT NOT NULL,
    source_id TEXT NOT NULL,
    date TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    description TEXT NOT NULL,
    counterparty TEXT NOT NULL DEFAULT '',
    kind TEXT NOT NULL,
    category TEXT NOT NULL,
    category_locked INTEGER NOT NULL DEFAULT 0,
    dedupe_key TEXT NOT NULL,
    UNIQUE (household_id, dedupe_key)
);
CREATE INDEX IF NOT EXISTS idx_tx_date ON transactions (household_id, date);
CREATE TABLE IF NOT EXISTS rules (
    id INTEGER PRIMARY KEY,
    household_id TEXT NOT NULL DEFAULT 'default',
    pattern TEXT NOT NULL,
    category TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS budgets (
    household_id TEXT NOT NULL DEFAULT 'default',
    category TEXT NOT NULL,
    limit_cents INTEGER NOT NULL CHECK (limit_cents > 0),
    PRIMARY KEY (household_id, category)
);
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS own_names (
    household_id TEXT NOT NULL DEFAULT 'default',
    name TEXT NOT NULL,
    PRIMARY KEY (household_id, name)
);
"""


def connect(path: str | Path | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path or DEFAULT_PATH), check_same_thread=False)  # 1 conexão por requisição
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn
