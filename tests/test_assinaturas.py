"""Assinaturas (P5): é a categoria "Assinaturas", lida do que o usuário marcou por regra.

Não detecta sozinho: Uber, 99 e Pix para pessoas se repetem e não são assinatura.
Leituras cobertas:
  1. soma do mês só da categoria Assinaturas, só kind=expense (receita, transferência ficam fora)
  2. conta e fatura entram igual
  3. estorno na fatura reduz o total
  4. uma assinatura por nome; valor e data são os da cobrança mais recente
  5. próxima cobrança estimada só com 2+ meses de histórico
  6. só lista as ativas: com cobrança nos 3 meses que terminam no mês pedido
  7. outras categorias não entram
"""
import pytest

from financas import assinaturas, db, service


def fatura(*linhas):
    return "date,title,amount\n" + "".join(f'{d},{t},"{v}"\n' for d, t, v in linhas)


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setenv("FINANCAS_OWN_NAMES", "Dono Exemplo Silva")
    c = db.connect(tmp_path / "t.db")
    c.execute("INSERT INTO rules (household_id, pattern, category, priority) VALUES (?,?,?,?)",
              (service.HOUSEHOLD, "streaming", "Assinaturas", 0))
    c.commit()
    yield c
    c.close()


def itens(conn, mes):
    return {i["nome"]: i for i in assinaturas.listar(conn, mes)["itens"]}


def test_soma_do_mes_so_da_categoria(conn):
    service.import_csv(conn, fatura(("2026-09-05", "Streaming Exemplo", "39,90"),
                                    ("2026-09-06", "Padaria Exemplo", "12,00")))
    r = assinaturas.listar(conn, "2026-09")
    assert r["total"] == 39.9


def test_conta_e_fatura_entram(conn):
    service.import_csv(conn, "Data,Valor,Identificador,Descrição\n"
                             "06/09/2026,-20.00,id-1,Compra no débito - Streaming Conta\n")
    service.import_csv(conn, fatura(("2026-09-05", "Streaming Exemplo", "39,90")))
    assert assinaturas.listar(conn, "2026-09")["total"] == 59.9


def test_estorno_reduz_o_total(conn):
    service.import_csv(conn, fatura(("2026-09-05", "Streaming Exemplo", "39,90"),
                                    ("2026-09-08", "Estorno Streaming Exemplo", "- 10,00")))
    assert assinaturas.listar(conn, "2026-09")["total"] == 29.9


def test_valor_e_data_da_cobranca_mais_recente(conn):
    service.import_csv(conn, fatura(("2026-07-05", "Streaming Exemplo", "59,90"),
                                    ("2026-08-05", "Streaming Exemplo", "159,90")))
    i = itens(conn, "2026-08")["STREAMING EXEMPLO"]
    assert (i["ultima_data"], i["ultimo_valor"], i["meses"]) == ("2026-08-05", 159.9, 2)


def test_proxima_so_com_dois_meses(conn):
    service.import_csv(conn, fatura(("2026-08-05", "Streaming Exemplo", "39,90")))
    assert itens(conn, "2026-08")["STREAMING EXEMPLO"]["proxima"] is None
    service.import_csv(conn, fatura(("2026-09-05", "Streaming Exemplo", "39,90")))
    assert itens(conn, "2026-09")["STREAMING EXEMPLO"]["proxima"] == "2026-10-05"


def test_so_lista_as_ativas(conn):
    service.import_csv(conn, fatura(("2026-03-05", "Streaming Antigo", "20,00"),
                                    ("2026-09-05", "Streaming Exemplo", "39,90")))
    assert set(itens(conn, "2026-09")) == {"STREAMING EXEMPLO"}
    assert set(itens(conn, "2026-03")) == {"STREAMING ANTIGO"}


def test_outras_categorias_nao_entram(conn):
    service.import_csv(conn, fatura(("2026-09-06", "Padaria Exemplo", "12,00")))
    r = assinaturas.listar(conn, "2026-09")
    assert r["total"] == 0 and r["itens"] == []
