"""Aplicação e resgate de investimento não são gasto nem receita (P18, decisão do Thiago).

Leituras cobertas:
  1. "Aplicação RDB" (sai da conta)  -> investment, fora do gasto
  2. "Resgate RDB" (entra na conta) -> investment, fora da receita
  3. aplicação e resgate de mesmo valor no mesmo dia -> continua investment (não vira repasse)
  4. nome parecido NÃO é investimento: "Aplicativo ...", Pix para quem tem "Resgate" no meio do nome
  5. tipo de operação do Pluggy RESGATE_APLIC_FINANCEIRA -> investment, mesmo com outra descrição
  6. totais do mês: gasto e receita não incluem investimento
"""
import pytest

from financas import classifier, db, service

CAB = "Data,Valor,Identificador,Descrição\n"


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setenv("FINANCAS_OWN_NAMES", "Dono Exemplo Silva")
    c = db.connect(tmp_path / "t.db")
    yield c
    c.close()


def kinds(conn):
    return {r["description"]: r["kind"] for r in conn.execute("SELECT description, kind FROM transactions")}


def test_classificador():
    c = classifier.classify
    assert c("Aplicação RDB", -10000, "", set()) == classifier.INVESTMENT
    assert c("Resgate RDB", 10000, "", set()) == classifier.INVESTMENT
    assert c("Aplicativo Exemplo Ltda", -1000, "", set()) == classifier.EXPENSE
    assert c("Transferência enviada pelo Pix - RESGATE LTDA - •••.111.111-•• - X", -1000, "RESGATE LTDA", set()) \
        == classifier.EXPENSE
    assert c("Algo qualquer", 5000, "", set(), operation_type="RESGATE_APLIC_FINANCEIRA") == classifier.INVESTMENT
    assert c("Algo qualquer", 5000, "", set(), operation_type="PIX") == classifier.INCOME


def test_importacao_e_totais(conn):
    service.import_csv(conn, CAB +
        "05/09/2026,-100.00,id-1,Aplicação RDB\n"
        "06/09/2026,40.00,id-2,Resgate RDB\n"
        "07/09/2026,-20.00,id-3,Aplicativo Exemplo Ltda\n"
        "08/09/2026,300.00,id-4,Transferência recebida pelo Pix - CICLANO - •••.222.222-•• - X (1) Agência: 1 Conta: 1-1\n")
    k = kinds(conn)
    assert k["Aplicação RDB"] == "investment" and k["Resgate RDB"] == "investment"
    assert k["Aplicativo Exemplo Ltda"] == "expense"
    rep = service.monthly_report(conn, "2026-09")
    assert rep["gastos_total"] == 20.0      # só o aplicativo; a aplicação de 100 não é gasto
    assert rep["receitas_total"] == 300.0   # o resgate de 40 não é receita


def test_aplicacao_e_resgate_iguais_no_mesmo_dia_seguem_investimento(conn):
    service.import_csv(conn, CAB + "05/09/2026,-50.00,id-1,Aplicação RDB\n05/09/2026,50.00,id-2,Resgate RDB\n")
    assert set(kinds(conn).values()) == {"investment"}
