from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from financas import api, db

FIXTURE = Path(__file__).parent / "fixtures" / "nubank_conta_fake.csv"


@pytest.fixture
def c(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DEFAULT_PATH", tmp_path / "regras.db")
    with TestClient(api.app) as client:
        yield client


def _cat_de(c, trecho):
    txs = c.get("/transactions", params={"month": "2026-09", "kinds": "expense,income"}).json()
    return {t["category"] for t in txs if trecho.lower() in (t["description"] + t["counterparty"]).lower()}


def _regra(c, pattern):
    return next(r for r in c.get("/rules").json() if r["pattern"] == pattern)


def test_editar_regra_recategoriza(c):
    c.post("/import", files={"file": ("x.csv", FIXTURE.read_bytes())})
    c.post("/rules", json={"pattern": "mercado", "category": "Mercado"})
    assert _cat_de(c, "mercado") == {"Mercado"}
    rid = _regra(c, "mercado")["id"]
    r = c.put(f"/rules/{rid}", json={"pattern": "mercado", "category": "Casa", "priority": 3})
    assert r.status_code == 200
    assert _cat_de(c, "mercado") == {"Casa"}
    assert _regra(c, "mercado")["priority"] == 3


def test_editar_regra_nao_toca_categoria_travada(c):
    c.post("/import", files={"file": ("x.csv", FIXTURE.read_bytes())})
    c.post("/rules", json={"pattern": "mercado", "category": "Mercado"})
    tx = next(t for t in c.get("/transactions", params={"month": "2026-09"}).json()
              if "mercado" in (t["description"] + t["counterparty"]).lower())
    c.patch(f"/transactions/{tx['id']}", json={"category": "Presente", "remember": False})
    rid = _regra(c, "mercado")["id"]
    c.put(f"/rules/{rid}", json={"pattern": "mercado", "category": "Casa"})
    de_novo = next(t for t in c.get("/transactions", params={"month": "2026-09"}).json() if t["id"] == tx["id"])
    assert de_novo["category"] == "Presente"


def test_editar_regra_inexistente_da_404(c):
    assert c.put("/rules/999999", json={"pattern": "x", "category": "Y"}).status_code == 404


@pytest.mark.parametrize("corpo", [
    {"pattern": "", "category": "Mercado"},
    {"pattern": "   ", "category": "Mercado"},
    {"pattern": "mercado", "category": " "},
])
def test_regra_vazia_e_recusada(c, corpo):
    """Padrão vazio casaria com tudo e categorizaria o banco inteiro."""
    assert c.post("/rules", json=corpo).status_code == 422
    rid = c.get("/rules").json()[0]["id"]
    assert c.put(f"/rules/{rid}", json=corpo).status_code == 422
