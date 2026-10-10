"""Pix no crédito para terceiro conta uma vez só: fica a linha da fatura (P3, decisão do Thiago).

Na conta o Pix aparece em duas linhas com o mesmo identificador: a entrada fictícia ("Valor adicionado
na conta por cartão de crédito") e o Pix de saída. Na fatura vem "Pix no Crédito - NOME", com valor
MAIOR (inclui o custo do crédito), então o pareamento é por nome e data, não por valor.

Leituras cobertas:
  1. Pix de saída com entrada fictícia + linha na fatura do mesmo nome -> saída deixa de contar, fatura conta
  2. sem linha na fatura (fatura ainda não importada)                   -> saída continua gasto
  3. um para um: duas saídas e uma linha de fatura                      -> só uma é pareada
  4. linha de fatura muito distante da saída                            -> não pareia
  5. Pix de saída comum (sem entrada fictícia) para o mesmo nome        -> continua gasto
  6. parcelas seguintes ("- 2/3") da fatura                             -> continuam gasto (custo real)
  7. nome diferente                                                     -> não pareia
"""
import pytest

from financas import db, service

HEADER = "Data,Valor,Identificador,Descrição\n"


def conta(*linhas):
    return HEADER + "".join(f"{d},{v},{i},{desc}\n" for d, v, i, desc in linhas)


def pix_credito(data, ident, valor, nome):
    """As duas linhas que o Nubank gera para um Pix no crédito."""
    return [
        (data, f"{valor}.00", ident, "Valor adicionado na conta por cartão de crédito - Valor adicionado para Pix no Crédito"),
        (data, f"-{valor}.00", ident, f"Transferência enviada pelo Pix - {nome} - •••.111.111-•• - BANCO (0001) Agência: 1 Conta: 1-1"),
    ]


def pix_comum(data, ident, valor, nome):
    return [(data, f"-{valor}.00", ident, f"Transferência enviada pelo Pix - {nome} - •••.111.111-•• - BANCO (0001) Agência: 1 Conta: 1-1")]


def fatura(*linhas):
    return "date,title,amount\n" + "".join(f'{d},{t},"{v}"\n' for d, t, v in linhas)


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setenv("FINANCAS_OWN_NAMES", "Dono Exemplo Silva")
    c = db.connect(tmp_path / "t.db")
    yield c
    c.close()


def gastos(conn):
    return {(r["account"], r["date"], r["amount_cents"]) for r in conn.execute(
        "SELECT account, date, amount_cents FROM transactions WHERE kind='expense'")}


def test_pareia_e_conta_uma_vez(conn):
    service.import_csv(conn, conta(*pix_credito("01/07/2026", "id-1", 100, "Fulana de Tal")))
    assert ("nubank_conta", "2026-07-01", -10000) in gastos(conn)  # sem fatura ainda: continua gasto
    service.import_csv(conn, fatura(("2026-07-12", "Pix no Crédito - Fulana de Tal", "128,40")))
    g = gastos(conn)
    assert ("nubank_conta", "2026-07-01", -10000) not in g
    assert ("nubank_fatura", "2026-07-12", -12840) in g
    assert sum(1 for x in g if x[0] == "nubank_conta") == 0


def test_um_para_um(conn):
    service.import_csv(conn, conta(*pix_credito("01/07/2026", "id-1", 100, "Fulana de Tal"),
                                   *pix_credito("05/07/2026", "id-2", 100, "Fulana de Tal")))
    service.import_csv(conn, fatura(("2026-07-12", "Pix no Crédito - Fulana de Tal", "128,40")))
    na_conta = [x for x in gastos(conn) if x[0] == "nubank_conta"]
    assert len(na_conta) == 1  # uma saída pareada, a outra segue como gasto
    assert na_conta[0][1] == "2026-07-01"  # a mais próxima é a de 05/07, a outra sobra


def test_fatura_distante_nao_pareia(conn):
    service.import_csv(conn, conta(*pix_credito("01/03/2026", "id-1", 100, "Fulana de Tal")))
    service.import_csv(conn, fatura(("2026-07-12", "Pix no Crédito - Fulana de Tal", "128,40")))
    assert ("nubank_conta", "2026-03-01", -10000) in gastos(conn)


def test_pix_comum_nao_e_pareado(conn):
    service.import_csv(conn, conta(*pix_comum("01/07/2026", "id-1", 100, "Fulana de Tal")))
    service.import_csv(conn, fatura(("2026-07-12", "Pix no Crédito - Fulana de Tal", "128,40")))
    g = gastos(conn)
    assert ("nubank_conta", "2026-07-01", -10000) in g  # sem entrada fictícia, não foi pelo crédito
    assert ("nubank_fatura", "2026-07-12", -12840) in g


def test_parcelas_seguintes_continuam_gasto(conn):
    service.import_csv(conn, conta(*pix_credito("01/07/2026", "id-1", 100, "Fulana de Tal")))
    service.import_csv(conn, fatura(("2026-07-12", "Pix no Crédito - Fulana de Tal - 1/2", "64,20"),
                                    ("2026-08-12", "Pix no Crédito - Fulana de Tal - 2/2", "64,20")))
    g = gastos(conn)
    assert ("nubank_conta", "2026-07-01", -10000) not in g
    assert ("nubank_fatura", "2026-07-12", -6420) in g
    assert ("nubank_fatura", "2026-08-12", -6420) in g


def test_nome_diferente_nao_pareia(conn):
    service.import_csv(conn, conta(*pix_credito("01/07/2026", "id-1", 100, "Fulana de Tal")))
    service.import_csv(conn, fatura(("2026-07-12", "Pix no Crédito - Beltrano de Tal", "128,40")))
    assert ("nubank_conta", "2026-07-01", -10000) in gastos(conn)


def test_reimportar_nao_muda_nada(conn):
    c1 = conta(*pix_credito("01/07/2026", "id-1", 100, "Fulana de Tal"))
    f1 = fatura(("2026-07-12", "Pix no Crédito - Fulana de Tal", "128,40"))
    service.import_csv(conn, c1); service.import_csv(conn, f1)
    antes = gastos(conn)
    service.import_csv(conn, c1); service.import_csv(conn, f1)
    assert gastos(conn) == antes


def test_fatura_nunca_e_menor_que_o_pix_escolhe_a_saida_compativel(conn):
    """A fatura soma o custo do crédito: uma saída maior que a linha da fatura não pode ser a dela."""
    service.import_csv(conn, conta(*pix_credito("08/06/2026", "id-1", 100, "Fulana de Tal"),
                                   *pix_credito("10/07/2026", "id-2", 150, "Fulana de Tal")))
    service.import_csv(conn, fatura(("2026-07-12", "Pix no Crédito - Fulana de Tal", "128,40")))
    g = gastos(conn)
    assert ("nubank_conta", "2026-06-08", -10000) not in g  # a de 100 é a que virou 128,40
    assert ("nubank_conta", "2026-07-10", -15000) in g
