"""Importador do Meu Pluggy (ADRs 0020 e 0022). Dados fictícios no formato da API v2.

Leituras cobertas:
  conta:  direção pelo type; só POSTED; centavos exatos
  cartão: sinal do amount é INVERTIDO (compra positiva) -> direção pelo type; data = billPostDate;
          PAGAMENTO_FATURA = pagamento de fatura; parcela vira "- Parcela n/m"
  idempotência: sincronizar de novo não muda nada
  duplicata com CSV, nos dois sentidos: valor igual e data até 1 dia, um para um, exato primeiro
"""
import pytest

from financas import db, pluggy, service


class FakeAPI:
    def __init__(self, contas, txs):
        self._contas, self._txs = contas, txs

    def contas(self):
        return self._contas

    def transacoes(self, conta_id):
        return self._txs.get(conta_id, [])


BANCO = {"id": "acc-banco", "type": "BANK", "subtype": "CHECKING_ACCOUNT"}
CARTAO = {"id": "acc-cartao", "type": "CREDIT", "subtype": "CREDIT_CARD"}


def tx(id, date, amount, tipo, desc, status="POSTED", op=None, cc=None):
    return {"id": id, "date": f"{date}T00:00:00.000Z", "amount": amount, "type": tipo, "description": desc,
            "descriptionRaw": desc, "status": status, "operationType": op, "creditCardMetadata": cc}


PIX_ENVIADO = "Transferência enviada pelo Pix - FULANO DE TAL - •••.111.111-•• - BANCO (0001) Agência: 1 Conta: 1-1"


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setenv("FINANCAS_OWN_NAMES", "Dono Exemplo Silva")
    c = db.connect(tmp_path / "t.db")
    yield c
    c.close()


def linhas(conn, conta=None):
    q = "SELECT account, date, amount_cents, kind, description, source FROM transactions"
    q += " WHERE account=?" if conta else ""
    return [tuple(r) for r in conn.execute(q + " ORDER BY date, amount_cents", (conta,) if conta else ())]


def test_conta_direcao_pelo_type_e_so_posted(conn):
    api = FakeAPI([BANCO], {"acc-banco": [
        tx("a", "2026-09-10", 19.9, "DEBIT", PIX_ENVIADO),            # sinal do amount não importa
        tx("b", "2026-09-11", 100.0, "CREDIT", "Transferência recebida pelo Pix - CICLANO - •••.222.222-•• - X (1)"),
        tx("c", "2026-09-12", 5.0, "DEBIT", "Compra pendente", status="PENDING"),
    ]})
    r = pluggy.sincronizar(conn, api)
    assert r["novas"] == 2
    assert [(d, c) for _, d, c, *_ in linhas(conn)] == [("2026-09-10", -1990), ("2026-09-11", 10000)]


def test_centavos_exatos_sem_float(conn):
    api = FakeAPI([BANCO], {"acc-banco": [tx("a", "2026-09-10", 0.29, "DEBIT", "X"), tx("b", "2026-09-10", 1.15, "DEBIT", "Y")]})
    pluggy.sincronizar(conn, api)
    assert sorted(c for _, _, c, *_ in linhas(conn)) == [-115, -29]


def test_cartao_sinal_invertido_data_da_fatura_e_pagamento(conn):
    api = FakeAPI([CARTAO], {"acc-cartao": [
        tx("a", "2026-09-01", 50.0, "DEBIT", "Loja Exemplo", op="PAGAMENTO",
           cc={"billPostDate": "2026-09-12", "installmentNumber": 1, "totalInstallments": 1, "paymentType": "SINGLE"}),
        tx("b", "2026-09-20", -300.0, "CREDIT", "Pagamento da fatura", op="PAGAMENTO_FATURA",
           cc={"billPostDate": "2026-09-20"}),
        tx("c", "2026-09-02", -10.0, "CREDIT", "Estorno Loja Exemplo", op="ESTORNO", cc={"billPostDate": "2026-09-12"}),
    ]})
    pluggy.sincronizar(conn, api)
    por_desc = {d: (data, c, k) for _, data, c, k, d, _ in linhas(conn)}
    assert por_desc["Loja Exemplo"] == ("2026-09-12", -5000, "expense")          # compra: negativa, data da fatura
    assert por_desc["Pagamento da fatura"] == ("2026-09-20", 30000, "card_payment")
    assert por_desc["Estorno Loja Exemplo"] == ("2026-09-12", 1000, "expense")  # estorno reduz o gasto


def test_parcela_vira_sufixo_que_o_resto_do_app_entende(conn):
    api = FakeAPI([CARTAO], {"acc-cartao": [
        tx("a", "2026-09-01", 30.0, "DEBIT", "Loja Exemplo", op="PAGAMENTO",
           cc={"billPostDate": "2026-09-12", "installmentNumber": 1, "totalInstallments": 3, "paymentType": "INSTALLMENT"}),
    ]})
    pluggy.sincronizar(conn, api)
    assert linhas(conn)[0][4] == "Loja Exemplo - Parcela 1/3"
    from financas import parcelas
    assert [m["mes"] for m in parcelas.projetar(conn)["meses"]] == ["2026-10", "2026-11"]


def test_sincronizar_de_novo_nao_muda_nada(conn):
    api = FakeAPI([BANCO], {"acc-banco": [tx("a", "2026-09-10", 19.9, "DEBIT", PIX_ENVIADO)]})
    assert pluggy.sincronizar(conn, api)["novas"] == 1
    r = pluggy.sincronizar(conn, api)
    assert (r["novas"], r["duplicadas"]) == (0, 1)
    assert len(linhas(conn)) == 1


def test_csv_primeiro_depois_pluggy_nao_duplica(conn):
    service.import_csv(conn, "Data,Valor,Identificador,Descrição\n"
                             f"10/09/2026,-19.90,id-1,{PIX_ENVIADO}\n")
    api = FakeAPI([BANCO], {"acc-banco": [tx("a", "2026-09-11", 19.9, "DEBIT", PIX_ENVIADO)]})  # 1 dia de diferença
    r = pluggy.sincronizar(conn, api)
    assert (r["novas"], r["duplicadas"]) == (0, 1)
    assert len(linhas(conn)) == 1


def test_pluggy_primeiro_depois_csv_nao_duplica(conn):
    api = FakeAPI([BANCO], {"acc-banco": [tx("a", "2026-09-11", 19.9, "DEBIT", PIX_ENVIADO)]})
    pluggy.sincronizar(conn, api)
    r = service.import_csv(conn, "Data,Valor,Identificador,Descrição\n"
                                 f"10/09/2026,-19.90,id-1,{PIX_ENVIADO}\n")
    assert (r["novas"], r["duplicadas"]) == (0, 1)
    assert len(linhas(conn)) == 1


def test_um_para_um_o_excedente_entra(conn):
    service.import_csv(conn, "Data,Valor,Identificador,Descrição\n"
                             f"10/09/2026,-4.60,id-1,{PIX_ENVIADO}\n")
    api = FakeAPI([BANCO], {"acc-banco": [tx("a", "2026-09-10", 4.6, "DEBIT", PIX_ENVIADO),
                                          tx("b", "2026-09-10", 4.6, "DEBIT", PIX_ENVIADO)]})
    r = pluggy.sincronizar(conn, api)
    assert (r["novas"], r["duplicadas"]) == (1, 1)  # duas corridas iguais: uma já estava, a outra é nova
    assert len(linhas(conn)) == 2


def test_data_exata_tem_preferencia_sobre_um_dia_de_diferenca(conn):
    service.import_csv(conn, "Data,Valor,Identificador,Descrição\n"
                             f"10/09/2026,-4.60,id-1,{PIX_ENVIADO}\n"
                             f"11/09/2026,-4.60,id-2,{PIX_ENVIADO}\n")
    api = FakeAPI([BANCO], {"acc-banco": [tx("a", "2026-09-11", 4.6, "DEBIT", PIX_ENVIADO),
                                          tx("b", "2026-09-10", 4.6, "DEBIT", PIX_ENVIADO)]})
    r = pluggy.sincronizar(conn, api)
    assert (r["novas"], r["duplicadas"]) == (0, 2)


def test_valor_diferente_ou_dois_dias_nao_casa(conn):
    service.import_csv(conn, "Data,Valor,Identificador,Descrição\n"
                             f"10/09/2026,-4.60,id-1,{PIX_ENVIADO}\n")
    api = FakeAPI([BANCO], {"acc-banco": [tx("a", "2026-09-10", 4.61, "DEBIT", PIX_ENVIADO),
                                          tx("b", "2026-09-12", 4.6, "DEBIT", PIX_ENVIADO)]})
    assert pluggy.sincronizar(conn, api)["novas"] == 2


def test_nome_proprio_vira_transferencia_tambem_no_pluggy(conn):
    api = FakeAPI([BANCO], {"acc-banco": [tx(
        "a", "2026-09-10", 50.0, "DEBIT",
        "Transferência enviada pelo Pix - DONO EXEMPLO SILVA - •••.111.111-•• - BANCO (0001) Agência: 1 Conta: 1-1")]})
    pluggy.sincronizar(conn, api)
    assert linhas(conn)[0][3] == "transfer"


@pytest.mark.parametrize("ruim", [
    {"id": "x", "date": "lixo", "amount": 1.0, "type": "DEBIT", "description": "a", "status": "POSTED"},
    {"id": "x", "date": "2026-09-10T00:00:00.000Z", "amount": "abc", "type": "DEBIT", "description": "a", "status": "POSTED"},
    {"id": "x", "date": "2026-09-10T00:00:00.000Z", "amount": 1.0, "type": "OUTRO", "description": "a", "status": "POSTED"},
    {"id": "x", "date": "2026-09-10T00:00:00.000Z", "amount": float("nan"), "type": "DEBIT", "description": "a", "status": "POSTED"},
])
def test_linha_malformada_e_ignorada_sem_quebrar(conn, ruim):
    r = pluggy.sincronizar(conn, FakeAPI([BANCO], {"acc-banco": [ruim, tx("ok", "2026-09-10", 1.0, "DEBIT", "ok")]}))
    assert (r["novas"], r["ignoradas"]) == (1, 1)
