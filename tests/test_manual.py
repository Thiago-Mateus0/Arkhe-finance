from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from financas import api, db, service

CONTA = (Path(__file__).parent / "fixtures" / "nubank_conta_fake.csv").read_bytes()


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DEFAULT_PATH", tmp_path / "m.db")
    c = TestClient(api.app)
    c.post("/import", files={"file": ("x.csv", CONTA)})
    return c


def _pending(c):
    return c.get("/transactions", params={"month": "2026-09", "kind": "expense", "category": "Sem categoria"}).json()


def test_manual_category_is_locked_against_rules(client):
    tx = next(t for t in _pending(client) if t["counterparty"] == "MARIA SILVA")
    assert client.patch(f"/transactions/{tx['id']}", json={"category": "Família"}).json()["categoria"] == "Família"
    client.post("/rules", json={"pattern": "maria", "category": "Outros"})  # recategoriza tudo
    cats = {c["categoria"] for c in client.get("/reports/monthly", params={"month": "2026-09"}).json()["por_categoria"]}
    assert "Família" in cats and "Outros" not in cats


def test_remember_creates_rule_for_same_counterparty(client):
    zes = [t for t in _pending(client) if t["counterparty"] == "MERCADO DO ZE LTDA"]
    assert len(zes) == 3
    res = client.patch(f"/transactions/{zes[0]['id']}", json={"category": "Mercado", "remember": True}).json()
    assert res["regra_criada"] == "mercado do ze ltda"
    assert not [t for t in _pending(client) if t["counterparty"] == "MERCADO DO ZE LTDA"]
    assert "Mercado" in client.get("/categories").json()


def test_errors(client):
    assert client.patch("/transactions/9999", json={"category": "X"}).status_code == 404
    assert client.patch("/transactions/1", json={"category": "  "}).status_code == 422


def test_previous_month_comparison(tmp_path):
    c = db.connect(tmp_path / "p.db")
    service.import_csv(c, b"date,title,amount\n2026-08-10,Loja,\"50,00\"\n2026-09-10,Loja,\"80,00\"\n")
    rep = service.monthly_report(c, "2026-09")
    assert rep["gastos_mes_anterior"] == 50.0 and rep["por_categoria"][0]["mes_anterior"] == 50.0
    assert service._month_before("2026-01") == "2025-12"


def test_own_names_from_env_and_first_run_seed(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DEFAULT_PATH", tmp_path / "e.db")
    monkeypatch.setenv("FINANCAS_OWN_NAMES", "maria  silva; outra pessoa")
    with TestClient(api.app) as c:  # dispara o lifespan
        assert any(r["category"] == "Transporte" for r in c.get("/rules").json())
        c.post("/import", files={"file": ("x.csv", CONTA)})
        kinds = {t["counterparty"]: t["kind"] for t in c.get("/transactions", params={"month": "2026-09"}).json()}
        assert kinds["MARIA SILVA"] == "transfer"
