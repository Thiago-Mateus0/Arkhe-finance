"""Pix no crédito para o próprio dono é transferência, não gasto (P3, decisão do Thiago).

Leituras possíveis, todas cobertas aqui:
  1. para nome próprio            -> transfer
  2. para terceiro                -> segue expense (esse é o outro lado de P3, ainda aberto)
  3. parcelado ("- 2/3") próprio  -> transfer
  4. nome próprio cadastrado depois da importação -> reclassifica a fatura
  5. compra comum com o nome do dono na loja      -> segue expense
"""
import pytest

from financas import classifier, db, service

FATURA = (
    "date,title,amount\n"
    "2026-09-12,Pix no Crédito - Dono Exemplo Silva,\"200,00\"\n"
    "2026-09-12,Pix no Crédito - Dono Exemplo Silva - 2/3,\"50,00\"\n"
    "2026-09-12,Pix no Crédito - Fulana de Tal,\"80,00\"\n"
    "2026-09-12,Loja do Dono Exemplo Silva,\"30,00\"\n"
)


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.delenv("FINANCAS_OWN_NAMES", raising=False)
    c = db.connect(tmp_path / "t.db")
    yield c
    c.close()


def _kinds(conn):
    return {r["description"]: r["kind"] for r in conn.execute(
        "SELECT description, kind FROM transactions WHERE account='nubank_fatura'")}


def test_classificador_nome_proprio():
    own = {"DONO EXEMPLO SILVA"}
    f = classifier.classify_fatura
    assert f("Pix no Crédito - Dono Exemplo Silva", -20000, own) == classifier.TRANSFER
    assert f("Pix no Crédito - DONO EXEMPLO SILVA - 2/3", -5000, own) == classifier.TRANSFER
    assert f("Pix no Crédito - Fulana de Tal", -8000, own) == classifier.EXPENSE
    assert f("Loja do Dono Exemplo Silva", -3000, own) == classifier.EXPENSE
    assert f("Pagamento recebido", 10000, own) == classifier.CARD_PAYMENT


def test_importacao_com_nome_proprio(conn, monkeypatch):
    monkeypatch.setenv("FINANCAS_OWN_NAMES", "Dono Exemplo Silva")
    service.import_csv(conn, FATURA)
    k = _kinds(conn)
    assert k["Pix no Crédito - Dono Exemplo Silva"] == "transfer"
    assert k["Pix no Crédito - Dono Exemplo Silva - 2/3"] == "transfer"
    assert k["Pix no Crédito - Fulana de Tal"] == "expense"
    assert k["Loja do Dono Exemplo Silva"] == "expense"


def test_nome_cadastrado_depois_reclassifica_a_fatura(conn, monkeypatch):
    service.import_csv(conn, FATURA)
    assert _kinds(conn)["Pix no Crédito - Dono Exemplo Silva"] == "expense"
    monkeypatch.setenv("FINANCAS_OWN_NAMES", "Dono Exemplo Silva")
    service.reclassify(conn)
    assert _kinds(conn)["Pix no Crédito - Dono Exemplo Silva"] == "transfer"
    # e volta ao tirar o nome
    monkeypatch.delenv("FINANCAS_OWN_NAMES")
    service.reclassify(conn)
    assert _kinds(conn)["Pix no Crédito - Dono Exemplo Silva"] == "expense"


def test_nao_entra_no_total_de_gastos(conn, monkeypatch):
    monkeypatch.setenv("FINANCAS_OWN_NAMES", "Dono Exemplo Silva")
    service.import_csv(conn, FATURA)
    total = conn.execute(
        "SELECT SUM(ABS(amount_cents)) FROM transactions WHERE kind='expense' AND account='nubank_fatura'"
    ).fetchone()[0]
    assert total == 8000 + 3000  # só o Pix para terceiro e a compra na loja
