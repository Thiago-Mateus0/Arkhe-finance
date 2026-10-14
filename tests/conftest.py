"""Postgres 16 descartável em Docker, com a migração do Supabase aplicada (ADR 0025).

Os testes que usam a fixture `pg` pulam sozinhos se não houver Docker com a imagem postgres:16.
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


def docker_ok() -> bool:
    if not shutil.which("docker"):
        return False
    return subprocess.run(["docker", "image", "inspect", "postgres:16"], capture_output=True).returncode == 0


def psql(nome: str, sql: str) -> str:
    r = subprocess.run(["docker", "exec", "-i", nome, "psql", "-U", "postgres", "-At", "-v", "ON_ERROR_STOP=1", "-q"],
                       input=sql, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip()


@pytest.fixture(scope="module")
def pg():
    """Devolve (nome do contêiner, URL de conexão)."""
    if not docker_ok():
        pytest.skip("precisa de Docker com a imagem postgres:16")
    nome = f"arkhe-pg-{uuid.uuid4().hex[:8]}"
    subprocess.run(["docker", "run", "-d", "--rm", "--name", nome, "-p", "127.0.0.1::5432",
                    "-e", "POSTGRES_PASSWORD=teste", "postgres:16"], check=True, capture_output=True)
    try:
        for _ in range(60):
            if subprocess.run(["docker", "exec", nome, "psql", "-h", "127.0.0.1", "-U", "postgres", "-c", "select 1"],
                              capture_output=True).returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError("Postgres não subiu")
        psql(nome, STUB.read_text())
        for m in MIGRACOES:
            psql(nome, m.read_text())
        porta = subprocess.run(["docker", "port", nome, "5432"], capture_output=True, text=True,
                               check=True).stdout.split(":")[-1].strip()
        yield nome, f"postgresql://postgres:teste@127.0.0.1:{porta}/postgres"
    finally:
        subprocess.run(["docker", "rm", "-f", nome], capture_output=True)
