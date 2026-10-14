"""Backup e restauração: cópia consistente e conferida, retenção só do que é nosso, restauração segura."""
import os
import sqlite3
import stat
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from financas import __main__ as cli
from financas import backup, db, service

CONTA = (Path(__file__).parent / "fixtures" / "nubank_conta_fake.csv").read_bytes()


@pytest.fixture
def banco(tmp_path):
    caminho = tmp_path / "app" / "financas.db"
    caminho.parent.mkdir()
    conn = db.connect(caminho)
    service.import_csv(conn, CONTA)
    service.set_budget(conn, "Delivery", 15000)
    conn.close()
    return caminho


def _linhas(caminho):
    conn = sqlite3.connect(str(caminho))
    try:
        return conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
    finally:
        conn.close()


def test_backup_copia_confere_e_protege_o_arquivo(banco, tmp_path):
    r = backup.fazer(banco, tmp_path / "bk")
    assert backup.PADRAO.match(r["arquivo"].name)
    assert _linhas(r["arquivo"]) == _linhas(banco) > 0
    assert r["tabelas"]["transactions"] == _linhas(banco)
    assert r["tabelas"]["budgets"] == 1
    assert stat.S_IMODE(os.stat(r["arquivo"]).st_mode) == 0o600  # só o dono lê
    assert not list((tmp_path / "bk").glob("*.parcial"))  # nada de arquivo pela metade


def test_backup_nao_altera_o_banco_de_origem(banco, tmp_path):
    antes = banco.read_bytes()
    backup.fazer(banco, tmp_path / "bk")
    assert banco.read_bytes() == antes


def test_backup_com_o_app_aberto_e_escrevendo(banco, tmp_path):
    conn = db.connect(banco)  # conexão do app, com transação pendente
    conn.execute("UPDATE transactions SET category='Teste' WHERE id=(SELECT MIN(id) FROM transactions)")
    r = backup.fazer(banco, tmp_path / "bk")  # lê só o que foi gravado: consistente
    conn.rollback()
    conn.close()
    assert backup.PADRAO.match(r["arquivo"].name)
    assert _linhas(r["arquivo"]) == _linhas(banco)


def test_dois_backups_no_mesmo_segundo_nao_se_sobrescrevem(banco, tmp_path):
    t = datetime(2026, 10, 14, 12, 0, 0)
    a = backup.fazer(banco, tmp_path / "bk", agora=t)["arquivo"]
    b = backup.fazer(banco, tmp_path / "bk", agora=t)["arquivo"]
    assert a != b and a.exists() and b.exists()


def test_retencao_guarda_as_mais_novas_e_so_apaga_o_que_e_nosso(banco, tmp_path):
    pasta = tmp_path / "bk"
    pasta.mkdir()
    (pasta / "notas.db").write_text("meu arquivo")
    (pasta / "financas-antigo-importante.db").write_text("renomeado por mim")
    base = datetime(2026, 1, 1, 8, 0, 0)
    for i in range(5):
        backup.fazer(banco, pasta, manter=None, agora=base + timedelta(days=i))
    r = backup.fazer(banco, pasta, manter=3, agora=base + timedelta(days=10))
    nossos = sorted(p.name for p in pasta.iterdir() if backup.PADRAO.match(p.name))
    assert len(nossos) == 3 and nossos[-1] == r["arquivo"].name  # a nova fica
    assert len(r["removidos"]) == 3
    assert (pasta / "notas.db").exists() and (pasta / "financas-antigo-importante.db").exists()


def test_manter_zero_ou_nada_guarda_todas(banco, tmp_path):
    base = datetime(2026, 1, 1)
    for i in range(4):
        r = backup.fazer(banco, tmp_path / "bk", manter=0, agora=base + timedelta(days=i))
    assert len([p for p in (tmp_path / "bk").iterdir() if backup.PADRAO.match(p.name)]) == 4
    assert r["removidos"] == []


def test_origem_inexistente_explica(tmp_path):
    with pytest.raises(backup.ErroBackup, match="Não achei o banco"):
        backup.fazer(tmp_path / "nao-existe.db", tmp_path / "bk")


def test_restaurar_em_lugar_vazio_nao_precisa_de_confirmacao(banco, tmp_path):
    b = backup.fazer(banco, tmp_path / "bk")["arquivo"]
    novo = tmp_path / "outro" / "financas.db"
    novo.parent.mkdir()
    r = backup.restaurar(b, novo)
    assert _linhas(novo) == _linhas(banco) and r["copia_de_seguranca"] is None


def test_restaurar_sobre_banco_existente_exige_sim_e_guarda_o_atual(banco, tmp_path):
    b = backup.fazer(banco, tmp_path / "bk")["arquivo"]
    conn = db.connect(banco)
    conn.execute("DELETE FROM transactions")  # o desastre
    conn.commit()
    conn.close()
    assert _linhas(banco) == 0

    with pytest.raises(backup.ErroBackup, match="--sim"):
        backup.restaurar(b, banco)
    assert _linhas(banco) == 0  # nada mudou sem confirmação

    r = backup.restaurar(b, banco, substituir=True)
    assert _linhas(banco) > 0
    seguranca = r["copia_de_seguranca"]
    assert seguranca.exists() and "antes-da-restauracao" in seguranca.name
    assert _linhas(seguranca) == 0  # o estado de antes da restauração ficou guardado
    assert not backup.PADRAO.match(seguranca.name)  # a retenção nunca apaga essa cópia


def test_restaurar_recusa_arquivo_corrompido_sem_tocar_no_banco(banco, tmp_path):
    ruim = tmp_path / "ruim.db"
    ruim.write_bytes(b"isto nao e um banco sqlite" * 50)
    antes = banco.read_bytes()
    with pytest.raises(backup.ErroBackup):
        backup.restaurar(ruim, banco, substituir=True)
    assert banco.read_bytes() == antes


def test_restaurar_recusa_banco_que_nao_e_do_app(tmp_path, banco):
    outro = tmp_path / "outro.db"
    c = sqlite3.connect(str(outro))
    c.execute("CREATE TABLE coisa (x)")
    c.commit()
    c.close()
    with pytest.raises(backup.ErroBackup, match="não parece ser um banco do app"):
        backup.restaurar(outro, banco, substituir=True)


def test_cli_backup_e_restaurar(banco, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(db, "DEFAULT_PATH", banco)
    pasta = tmp_path / "cli-bk"
    assert cli.main(["backup", "--dir", str(pasta), "--manter", "5"]) == 0
    saida = capsys.readouterr().out
    assert "Backup:" in saida and "integridade ok" in saida and "dados reais" in saida
    arquivo = next(pasta.iterdir())

    assert cli.main(["restaurar", str(arquivo)]) == 1  # banco existe: pede --sim
    assert "--sim" in capsys.readouterr().out
    assert cli.main(["restaurar", str(arquivo), "--sim"]) == 0
    assert cli.main(["backup", "--manter", "abc"]) == 1
    assert cli.main(["backup", "--dir"]) == 2  # argumento incompleto mostra o uso


def test_pasta_padrao_fica_ao_lado_do_banco_ou_na_variavel(banco, monkeypatch, tmp_path):
    monkeypatch.delenv("FINANCAS_BACKUP_DIR", raising=False)
    assert backup.pasta_padrao(banco) == banco.resolve().parent / "backups"
    monkeypatch.setenv("FINANCAS_BACKUP_DIR", str(tmp_path / "nuvem"))
    assert backup.pasta_padrao(banco) == tmp_path / "nuvem"
