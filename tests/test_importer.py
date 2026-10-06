from pathlib import Path

import pytest

from financas import db, service
from financas.importer import counterparty_of, parse_nubank_conta

FIXTURE = Path(__file__).parent / "fixtures" / "nubank_conta_fake.csv"


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "t.db")
    yield c
    c.close()


def test_parse_values_and_dates():
    rows = parse_nubank_conta(FIXTURE.read_bytes())
    assert len(rows) == 9
    assert rows[0].date == "2026-09-01" and rows[0].amount_cents == 50000
    assert rows[2].amount_cents == -4590


def test_counterparty_extraction():
    d = "Transferência enviada pelo Pix - MERCADO DO ZE LTDA - 22.222.222/0001-22 - BANCO Z (0003)"
    assert counterparty_of(d) == "MERCADO DO ZE LTDA"
    d2 = "Transferência enviada pelo Pix via Open Banking - Iniciada por: AppPix - EMPRESA FICTICIA LTDA - 11.111.111/0001-11 - X"
    assert counterparty_of(d2) == "EMPRESA FICTICIA LTDA"
    assert counterparty_of("Pagamento de fatura") == ""


def test_shared_id_and_identical_rows_get_distinct_keys():
    keys = [r.dedupe_key for r in parse_nubank_conta(FIXTURE.read_bytes())]
    assert len(set(keys)) == len(keys)  # id-6 repetido e duas linhas idênticas de id-7


def test_reimport_is_idempotent(conn):
    first = service.import_csv(conn, FIXTURE.read_bytes())
    again = service.import_csv(conn, FIXTURE.read_bytes())
    assert first["novas"] == 9
    assert again == {"formato": "nubank_conta", "lidas": 9, "novas": 0, "duplicadas": 9}


def test_wrong_csv_rejected(conn):
    with pytest.raises(ValueError):
        service.import_csv(conn, "a,b\n1,2\n")


def test_spending_excludes_transfers_cardpayment_credit_and_passthrough(conn):
    conn.execute("INSERT INTO own_names (name) VALUES ('MARIA SILVA')")
    conn.execute("INSERT INTO rules (pattern, category, priority) VALUES ('mercado', 'Mercado', 0)")
    conn.execute("INSERT INTO rules (pattern, category, priority) VALUES ('barbearia', 'Cuidados', 0)")
    service.import_csv(conn, FIXTURE.read_bytes())
    rep = service.monthly_report(conn, "2026-09")
    cats = {c["categoria"]: c["valor"] for c in rep["por_categoria"]}
    # 500 recebido e 500 enviado no mesmo dia = passagem; MARIA = própria; fatura excluída;
    # Pix no crédito (+150) é fictício, o gasto de 150 na barbearia conta.
    assert cats == {"Cuidados": 150.0, "Mercado": 45.90 + 40.0}
    assert rep["receitas_total"] == 0


def test_rule_priority_then_specificity(conn):
    conn.execute("INSERT INTO rules (pattern, category, priority) VALUES ('mercado', 'Casa', 0)")
    conn.execute("INSERT INTO rules (pattern, category, priority) VALUES ('mercado do ze', 'Mercado', 0)")
    service.import_csv(conn, FIXTURE.read_bytes())
    assert conn.execute("SELECT DISTINCT category FROM transactions WHERE counterparty='MERCADO DO ZE LTDA'").fetchall()[0][0] == "Mercado"
    conn.execute("INSERT INTO rules (pattern, category, priority) VALUES ('mercado', 'Forçada', 5)")
    service.recategorize(conn)
    assert conn.execute("SELECT DISTINCT category FROM transactions WHERE counterparty='MERCADO DO ZE LTDA'").fetchall()[0][0] == "Forçada"
