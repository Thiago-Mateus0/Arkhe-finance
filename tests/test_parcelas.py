"""Parcelas futuras (ADR 0012): projeta o que ainda vem pela frente a partir da fatura.

Como o Nubank escreve: "TÍTULO - Parcela 1/2" e, no Pix no crédito, "Pix no Crédito - NOME - 2/2".
Cada linha da fatura é UMA parcela, com o valor da parcela. Projeção é leitura; não muda o tipo
nem o total de gastos.

Leituras cobertas:
  1. 1/3 vira duas parcelas futuras (meses seguintes, mesmo valor)
  2. a última parcela (3/3) não projeta nada
  3. a mesma compra vista em 1/3 e 2/3: projeta só o que falta depois da mais recente
  4. compras diferentes com mesmo título mas valor diferente não se misturam
  5. Pix no crédito parcelado também projeta
  6. compra sem parcela não projeta
  7. só projeta depois do último mês importado (não inventa parcela de mês já coberto)
"""
import pytest

from financas import db, parcelas, service


def fatura(*linhas):
    return "date,title,amount\n" + "".join(f'{d},{t},"{v}"\n' for d, t, v in linhas)


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "t.db")
    yield c
    c.close()


def meses(conn):
    return {m["mes"]: m["total"] for m in parcelas.projetar(conn)["meses"]}


def test_projeta_parcelas_restantes(conn):
    service.import_csv(conn, fatura(("2026-09-10", "Loja Exemplo - Parcela 1/3", "30,00")))
    assert meses(conn) == {"2026-10": 30.0, "2026-11": 30.0}


def test_ultima_parcela_nao_projeta(conn):
    service.import_csv(conn, fatura(("2026-09-10", "Loja Exemplo - Parcela 3/3", "30,00")))
    assert meses(conn) == {}


def test_mesma_compra_em_varias_faturas_projeta_so_o_que_falta(conn):
    service.import_csv(conn, fatura(("2026-08-10", "Loja Exemplo - Parcela 1/4", "25,00"),
                                    ("2026-09-10", "Loja Exemplo - Parcela 2/4", "25,00")))
    assert meses(conn) == {"2026-10": 25.0, "2026-11": 25.0}


def test_valores_diferentes_nao_se_misturam(conn):
    service.import_csv(conn, fatura(("2026-09-10", "Loja Exemplo - Parcela 1/2", "30,00"),
                                    ("2026-09-11", "Loja Exemplo - Parcela 1/2", "50,00")))
    assert meses(conn) == {"2026-10": 80.0}


def test_pix_no_credito_parcelado_projeta(conn):
    service.import_csv(conn, fatura(("2026-09-10", "Pix no Crédito - Fulana de Tal - 1/2", "64,20")))
    assert meses(conn) == {"2026-10": 64.2}


def test_compra_sem_parcela_nao_projeta(conn):
    service.import_csv(conn, fatura(("2026-09-10", "Padaria Exemplo", "12,00")))
    assert meses(conn) == {}


def test_nao_projeta_para_mes_ja_importado(conn):
    service.import_csv(conn, fatura(("2026-09-10", "Loja Exemplo - Parcela 1/3", "30,00"),
                                    ("2026-10-10", "Outra Loja", "10,00")))
    # a fatura de outubro já foi importada e não trouxe a parcela 2/3: não inventa outubro
    assert meses(conn) == {"2026-11": 30.0}


def test_nao_altera_o_total_de_gastos(conn):
    service.import_csv(conn, fatura(("2026-09-10", "Loja Exemplo - Parcela 1/3", "30,00")))
    antes = conn.execute("SELECT SUM(amount_cents) FROM transactions WHERE kind='expense'").fetchone()[0]
    parcelas.projetar(conn)
    depois = conn.execute("SELECT SUM(amount_cents) FROM transactions WHERE kind='expense'").fetchone()[0]
    assert antes == depois == -3000


@pytest.mark.parametrize("marca", ["1/999999999", "1/61", "0/3", "5/3", "1/1"])
def test_parcelamento_implausivel_e_ignorado(conn, marca):
    """O CSV não é confiável: total absurdo não pode travar nem inflar a projeção."""
    service.import_csv(conn, fatura(("2026-09-10", f"Loja Exemplo - Parcela {marca}", "30,00")))
    assert meses(conn) == {}


def test_limite_de_parcelas_aceita_o_maximo(conn):
    service.import_csv(conn, fatura(("2026-09-10", f"Loja Exemplo - Parcela 1/{parcelas.MAX_PARCELAS}", "30,00")))
    assert len(meses(conn)) == parcelas.MAX_PARCELAS - 1
