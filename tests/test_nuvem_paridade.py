"""Etapa 2 do ADR 0025: o importador grava no Postgres e dá o MESMO resultado que no SQLite.

A prova é a paridade: a mesma entrada, nos dois bancos, gera as mesmas linhas, tipos e categorias
(classificação, repasse, duplicata, Pix no crédito, idempotência, categoria travada). Dados fictícios.
Pula se não houver Docker com a imagem postgres:16.
"""
import uuid
from pathlib import Path

import pytest
from conftest import docker_ok, psql
from test_pluggy import BANCO, CARTAO, FakeAPI, tx

from financas import db, nuvem, pluggy, service

pytestmark = pytest.mark.skipif(not docker_ok(), reason="precisa de Docker com a imagem postgres:16")

FIX = Path(__file__).parent / "fixtures"
SNAPSHOT = ("SELECT account, date, amount_cents, description, counterparty, kind, category, category_locked,"
            " dedupe_key, source, external_id, operation_type FROM transactions WHERE household_id=? ORDER BY dedupe_key")


@pytest.fixture
def ambos(pg, tmp_path, monkeypatch):
    """Um SQLite novo e uma casa nova no Postgres."""
    monkeypatch.setenv("FINANCAS_OWN_NAMES", "Dono Exemplo Silva")
    nome, url = pg
    casa = str(uuid.uuid4())
    psql(nome, f"insert into households (id, name) values ('{casa}', 'teste')")
    lite = db.connect(tmp_path / "t.db")
    nuv = nuvem.PgConn(url, casa)
    yield lite, nuv
    lite.close()
    nuv.close()


def foto(conn) -> list[tuple]:
    out = []
    for r in conn.execute(SNAPSHOT, (service._casa(conn),)).fetchall():
        v = list(dict(r).values()) if not isinstance(r, tuple) else list(r)
        v[7] = bool(v[7])  # category_locked: 0/1 no SQLite, boolean no Postgres
        out.append(tuple(v))
    return out


def importar_fixtures(lite, nuv):
    for conn in (lite, nuv):
        service.seed_default_rules_once(conn)
    resultados = []
    for arq in ("nubank_conta_fake.csv", "nubank_fatura_fake.csv"):
        dados = (FIX / arq).read_bytes()
        resultados.append((service.import_csv(lite, dados), service.import_csv(nuv, dados)))
    return resultados


def test_csv_da_conta_e_da_fatura_dao_o_mesmo_resultado(ambos):
    lite, nuv = ambos
    for a, b in importar_fixtures(lite, nuv):
        assert a == b
    assert len(foto(lite)) > 0
    assert foto(lite) == foto(nuv)


def test_reimportar_nao_muda_nada_em_nenhum_dos_dois(ambos):
    lite, nuv = ambos
    importar_fixtures(lite, nuv)
    antes_l, antes_n = foto(lite), foto(nuv)
    for a, b in importar_fixtures(lite, nuv):
        assert a["novas"] == 0 and b["novas"] == 0
    assert foto(lite) == antes_l and foto(nuv) == antes_n


def test_regras_padrao_so_na_primeira_vez(ambos):
    lite, nuv = ambos
    for conn in (lite, nuv):
        assert service.seed_default_rules_once(conn) is True
        assert service.seed_default_rules_once(conn) is False
    assert len(service.get_rules(lite)) == len(service.get_rules(nuv)) > 0


def test_categoria_manual_fica_travada_e_regra_nova_recategoriza_o_resto(ambos):
    lite, nuv = ambos
    importar_fixtures(lite, nuv)
    for conn in (lite, nuv):
        tid = conn.execute("SELECT id FROM transactions WHERE household_id=? AND kind='expense' ORDER BY dedupe_key LIMIT 1",
                          (service._casa(conn),)).fetchone()["id"]
        r = service.set_category(conn, tid, "Categoria Teste", remember=True)
        assert r["categoria"] == "Categoria Teste"
    assert foto(lite) == foto(nuv)
    assert any(f[7] for f in foto(nuv))  # a linha travada existe


def test_pluggy_casa_com_csv_igual_nos_dois_bancos(ambos):
    lite, nuv = ambos
    importar_fixtures(lite, nuv)
    api = FakeAPI([BANCO, CARTAO], {
        "acc-banco": [tx("p1", "2026-09-10", 19.9, "DEBIT", "Compra fictícia no débito"),
                      tx("p2", "2026-09-11", 100.0, "CREDIT", "Transferência recebida pelo Pix - CICLANO - •••.222.222-•• - X (1)")],
        "acc-cartao": [tx("c1", "2026-09-12", 42.5, "DEBIT", "Compra fictícia no crédito")],
    })
    ra, rb = pluggy.sincronizar(lite, api), pluggy.sincronizar(nuv, api)
    assert ra == rb
    assert foto(lite) == foto(nuv)
    # sincronizar de novo não muda nada
    assert pluggy.sincronizar(nuv, api)["novas"] == 0
    assert foto(lite) == foto(nuv)


def test_casas_diferentes_no_mesmo_postgres_nao_se_misturam(pg, ambos):
    lite, nuv = ambos
    importar_fixtures(lite, nuv)
    outra = nuvem.PgConn(pg[1], str(uuid.uuid4()))
    try:
        # uma casa que não existe não pode gravar (FK); e a leitura dela é vazia
        assert outra.execute("SELECT COUNT(*) AS n FROM transactions WHERE household_id=?", (outra.household,)).fetchone()["n"] == 0
        assert nuv.execute("SELECT COUNT(*) AS n FROM transactions WHERE household_id=?", (nuv.household,)).fetchone()["n"] > 0
    finally:
        outra.close()


def test_nuvem_sem_credencial_diz_o_que_falta():
    with pytest.raises(nuvem.ErroNuvem, match="SUPABASE_DB_URL"):
        nuvem.connect({})


# ---------- migração do banco local (etapa 5) ----------

def _banco_local_rico(lite):
    """Um banco local com o que só existe nele: regra própria, nome próprio, orçamento, categoria travada."""
    service.seed_default_rules_once(lite)
    lite.execute("INSERT INTO rules (household_id, pattern, category, priority) VALUES ('default','sua academia','Assinaturas',10)")
    lite.execute("INSERT INTO own_names (household_id, name) VALUES ('default','NOME FICTICIO PROPRIO')")
    lite.commit()
    service.set_budget(lite, "Delivery", 15050)
    for arq in ("nubank_conta_fake.csv", "nubank_fatura_fake.csv"):
        service.import_csv(lite, (FIX / arq).read_bytes())
    tid = lite.execute("SELECT id FROM transactions WHERE kind='expense' ORDER BY dedupe_key LIMIT 1").fetchone()["id"]
    service.set_category(lite, tid, "Categoria Manual")  # fica travada


def test_migrar_leva_tudo_e_os_totais_batem(ambos):
    lite, nuv = ambos
    _banco_local_rico(lite)
    r = nuvem.migrar(lite, nuv)
    assert r["conferido"] and r["lancamentos_novos"] == r["lancamentos_locais"] > 0
    assert r["regras_novas"] > 0 and r["nomes"] == 1 and r["orcamentos"] == 1
    assert foto(lite) == foto(nuv)                                   # linha por linha, tipo e categoria
    assert nuvem.resumo(lite) == nuvem.resumo(nuv)
    assert nuvem.resumo(nuv)["travadas"] >= 1                        # categoria travada foi junto
    assert {(r["pattern"], r["category"]) for r in service.get_rules(lite)} == \
           {(r["pattern"], r["category"]) for r in service.get_rules(nuv)}
    assert service.get_own_names(lite) == service.get_own_names(nuv)
    assert service.seed_default_rules_once(nuv) is False             # regras padrão não entram de novo


def test_migrar_de_novo_nao_duplica_nada(ambos):
    lite, nuv = ambos
    _banco_local_rico(lite)
    nuvem.migrar(lite, nuv)
    antes = foto(nuv), len(service.get_rules(nuv))
    r = nuvem.migrar(lite, nuv)
    assert r["lancamentos_novos"] == 0 and r["regras_novas"] == 0 and r["conferido"]
    assert (foto(nuv), len(service.get_rules(nuv))) == antes


def test_simular_nao_grava_nada_na_nuvem(ambos):
    lite, nuv = ambos
    _banco_local_rico(lite)
    r = nuvem.migrar(lite, nuv, simular=True)
    assert r["simulacao"] and r["lancamentos_novos"] > 0
    assert foto(nuv) == [] and service.get_rules(nuv) == []


def test_migrar_nao_altera_o_banco_local(ambos):
    lite, nuv = ambos
    _banco_local_rico(lite)
    antes = foto(lite), len(service.get_rules(lite))
    nuvem.migrar(lite, nuv)
    assert (foto(lite), len(service.get_rules(lite))) == antes


def test_nuvem_com_dado_diferente_nao_confere_e_nada_e_gravado(ambos):
    """Se a casa da nuvem já tem outra coisa, os totais não batem: recusa em vez de misturar."""
    lite, nuv = ambos
    _banco_local_rico(lite)
    nuv.execute("INSERT INTO transactions (household_id, account, source_id, date, amount_cents, description, kind,"
                " category, dedupe_key) VALUES (?, 'nubank_conta', 'x', '2026-01-01', -999, 'OUTRA COISA', 'expense',"
                " 'Mercado', 'chave-estranha')", (nuv.household,))
    nuv.commit()
    r = nuvem.migrar(lite, nuv)
    assert r["conferido"] is False
    assert nuv.execute("SELECT COUNT(*) AS n FROM transactions WHERE household_id=?", (nuv.household,)).fetchone()["n"] == 1


def test_migrar_grava_de_verdade_visivel_para_outra_conexao(pg, ambos):
    lite, nuv = ambos
    _banco_local_rico(lite)
    nuvem.migrar(lite, nuv)
    outra = nuvem.PgConn(pg[1], nuv.household)  # sessão nova: só enxerga o que foi confirmado (commit)
    try:
        assert foto(outra) == foto(lite)
    finally:
        outra.close()
