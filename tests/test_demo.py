"""Os dados de demonstração (portfólio) precisam sempre importar e exercitar os casos difíceis."""
import subprocess
import sys
from pathlib import Path

import pytest

from financas import db, service

RAIZ = Path(__file__).resolve().parent.parent
DEMO = RAIZ / "data" / "demo"


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setenv("FINANCAS_OWN_NAMES", "JOAO PEDRO ALMEIDA")
    c = db.connect(tmp_path / "demo.db")
    service.seed_default_rules_once(c)
    for f in sorted(DEMO.glob("*.csv")):
        service.import_csv(c, f.read_bytes())
    yield c
    c.close()


def test_gerador_e_deterministico(tmp_path):
    antes = {f.name: f.read_bytes() for f in DEMO.glob("*.csv")}
    subprocess.run([sys.executable, str(RAIZ / "scripts" / "gerar_demo.py")], check=True, capture_output=True)
    assert {f.name: f.read_bytes() for f in DEMO.glob("*.csv")} == antes


def test_demo_cobre_todos_os_tipos(conn):
    kinds = {r[0] for r in conn.execute("SELECT DISTINCT kind FROM transactions")}
    assert kinds == {"expense", "income", "transfer", "card_payment", "credit_funding", "passthrough"}


def test_demo_reimportar_nao_duplica(conn):
    for f in sorted(DEMO.glob("*.csv")):
        assert service.import_csv(conn, f.read_bytes())["novas"] == 0


def test_demo_tem_categorias_e_alguns_pendentes_para_mostrar(conn):
    rep = service.monthly_report(conn, "2026-09")
    nomes = {c["categoria"] for c in rep["por_categoria"]}
    assert {"Transporte", "Delivery", "Saúde", "Educação", "Assinaturas"} <= nomes
    assert "Sem categoria" in nomes  # Pix para pessoas: o fluxo manual aparece na demo
    assert rep["receitas_total"] > 0 and rep["gastos_mes_anterior"] > 0


def test_demo_nao_traz_dado_pessoal_real():
    texto = "".join(f.read_text(encoding="utf-8") for f in DEMO.glob("*.csv")).upper()
    assert "EXEMPLO" in texto and "11.111.111/0001-11" in texto
