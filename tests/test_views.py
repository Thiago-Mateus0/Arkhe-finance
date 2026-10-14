import pytest
from fastapi.testclient import TestClient

from financas import api, db, service

CSV = (
    "date,title,amount\n"
    '2026-08-30,Loja Antiga,"50,00"\n'
    '2026-09-02,Uber Uber *Trip,"10,00"\n'
    '2026-09-02,Padaria Boa,"5,50"\n'
    '2026-09-10,Pagamento recebido,"- 20,00"\n'
)


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DEFAULT_PATH", tmp_path / "v.db")
    with TestClient(api.app) as c:
        c.post("/import", files={"file": ("f.csv", CSV.encode())})
        yield c


def test_daily_report_shape_and_values(client):
    r = client.get("/reports/daily", params={"month": "2026-09"}).json()
    assert len(r["dias"]) == 30 and len(r["anterior"]) == 31
    assert r["dias"][1] == {"dia": 2, "gastos": 15.5, "entradas": 0}
    assert r["anterior"][29]["gastos"] == 50.0  # 30/08


def test_month_boundaries_for_february_and_december():
    assert service._days_in_month("2028-02") == 29 and service._days_in_month("2026-12") == 31


def test_monthly_report_splits_card_and_account(client):
    r = client.get("/reports/monthly", params={"month": "2026-09"}).json()
    assert r["gastos_cartao"] == 15.5 and r["gastos_conta"] == 0


def test_transactions_search_kinds_and_order(client):
    t = lambda **p: client.get("/transactions", params={"month": "2026-09", **p}).json()
    assert [x["description"] for x in t(q="UBER")] == ["Uber Uber *Trip"]
    assert {x["kind"] for x in t(kinds="expense")} == {"expense"}
    assert t(desc=True)[0]["date"] >= t(desc=True)[-1]["date"]
    assert t(q="   ") == t()
