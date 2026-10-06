from pathlib import Path

import pytest

from financas import db, service
from financas.importer import detect_format, parse_nubank_fatura

FIX = Path(__file__).parent / "fixtures"
FATURA = (FIX / "nubank_fatura_fake.csv").read_bytes()
CONTA = (FIX / "nubank_conta_fake.csv").read_bytes()


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "t.db")
    yield c
    c.close()


def test_format_detection():
    assert detect_format(FATURA.decode()) == "nubank_fatura"
    assert detect_format(CONTA.decode()) == "nubank_conta"
    with pytest.raises(ValueError):
        detect_format("a,b\n1,2\n")


def test_brl_amounts_and_signs():
    rows = parse_nubank_fatura(FATURA)
    assert [r.amount_cents for r in rows] == [20000, -460, -460, -1234, -115990, 1000]


def test_identical_lines_same_day_are_both_kept(conn):
    r = service.import_csv(conn, FATURA)
    assert r["novas"] == 6
    assert service.import_csv(conn, FATURA)["novas"] == 0


def test_fatura_spending_excludes_payment_and_nets_refund(conn):
    service.import_csv(conn, FATURA)
    rep = service.monthly_report(conn, "2026-09")
    assert rep["gastos_total"] == pytest.approx(4.60 * 2 + 12.34 + 1159.90 - 10.00)


def test_fatura_payment_not_double_counted_with_conta(conn):
    service.import_csv(conn, CONTA)
    service.import_csv(conn, FATURA)
    kinds = {r["description"]: r["kind"] for r in conn.execute("SELECT description, kind FROM transactions")}
    assert kinds["Pagamento de fatura"] == "card_payment"
    assert kinds["Pagamento recebido"] == "card_payment"


def test_own_name_added_later_reclassifies(conn):
    service.import_csv(conn, CONTA)
    before = service.monthly_report(conn, "2026-09")["gastos_total"]
    conn.execute("INSERT INTO own_names (name) VALUES ('MARIA SILVA')")
    service.reclassify(conn)
    assert service.monthly_report(conn, "2026-09")["gastos_total"] == pytest.approx(before - 100)
