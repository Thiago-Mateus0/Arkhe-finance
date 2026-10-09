import pytest

from financas import db, rules, service


@pytest.fixture
def conn(tmp_path):
    c = db.connect(tmp_path / "t.db")
    service.seed_default_rules(c)
    yield c
    c.close()


@pytest.mark.parametrize("title,expected", [
    ("Uber Uber *Trip Help.U", "Transporte"),
    ("99*", "Transporte"),
    ("99Food", "Delivery"),
    ("iFood *Restaurante X", "Delivery"),  # ifood (prioridade 10) vence 'restaurante'
    ("Uber *Eats", "Delivery"),  # Uber Eats não é corrida
    ("Sua Academia", "Saúde"),
    ("Recarga de celular", "Celular"),
    ("Transferência enviada pelo Pix - IMOBILIARIA SOL LTDA", "Moradia"),
    ("Barbearia do Ze", "Cuidados"),
    ("Livraria Cultura Exemplo", "Compras"),
    ("Loja Qualquer", rules.UNCATEGORIZED),
])
def test_default_rules(conn, title, expected):
    assert rules.pick_category(title, title.upper(), service.get_rules(conn)) == expected


def test_99_does_not_match_account_numbers(conn):
    desc = "Transferência enviada pelo Pix - FULANO - •••.111.111-•• - BANCO (0001) Agência: 99 Conta: 1999-9"
    assert rules.pick_category(desc, "FULANO", service.get_rules(conn)) == rules.UNCATEGORIZED


def test_seed_is_idempotent_and_delete(conn):
    assert service.seed_default_rules(conn)["adicionadas"] == 0
    rid = service.get_rules(conn)[0]["id"]
    assert service.delete_rule(conn, rid) and not service.delete_rule(conn, rid)


def test_seed_once_survives_importing_before_first_server_start(tmp_path):
    c = db.connect(tmp_path / "once.db")
    service.import_csv(c, b'date,title,amount\n2026-09-01,Uber,"10,00"\n')  # banco já tem transações
    assert service.seed_default_rules_once(c) is True
    assert service.seed_default_rules_once(c) is False
    rid = service.get_rules(c)[0]["id"]
    service.delete_rule(c, rid)
    service.seed_default_rules_once(c)  # não ressuscita o que o usuário apagou
    assert rid not in {r["id"] for r in service.get_rules(c)}
