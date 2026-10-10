"""Orçamento (docs/spec/orcamento.md, ADR 0015). Regra de dinheiro: testa as leituras possíveis dela."""
from fractions import Fraction
from pathlib import Path
import random

import pytest
from fastapi.testclient import TestClient

from financas import __main__ as cli
from financas import api, db, service

CONTA = (Path(__file__).parent / "fixtures" / "nubank_conta_fake.csv").read_bytes()


def fatura(*linhas):
    """linhas: (data, título, 'valor com vírgula')."""
    return ("date,title,amount\n" + "".join(f'{d},{t},"{v}"\n' for d, t, v in linhas)).encode()


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "o.db")
    c.execute("INSERT INTO rules (pattern, category) VALUES ('uber', 'Transporte')")
    c.execute("INSERT INTO rules (pattern, category) VALUES ('mercado', 'Mercado')")
    c.commit()
    yield c
    c.close()


def estado(conn, categoria, mes="2026-09"):
    return next(i for i in service.budget_status(conn, mes)["itens"] if i["categoria"] == categoria)


# ---------- as três leituras de "80%" e "100%" ----------

def test_limites_do_estado_em_centavos():
    f = service._budget_estado
    assert f(7999, 10000) == "ok"           # 79,99%
    assert f(8000, 10000) == "atencao"      # exatamente 80%: atenção (inclusive)
    assert f(10000, 10000) == "atencao"     # exatamente 100%: ainda não estourou
    assert f(10001, 10000) == "estourou"    # um centavo acima
    assert f(0, 10000) == "ok"


def test_estado_bate_com_a_conta_exata_para_qualquer_valor():
    rng = random.Random(7)
    for _ in range(2000):
        limite, gasto = rng.randint(1, 5000), rng.randint(0, 6000)
        esperado = "estourou" if gasto > limite else "atencao" if Fraction(gasto, limite) >= Fraction(4, 5) else "ok"
        assert service._budget_estado(gasto, limite) == esperado, (gasto, limite)


def test_limite_de_centavos_quebrados_nao_arredonda_para_ok():
    # 80% de 3 centavos é 2,4: gastar 2 centavos (66,7%) é ok, 3 centavos é atenção
    assert service._budget_estado(2, 3) == "ok"
    assert service._budget_estado(3, 3) == "atencao"


# ---------- o que conta como gasto ----------

def test_gasto_do_orcamento_acompanha_o_relatorio_mensal(conn):
    service.import_csv(conn, fatura(("2026-09-02", "Uber A", "12,34"), ("2026-09-09", "Uber B", "7,66")))
    service.set_budget(conn, "Transporte", 5000)
    rel = {c["categoria"]: c["valor"] for c in service.monthly_report(conn, "2026-09")["por_categoria"]}
    assert estado(conn, "Transporte")["gasto"] == rel["Transporte"] == 20.0


def test_estorno_reduz_o_gasto(conn):
    service.import_csv(conn, fatura(("2026-09-02", "Uber A", "80,00"), ("2026-09-03", "Estorno Uber", "-30,00")))
    service.set_budget(conn, "Transporte", 10000)
    assert estado(conn, "Transporte")["gasto"] == 50.0


def test_receita_repasse_transferencia_e_fatura_nao_entram(conn):
    conn.execute("INSERT INTO own_names (name) VALUES ('MARIA SILVA')")
    service.import_csv(conn, CONTA)   # tem receita, repasse, transferência, pagamento de fatura e Pix no crédito
    service.set_budget(conn, "Mercado", 20000)
    assert estado(conn, "Mercado")["gasto"] == 85.9   # só os dois Pix para o mercado


def test_so_conta_o_mes_pedido(conn):
    service.import_csv(conn, fatura(("2026-08-30", "Uber A", "50,00"), ("2026-09-01", "Uber B", "10,00")))
    service.set_budget(conn, "Transporte", 10000)
    assert estado(conn, "Transporte", "2026-09")["gasto"] == 10.0
    assert estado(conn, "Transporte", "2026-08")["gasto"] == 50.0
    assert estado(conn, "Transporte", "2026-07")["gasto"] == 0.0


def test_categoria_orcada_sem_gasto_aparece_zerada(conn):
    service.set_budget(conn, "Lazer", 10000)
    i = estado(conn, "Lazer")
    assert (i["gasto"], i["restante"], i["percentual"], i["estado"]) == (0.0, 100.0, 0.0, "ok")


def test_restante_negativo_e_percentual_quando_estoura(conn):
    service.import_csv(conn, fatura(("2026-09-02", "Uber A", "125,00")))
    service.set_budget(conn, "Transporte", 10000)
    i = estado(conn, "Transporte")
    assert (i["restante"], i["percentual"], i["estado"]) == (-25.0, 125.0, "estourou")


def test_ordem_do_mais_grave_ao_mais_folgado(conn):
    service.import_csv(conn, fatura(("2026-09-02", "Uber A", "50,00"), ("2026-09-02", "Mercado B", "95,00"),
                                    ("2026-09-02", "Farmacia C", "9,00")))
    service.set_budget(conn, "Transporte", 10000)   # 50%  -> ok
    service.set_budget(conn, "Mercado", 10000)      # 95%  -> atenção
    service.set_budget(conn, "Saúde", 800)          # sem gasto no mês (Farmacia não tem regra neste teste) -> ok
    nomes = [(i["categoria"], i["estado"]) for i in service.budget_status(conn, "2026-09")["itens"]]
    assert nomes == [("Mercado", "atencao"), ("Transporte", "ok"), ("Saúde", "ok")]


def test_totais(conn):
    service.import_csv(conn, fatura(("2026-09-02", "Uber A", "20,00")))
    service.set_budget(conn, "Transporte", 5000)
    service.set_budget(conn, "Lazer", 2550)
    r = service.budget_status(conn, "2026-09")
    assert (r["orcado_total"], r["gasto_nas_categorias"]) == (75.5, 20.0)


# ---------- validação ----------

@pytest.mark.parametrize("categoria,limite", [("Sem categoria", 100), ("", 100), ("   ", 100), ("x" * 61, 100),
                                              ("Lazer", 0), ("Lazer", -1)])
def test_orcamento_invalido_e_recusado_sem_gravar(conn, categoria, limite):
    with pytest.raises(ValueError):
        service.set_budget(conn, categoria, limite)
    assert conn.execute("SELECT COUNT(*) FROM budgets").fetchone()[0] == 0


def test_definir_de_novo_troca_o_limite_e_remover_nao_apaga_lancamentos(conn):
    service.import_csv(conn, fatura(("2026-09-02", "Uber A", "20,00")))
    service.set_budget(conn, "Transporte", 5000)
    service.set_budget(conn, " Transporte ", 8000)
    assert conn.execute("SELECT COUNT(*), MAX(limit_cents) FROM budgets").fetchone()[:] == (1, 8000)
    assert service.delete_budget(conn, "Transporte") is True and service.delete_budget(conn, "Transporte") is False
    assert conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0] == 1


# ---------- API ----------

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DEFAULT_PATH", tmp_path / "api.db")
    with TestClient(api.app) as c:
        c.post("/import", files={"file": ("f.csv", fatura(("2026-09-02", "Uber A", "90,00")))})
        yield c


def test_api_fluxo_completo(client):
    assert client.put("/budgets/Transporte", json={"limite": 100}).status_code == 200
    r = client.get("/budgets", params={"month": "2026-09"}).json()
    assert r["itens"][0]["categoria"] == "Transporte" and r["itens"][0]["estado"] == "atencao"
    assert client.delete("/budgets/Transporte").status_code == 200
    assert client.delete("/budgets/Transporte").status_code == 404
    assert client.get("/budgets", params={"month": "2026-09"}).json()["itens"] == []


@pytest.mark.parametrize("corpo", [{"limite": 0}, {"limite": -5}, {"limite": "abc"}, {"limite": 10.005}, {"limite": 1e13}, {}])
def test_api_recusa_limite_invalido(client, corpo):
    assert client.put("/budgets/Transporte", json=corpo).status_code == 422
    assert client.get("/budgets", params={"month": "2026-09"}).json()["itens"] == []


def test_api_recusa_sem_categoria_com_mensagem(client):
    r = client.put("/budgets/Sem categoria", json={"limite": 10})
    assert r.status_code == 422 and "classifique" in r.json()["detail"]


def test_api_centavos_sem_erro_de_ponto_flutuante(client):
    for v in (150.35, 0.01, 1234567.89):
        assert client.put("/budgets/Lazer", json={"limite": v}).status_code == 200
        assert client.get("/budgets", params={"month": "2026-09"}).json()["itens"][0]["limite"] == v


def test_api_meses_com_dados(client):
    client.post("/import", files={"file": ("g.csv", fatura(("2026-07-05", "Loja", "1,00")))})
    assert client.get("/months").json() == ["2026-09", "2026-07"]


def test_api_meses_vazio(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DEFAULT_PATH", tmp_path / "vazio.db")
    with TestClient(api.app) as c:
        assert c.get("/months").json() == []


# ---------- terminal ----------

@pytest.mark.parametrize("valor,centavos", [("150", 15000), ("150.5", 15050), ("150,50", 15050), ("1.500,00", 150000), ("R$ 99,90", 9990),
                                           ("1.500", 150000), ("10.005", 1000500), ("150.50", 15050)])
def test_cli_aceita_formatos_de_valor(tmp_path, monkeypatch, valor, centavos):
    monkeypatch.setattr(db, "DEFAULT_PATH", tmp_path / "cli.db")
    assert cli.main(["orcamento", "Delivery", valor]) == 0
    assert db.connect().execute("SELECT limit_cents FROM budgets").fetchone()[0] == centavos


@pytest.mark.parametrize("valor", ["abc", "0", "-5", "", "10,555", "150.5555", "1,5,5"])
def test_cli_recusa_valor_invalido(tmp_path, monkeypatch, valor):
    monkeypatch.setattr(db, "DEFAULT_PATH", tmp_path / "cli2.db")
    assert cli.main(["orcamento", "Delivery", valor]) == 1
    assert db.connect().execute("SELECT COUNT(*) FROM budgets").fetchone()[0] == 0
