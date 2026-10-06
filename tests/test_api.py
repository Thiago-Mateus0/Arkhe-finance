from pathlib import Path

from fastapi.testclient import TestClient

from financas import api, db

FIXTURE = Path(__file__).parent / "fixtures" / "nubank_conta_fake.csv"


def test_api_flow(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DEFAULT_PATH", tmp_path / "api.db")
    c = TestClient(api.app)
    c.post("/rules", json={"pattern": "mercado", "category": "Mercado"})
    r = c.post("/import/nubank-conta", files={"file": ("x.csv", FIXTURE.read_bytes())})
    assert r.json()["novas"] == 9
    rep = c.get("/reports/monthly", params={"month": "2026-09"}).json()
    assert any(x["categoria"] == "Mercado" for x in rep["por_categoria"])
    assert c.post("/import/nubank-conta", files={"file": ("x.csv", b"a,b\n1,2\n")}).status_code == 422
    assert c.get("/").status_code == 200
