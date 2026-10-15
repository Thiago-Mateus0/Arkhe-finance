"""Etapa 3 do ADR 0025: os relatórios em SQL (Supabase) dão o MESMO resultado que o Python local.

O banco local fictício é migrado para um Postgres de verdade e cada função SQL é chamada como a
pessoa logada (papel `authenticated`, sob RLS). A prova é a paridade com monthly_report, daily_report,
budget_status, assinaturas.listar e parcelas.projetar. Pula se não houver Docker com postgres:16.
"""
import json
import subprocess
import uuid

import pytest
from conftest import docker_ok, psql

from financas import assinaturas, db, nuvem, parcelas, service

pytestmark = pytest.mark.skipif(not docker_ok(), reason="precisa de Docker com a imagem postgres:16")

CONTA = "Data,Valor,Identificador,Descrição\n"
FATURA = "date,title,amount\n"


def _conta(*linhas):
    return CONTA + "".join(f"{d},{v},{i},{desc}\n" for d, v, i, desc in linhas)


def _fatura(*linhas):
    return FATURA + "".join(f"{d},{t},{v}\n" for d, t, v in linhas)


def _popular_local(lite):
    """Meses e casos que os relatórios precisam acertar: assinatura com fim de mês, estorno, parcelas,
    Pix no crédito parcelado, categoria sem orçamento, percentual com empate de arredondamento."""
    service.seed_default_rules_once(lite)
    for pat, cat in (("netflix", "Assinaturas"), ("spotify", "Assinaturas"), ("antiga", "Assinaturas"),
                     ("mercadofic", "Mercado"), ("farmaciafic", "Saúde"), ("padariafic", "Padaria")):
        lite.execute("INSERT INTO rules (household_id, pattern, category, priority) VALUES ('default',?,?,20)", (pat, cat))
    lite.commit()
    service.import_csv(lite, _conta(
        ("31/07/2026", "-39.90", "a1", "Compra no débito - NETFLIX"),
        ("31/08/2026", "-39.90", "a2", "Compra no débito - NETFLIX"),
        ("30/09/2026", "-44.90", "a3", "Compra no débito - NETFLIX"),
        ("05/10/2026", "39.90", "a4", "Estorno - NETFLIX"),
        ("15/08/2026", "-21.90", "a5", "Compra no débito - SPOTIFY"),
        ("15/09/2026", "-21.90", "a6", "Compra no débito - SPOTIFY"),
        ("10/03/2026", "-9.90", "a7", "Compra no débito - ANTIGA ASSINATURA"),
        ("03/09/2026", "-0.01", "a8", "Compra no débito - MERCADOFIC"),
        ("04/09/2026", "-12.34", "a9", "Compra no débito - FARMACIAFIC"),
        ("05/09/2026", "-300.00", "b1", "Compra no débito - LOJA SEM REGRA"),
        ("28/08/2026", "-150.00", "b2", "Compra no débito - LOJA SEM REGRA"),
        ("02/09/2026", "5000.00", "b3", "Transferência recebida pelo Pix - EMPRESA FIC - •••.111.111-•• - X (1)"),
        ("29/02/2028", "-1.00", "b4", "Compra no débito - MERCADOFIC"),
        ("06/09/2026", "-8.00", "b5", "Compra no débito - PADARIAFIC"),
    ))
    service.import_csv(lite, _fatura(
        ("2026-07-10", "Loja Fic - Parcela 1/3", "100,00"),
        ("2026-08-10", "Loja Fic - Parcela 2/3", "100,00"),
        ("2026-09-12", "Notebook - Parcela 3/10", "200,00"),
        ("2026-09-05", "Pix no Crédito - JOAO - 1/2", "50,00"),
        ("2026-09-06", "Compra normal fatura", "80,00"),
        ("2026-09-07", "Parcela absurda - 1/999", "10,00"),
        ("2026-09-08", "Loja Fic - Parcela 1/3", "100,00"),  # compra distinta com a mesma parcela
        ("2026-09-20", "Pagamento recebido", "-500,00"),
    ))
    service.set_budget(lite, "Mercado", 16)       # gasto de 1 centavo em 16: 6,25% -> 6,3
    service.set_budget(lite, "Saúde", 1234)       # estourou? exatamente o limite -> atenção
    service.set_budget(lite, "Delivery", 15050)
    service.set_budget(lite, "Assinaturas", 6000)
    service.set_budget(lite, "Padaria", 1000)     # gasto de 800 em 1000: exatamente 80% -> atenção


@pytest.fixture(scope="module")
def mundo(pg, tmp_path_factory):
    nome, url = pg
    import os
    os.environ["FINANCAS_OWN_NAMES"] = "Dono Exemplo Silva"
    lite = db.connect(tmp_path_factory.mktemp("rel") / "t.db")
    _popular_local(lite)
    casa, user = str(uuid.uuid4()), str(uuid.uuid4())
    psql(nome, f"insert into households (id, name) values ('{casa}', 'rel');"
               f"insert into auth.users (id) values ('{user}');"
               f"insert into members (user_id, household_id) values ('{user}', '{casa}')")
    nuv = nuvem.PgConn(url, casa)
    assert nuvem.migrar(lite, nuv)["conferido"]
    nuv.close()
    yield lite, nome, user
    lite.close()


def chamar(nome: str, user: str, consulta: str):
    r = subprocess.run(
        ["docker", "exec", "-i", nome, "psql", "-U", "postgres", "-At", "-v", "ON_ERROR_STOP=1", "-q"],
        input=f"set role authenticated; select set_config('request.jwt.claim.sub','{user}',false); select coalesce(({consulta})::text, 'null');",
        capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_meses_com_dados(mundo):
    lite, nome, user = mundo
    assert chamar(nome, user, "meses_com_dados()") == service.months_with_data(lite)
    assert len(service.months_with_data(lite)) >= 4


@pytest.mark.parametrize("mes", ["2026-03", "2026-07", "2026-08", "2026-09", "2026-10", "2028-02", "2027-01"])
def test_relatorio_mensal_igual(mundo, mes):
    lite, nome, user = mundo
    esperado = service.monthly_report(lite, mes)
    obtido = chamar(nome, user, f"relatorio_mensal('{mes}')")
    chave = lambda c: (-c["valor"], c["categoria"])  # noqa: E731 (empate: Python não define ordem)
    esperado["por_categoria"].sort(key=chave)
    assert obtido == esperado


@pytest.mark.parametrize("mes", ["2026-08", "2026-09", "2028-02", "2026-01"])
def test_relatorio_diario_igual(mundo, mes):
    lite, nome, user = mundo
    assert chamar(nome, user, f"relatorio_diario('{mes}')") == service.daily_report(lite, mes)


@pytest.mark.parametrize("mes", ["2026-08", "2026-09", "2026-10"])
def test_orcamento_igual(mundo, mes):
    lite, nome, user = mundo
    esperado = service.budget_status(lite, mes)
    obtido = chamar(nome, user, f"orcamento_status('{mes}')")
    for r in (esperado, obtido):  # empate de estado e proporção: a ordem não é definida
        assert [i["estado"] for i in r["itens"]] == sorted((i["estado"] for i in r["itens"]),
                                                          key=("estourou", "atencao", "ok").index)
        r["itens"].sort(key=lambda i: i["categoria"])
    assert obtido == esperado


def test_percentual_arredonda_meio_para_cima_nos_dois(mundo):
    lite, nome, user = mundo
    py = {i["categoria"]: i for i in service.budget_status(lite, "2026-09")["itens"]}
    sq = {i["categoria"]: i for i in chamar(nome, user, "orcamento_status('2026-09')")["itens"]}
    assert py["Mercado"]["percentual"] == sq["Mercado"]["percentual"] == 6.3  # 1 em 16 = 6,25
    assert py["Saúde"]["estado"] == sq["Saúde"]["estado"] == "atencao"      # gasto == limite
    assert py["Padaria"]["estado"] == sq["Padaria"]["estado"] == "atencao"  # exatamente 80%


@pytest.mark.parametrize("mes", ["2026-03", "2026-08", "2026-09", "2026-10", "2026-11", "2026-12"])
def test_assinaturas_igual(mundo, mes):
    lite, nome, user = mundo
    assert chamar(nome, user, f"assinaturas_do_mes('{mes}')") == assinaturas.listar(lite, mes)


def test_assinatura_do_dia_31_cai_no_ultimo_dia_do_mes_seguinte(mundo):
    lite, nome, user = mundo
    itens = {i["nome"]: i for i in chamar(nome, user, "assinaturas_do_mes('2026-09')")["itens"]}
    assert itens["COMPRA NO DÉBITO - NETFLIX"]["proxima"] == "2026-10-30"  # 30/09 + 1 mês


def test_parcelas_igual(mundo):
    lite, nome, user = mundo
    esperado = parcelas.projetar(lite)
    obtido = chamar(nome, user, "parcelas_a_vir()")
    for r in (esperado, obtido):
        for m in r["meses"]:
            m["itens"].sort(key=lambda i: (i["titulo"], i["parcela"]))
    assert obtido == esperado
    assert esperado["meses"], "o cenário precisa projetar alguma parcela"
    assert all("999" not in i["parcela"] for m in obtido["meses"] for i in m["itens"])  # texto hostil ignorado


def test_pessoa_sem_casa_recebe_relatorio_vazio(mundo):
    lite, nome, user = mundo
    sozinho = str(uuid.uuid4())
    psql(nome, f"insert into auth.users (id) values ('{sozinho}')")
    assert chamar(nome, sozinho, "meses_com_dados()") == []
    assert chamar(nome, sozinho, "relatorio_mensal('2026-09')")["gastos_total"] == 0
    assert chamar(nome, sozinho, "parcelas_a_vir()") == {"meses": [], "total": 0}


def test_duas_casas_cada_uma_ve_so_o_seu_relatorio(mundo, pg):
    lite, nome, user = mundo
    casa2, user2 = str(uuid.uuid4()), str(uuid.uuid4())
    psql(nome, f"insert into households (id, name) values ('{casa2}', 'outra');"
               f"insert into auth.users (id) values ('{user2}');"
               f"insert into members (user_id, household_id) values ('{user2}', '{casa2}');"
               f"insert into transactions (household_id, account, source_id, date, amount_cents, description, kind,"
               f" category, dedupe_key) values ('{casa2}', 'nubank_conta', '1', '2026-09-10', -777, 'OUTRA PESSOA',"
               f" 'expense', 'Lazer', 'outra-1')")
    do_outro = chamar(nome, user2, "relatorio_mensal('2026-09')")
    assert do_outro["gastos_total"] == 7.77 and [c["categoria"] for c in do_outro["por_categoria"]] == ["Lazer"]
    assert chamar(nome, user2, "meses_com_dados()") == ["2026-09"]
    meu = chamar(nome, user, "relatorio_mensal('2026-09')")
    assert "Lazer" not in [c["categoria"] for c in meu["por_categoria"]]


# ---------- escrita (migração 0003): mesma regra do Python ----------

def _rodar(nome, user, sql):
    r = subprocess.run(
        ["docker", "exec", "-i", nome, "psql", "-U", "postgres", "-At", "-v", "ON_ERROR_STOP=1", "-q"],
        input=f"set role authenticated; select set_config('request.jwt.claim.sub','{user}',false); {sql}",
        capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout.strip().splitlines()


def _estado_pg(nome, user):
    linhas = _rodar(nome, user, "select dedupe_key || '|' || category || '|' || category_locked "
                                 "from transactions order by dedupe_key")
    return [tuple(x.split("|")) for x in linhas[1:]]


def _estado_py(lite):
    return [(r["dedupe_key"], r["category"], "true" if r["category_locked"] else "false") for r in lite.execute(
        "SELECT dedupe_key, category, category_locked FROM transactions ORDER BY dedupe_key")]


@pytest.fixture
def escrita(pg, tmp_path):
    """Banco local e casa na nuvem recriados a cada teste, porque aqui os testes ESCREVEM."""
    import os
    nome, url = pg
    os.environ["FINANCAS_OWN_NAMES"] = "Dono Exemplo Silva"
    lite = db.connect(tmp_path / "w.db")
    _popular_local(lite)
    casa, user = str(uuid.uuid4()), str(uuid.uuid4())
    psql(nome, f"insert into households (id, name) values ('{casa}', 'esc');"
               f"insert into auth.users (id) values ('{user}');"
               f"insert into members (user_id, household_id) values ('{user}', '{casa}')")
    nuv = nuvem.PgConn(url, casa)
    assert nuvem.migrar(lite, nuv)["conferido"]
    nuv.close()
    yield lite, nome, user
    lite.close()


def test_categorias_igual(escrita):
    lite, nome, user = escrita
    assert chamar(nome, user, "categorias()") == service.list_categories(lite)


def test_categoria_manual_sem_lembrar_igual(escrita):
    lite, nome, user = escrita
    chave = lite.execute("SELECT dedupe_key, id FROM transactions WHERE category <> 'Sem categoria'"
                         " ORDER BY dedupe_key LIMIT 1").fetchone()
    esperado = service.set_category(lite, chave["id"], "Lazer", remember=False)
    obtido = chamar(nome, user, f"categorizar((select id from transactions where dedupe_key = '{chave['dedupe_key']}'),"
                                f" 'Lazer', false)")
    assert obtido == esperado
    assert _estado_pg(nome, user) == _estado_py(lite)


def test_categoria_manual_lembrando_cria_regra_e_recategoriza_igual(escrita):
    lite, nome, user = escrita
    chave = lite.execute("SELECT dedupe_key, id FROM transactions WHERE category = 'Sem categoria' "
                         "ORDER BY dedupe_key LIMIT 1").fetchone()
    esperado = service.set_category(lite, chave["id"], "Categoria Nova", remember=True)
    obtido = chamar(nome, user, f"categorizar((select id from transactions where dedupe_key = '{chave['dedupe_key']}'),"
                                f" 'Categoria Nova', true)")
    assert obtido == esperado and obtido["regra_criada"]
    assert _estado_pg(nome, user) == _estado_py(lite)


def test_travada_nao_e_recategorizada_pela_regra_nova(escrita):
    lite, nome, user = escrita
    chave = lite.execute("SELECT dedupe_key, id FROM transactions WHERE description LIKE '%NETFLIX%' "
                         "ORDER BY dedupe_key LIMIT 1").fetchone()
    service.set_category(lite, chave["id"], "Lazer")
    chamar(nome, user, f"categorizar((select id from transactions where dedupe_key = '{chave['dedupe_key']}'), 'Lazer')")
    lite.execute("INSERT INTO rules (household_id, pattern, category, priority) VALUES ('default','netflix','Outra',99)")
    lite.commit()
    esperado = service.recategorize(lite)
    _rodar(nome, user, "insert into rules (pattern, category, priority) values ('netflix', 'Outra', 99);")
    assert chamar(nome, user, "recategorizar()") == esperado
    assert _estado_pg(nome, user) == _estado_py(lite)
    assert dict((d, c) for d, c, _ in _estado_pg(nome, user))[chave["dedupe_key"]] == "Lazer"


def test_empate_de_prioridade_vence_o_padrao_mais_longo(escrita):
    lite, nome, user = escrita
    for conn_sql in ("netflix", "débito - netflix"):
        lite.execute("INSERT INTO rules (household_id, pattern, category, priority) VALUES ('default',?,?,50)",
                     (conn_sql, f"Cat {len(conn_sql)}"))
        _rodar(nome, user, f"insert into rules (pattern, category, priority) values ('{conn_sql}', 'Cat {len(conn_sql)}', 50);")
    lite.commit()
    assert chamar(nome, user, "recategorizar()") == service.recategorize(lite)
    assert _estado_pg(nome, user) == _estado_py(lite)


def test_nao_categoriza_lancamento_de_outra_casa(escrita):
    lite, nome, user = escrita
    outro = str(uuid.uuid4())
    psql(nome, f"insert into auth.users (id) values ('{outro}')")
    assert chamar(nome, outro, "categorizar(1, 'Hack', false)") is None
    assert chamar(nome, outro, "recategorizar()") == 0


def test_lembrar_usa_a_contraparte_quando_existe_igual(escrita):
    lite, nome, user = escrita
    chave = lite.execute("SELECT dedupe_key, id FROM transactions WHERE account='nubank_conta' AND counterparty <> '' "
                         "ORDER BY dedupe_key LIMIT 1").fetchone()
    esperado = service.set_category(lite, chave["id"], "Cat Contraparte", remember=True)
    obtido = chamar(nome, user, f"categorizar((select id from transactions where dedupe_key = '{chave['dedupe_key']}'),"
                                f" 'Cat Contraparte', true)")
    assert obtido == esperado
    assert obtido["regra_criada"] == lite.execute(
        "SELECT lower(counterparty) FROM transactions WHERE id=?", (chave["id"],)).fetchone()[0]
    assert _estado_pg(nome, user) == _estado_py(lite)
