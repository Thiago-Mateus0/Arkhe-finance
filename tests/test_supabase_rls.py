"""Etapa 1 do ADR 0025: isolamento por casa (RLS) num Postgres de verdade, em contêiner descartável.

Pula se não houver Docker com a imagem postgres:16. Dados 100% fictícios.
"""
import shutil
import subprocess
import time
import uuid
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
STUB = Path(__file__).parent / "supabase" / "stub_supabase.sql"
MIGRACOES = sorted((RAIZ / "supabase" / "migrations").glob("*.sql"))

A, B, C = (str(uuid.uuid4()) for _ in range(3))  # A e C na mesma casa; B em outra
CASA_AB, CASA_B = str(uuid.uuid4()), str(uuid.uuid4())


def _docker_ok() -> bool:
    if not shutil.which("docker"):
        return False
    r = subprocess.run(["docker", "image", "inspect", "postgres:16"], capture_output=True)
    return r.returncode == 0


pytestmark = pytest.mark.skipif(not _docker_ok(), reason="precisa de Docker com a imagem postgres:16")


class Banco:
    def __init__(self, nome: str):
        self.nome = nome

    def rodar(self, sql: str, usuario: str | None = None, papel: str = "authenticated") -> subprocess.CompletedProcess:
        prefixo = ""
        if papel:
            prefixo += f"set role {papel};"
        if usuario:
            prefixo += f"select set_config('request.jwt.claim.sub','{usuario}',false);"
        return subprocess.run(
            ["docker", "exec", "-i", self.nome, "psql", "-U", "postgres", "-At", "-v", "ON_ERROR_STOP=1", "-q"],
            input=prefixo + sql, capture_output=True, text=True,
        )

    def admin(self, sql: str) -> str:
        r = subprocess.run(
            ["docker", "exec", "-i", self.nome, "psql", "-U", "postgres", "-At", "-v", "ON_ERROR_STOP=1", "-q"],
            input=sql, capture_output=True, text=True,
        )
        assert r.returncode == 0, r.stderr
        return r.stdout.strip()

    def valor(self, sql: str, usuario: str | None = None, papel: str = "authenticated") -> str:
        r = self.rodar(sql, usuario, papel)
        assert r.returncode == 0, r.stderr
        # a linha do set_config também sai; o resultado da consulta é a última linha
        return r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""


@pytest.fixture(scope="module")
def db():
    nome = f"arkhe-rls-{uuid.uuid4().hex[:8]}"
    subprocess.run(["docker", "run", "-d", "--rm", "--name", nome, "-e", "POSTGRES_PASSWORD=teste", "postgres:16"],
                   check=True, capture_output=True)
    try:
        b = Banco(nome)
        for _ in range(60):
            r = subprocess.run(["docker", "exec", nome, "psql", "-h", "127.0.0.1", "-U", "postgres", "-c", "select 1"],
                               capture_output=True)
            if r.returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError("Postgres não subiu")
        b.admin(STUB.read_text())
        for m in MIGRACOES:
            b.admin(m.read_text())
        b.admin(f"""
            insert into auth.users (id) values ('{A}'), ('{B}'), ('{C}');
            insert into households (id, name) values ('{CASA_AB}', 'casa A'), ('{CASA_B}', 'casa B');
            insert into members (user_id, household_id) values ('{A}', '{CASA_AB}'), ('{C}', '{CASA_AB}'), ('{B}', '{CASA_B}');
            insert into transactions (household_id, account, source_id, date, amount_cents, description, kind, category, dedupe_key) values
              ('{CASA_AB}', 'conta', '1', '2026-01-05', -1500, 'MERCADO FICTICIO A', 'expense', 'Mercado', 'a1'),
              ('{CASA_AB}', 'conta', '2', '2026-01-06', -2500, 'PADARIA FICTICIA A', 'expense', 'Mercado', 'a2'),
              ('{CASA_B}',  'conta', '1', '2026-01-05', -9900, 'LOJA FICTICIA B', 'expense', 'Compras', 'b1');
            insert into rules (household_id, pattern, category) values ('{CASA_B}', 'loja', 'Compras');
            insert into budgets (household_id, category, limit_cents) values ('{CASA_B}', 'Compras', 50000);
            insert into own_names (household_id, name) values ('{CASA_B}', 'NOME FICTICIO B');
            insert into meta (household_id, key, value) values ('{CASA_B}', 'default_rules_seeded', '1');
        """)
        yield b
    finally:
        subprocess.run(["docker", "rm", "-f", nome], capture_output=True)


def test_toda_tabela_do_public_tem_rls_ligado(db):
    sem_rls = db.admin("select relname from pg_class c join pg_namespace n on n.oid = c.relnamespace "
                       "where n.nspname = 'public' and c.relkind = 'r' and not c.relrowsecurity")
    assert sem_rls == ""


def test_cada_pessoa_le_so_os_lancamentos_da_sua_casa(db):
    assert db.valor("select count(*) from transactions", A) == "2"
    assert db.valor("select count(*) from transactions", B) == "1"
    assert db.valor("select sum(amount_cents) from transactions", B) == "-9900"


def test_duas_pessoas_da_mesma_casa_veem_os_mesmos_lancamentos(db):
    assert db.valor("select count(*) from transactions", C) == "2"


def test_nao_le_regra_orcamento_nome_nem_casa_de_outra_pessoa(db):
    for tabela in ("rules", "budgets", "own_names"):
        assert db.valor(f"select count(*) from {tabela}", A) == "0", tabela
        assert db.valor(f"select count(*) from {tabela}", B) == "1", tabela
    assert db.valor("select count(*) from households", A) == "1"
    assert db.valor("select count(*) from members", A) == "1"


def test_muda_categoria_do_seu_lancamento_mas_nao_do_de_outra_casa(db):
    assert db.valor("with u as (update transactions set category = 'Lazer' where dedupe_key = 'a1' returning 1) "
                    "select count(*) from u", A) == "1"
    assert db.valor("with u as (update transactions set category = 'Hack' where dedupe_key = 'b1' returning 1) "
                    "select count(*) from u", A) == "0"
    assert db.admin("select category from transactions where dedupe_key = 'b1'") == "Compras"


def test_nao_cria_apaga_nem_muda_valor_de_lancamento(db):
    r = db.rodar("insert into transactions (account, source_id, date, amount_cents, description, kind, category, dedupe_key) "
                 "values ('c','9','2026-01-01',1,'x','income','x','z')", A)
    assert r.returncode != 0 and "permission denied" in r.stderr
    r = db.rodar("delete from transactions", A)
    assert r.returncode != 0 and "permission denied" in r.stderr
    r = db.rodar("update transactions set amount_cents = 0", A)
    assert r.returncode != 0 and "permission denied" in r.stderr


def test_nao_troca_a_casa_de_um_lancamento(db):
    r = db.rodar(f"update transactions set household_id = '{CASA_B}'", A)
    assert r.returncode != 0 and "permission denied" in r.stderr


def test_regra_nova_vai_para_a_propria_casa_e_nao_para_a_de_outra(db):
    db.valor("insert into rules (pattern, category) values ('padaria', 'Mercado') returning 1", A)
    assert db.admin(f"select count(*) from rules where household_id = '{CASA_AB}'") == "1"
    r = db.rodar(f"insert into rules (household_id, pattern, category) values ('{CASA_B}', 'x', 'y')", A)
    assert r.returncode != 0 and "row-level security" in r.stderr


def test_nao_apaga_nem_altera_regra_de_outra_casa(db):
    assert db.valor("with d as (delete from rules where pattern = 'loja' returning 1) select count(*) from d", A) == "0"
    assert db.valor("with u as (update rules set category = 'Hack' where pattern = 'loja' returning 1) "
                    "select count(*) from u", A) == "0"
    assert db.admin("select count(*) from rules where pattern = 'loja' and category = 'Compras'") == "1"


def test_nao_move_regra_para_a_casa_de_outra_pessoa(db):
    r = db.rodar(f"update rules set household_id = '{CASA_B}' where pattern = 'padaria'", A)
    assert r.returncode != 0 and "row-level security" in r.stderr


def test_sem_login_nao_ve_nada(db):
    assert db.valor("select count(*) from transactions", None) == "0"
    assert db.valor("select count(*) from rules", None) == "0"


def test_anon_nao_acessa_as_tabelas(db):
    r = db.rodar("select * from transactions", None, papel="anon")
    assert r.returncode != 0 and "permission denied" in r.stderr


def test_meta_e_so_da_chave_de_servico(db):
    r = db.rodar("select * from meta", B)
    assert r.returncode != 0 and "permission denied" in r.stderr
    assert db.valor("select count(*) from meta", None, papel="service_role") == "1"


def test_limite_de_orcamento_zero_ou_negativo_e_recusado(db):
    for v in ("0", "-5"):
        r = db.rodar(f"insert into budgets (category, limit_cents) values ('Lazer', {v})", A)
        assert r.returncode != 0
