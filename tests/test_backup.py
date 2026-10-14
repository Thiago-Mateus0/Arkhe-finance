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


# ---- backup automático antes de importar / sincronizar ----

def _auto(pasta, etiqueta="antes-de-importar"):
    return sorted(p.name for p in pasta.iterdir() if backup._padrao(etiqueta).match(p.name))


def test_automatico_cria_copia_etiquetada_ao_lado_do_banco(banco):
    r = backup.fazer_automatico(banco, "antes-de-importar")
    assert r is not None and r.parent == banco.parent / "backups"
    assert r.name.endswith("-antes-de-importar.db") and _linhas(r) == _linhas(banco)
    assert not backup.PADRAO.match(r.name)  # não se mistura com a retenção do backup manual


def test_automatico_nao_repete_dentro_do_intervalo(banco):
    assert backup.fazer_automatico(banco, "antes-de-importar") is not None
    assert backup.fazer_automatico(banco, "antes-de-importar") is None  # outro arquivo da mesma leva
    assert len(_auto(banco.parent / "backups")) == 1
    # outra etiqueta tem o próprio intervalo
    assert backup.fazer_automatico(banco, "antes-de-sincronizar") is not None


def test_automatico_guarda_so_as_ultimas_e_nao_toca_nas_manuais(banco, tmp_path):
    pasta = banco.parent / "backups"
    manual = backup.fazer(banco, pasta, agora=datetime(2026, 1, 1))["arquivo"]
    base = datetime.now() - timedelta(days=3)
    for i in range(backup.MANTER_AUTO + 4):
        backup.fazer(banco, pasta, manter=backup.MANTER_AUTO, etiqueta="antes-de-importar", agora=base + timedelta(minutes=i))
    assert len(_auto(pasta)) == backup.MANTER_AUTO
    assert manual.exists()


def test_automatico_desligado_por_variavel(banco, monkeypatch):
    monkeypatch.setenv("FINANCAS_BACKUP_AUTO", "0")
    assert backup.fazer_automatico(banco, "antes-de-importar") is None
    assert not (banco.parent / "backups").exists()


def test_automatico_sem_banco_ainda_nao_faz_nada(tmp_path):
    assert backup.fazer_automatico(tmp_path / "novo.db", "antes-de-importar") is None


def test_automatico_nunca_derruba_a_operacao(banco, monkeypatch, caplog):
    def falha(*a, **k):
        raise OSError("disco cheio")
    monkeypatch.setattr(backup, "fazer", falha)
    with caplog.at_level("WARNING"):
        assert backup.fazer_automatico(banco, "antes-de-importar") is None
    assert "não foi feito" in caplog.text and "disco cheio" not in caplog.text  # sem detalhe que vaze dado


def test_importar_pela_api_e_pela_cli_fazem_backup_antes(tmp_path, monkeypatch, capsys):
    from fastapi.testclient import TestClient
    from financas import api
    caminho = tmp_path / "app" / "financas.db"
    caminho.parent.mkdir()
    db.connect(caminho).close()
    monkeypatch.setattr(db, "DEFAULT_PATH", caminho)
    c = TestClient(api.app)
    assert c.post("/import", files={"file": ("x.csv", CONTA)}).status_code == 200
    assert len(_auto(caminho.parent / "backups")) == 1  # a API fez a cópia antes de gravar

    arquivo = tmp_path / "conta.csv"
    arquivo.write_bytes(CONTA)
    for p in (caminho.parent / "backups").iterdir():  # zera o intervalo para a CLI poder copiar de novo
        os.utime(p, (0, 0))
    assert cli.main(["import", str(arquivo)]) == 0
    assert "Backup automático antes de importar" in capsys.readouterr().out


# ---- erros de gravação viram mensagem, nunca traceback ----

@pytest.mark.skipif(os.geteuid() == 0, reason="root ignora permissão de pasta")
def test_pasta_sem_permissao_explica_o_que_conferir(banco, tmp_path):
    bloqueada = tmp_path / "disco"
    bloqueada.mkdir()
    bloqueada.chmod(0o500)  # como /media/usuario sem o disco espetado
    try:
        with pytest.raises(backup.ErroBackup, match="Sem permissão.*ls /media"):
            backup.fazer(banco, bloqueada / "financas")
    finally:
        bloqueada.chmod(0o700)


@pytest.mark.skipif(os.geteuid() == 0, reason="root ignora permissão de pasta")
def test_cli_com_destino_invalido_sai_com_erro_amigavel(banco, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(db, "DEFAULT_PATH", banco)
    bloqueada = tmp_path / "disco"
    bloqueada.mkdir()
    bloqueada.chmod(0o500)
    try:
        assert cli.main(["backup", "--dir", str(bloqueada / "x")]) == 1
    finally:
        bloqueada.chmod(0o700)
    saida = capsys.readouterr().out
    assert "ERRO — Sem permissão" in saida and "Traceback" not in saida


def test_erro_de_espaco_em_disco_tem_mensagem_propria(tmp_path):
    e = OSError(28, "No space left on device")
    assert "Sem espaço" in str(backup._erro_de_gravacao(e, tmp_path))


# ---- cópia criptografada (pasta na nuvem) ----
import shutil
import subprocess
import tempfile

SENHA = "uma-senha-bem-longa-123"
precisa_gpg = pytest.mark.skipif(shutil.which("gpg") is None, reason="gpg não instalado")


@pytest.fixture
def gnupg_isolado(monkeypatch):
    """GNUPGHOME curto e descartável: o teste não toca no chaveiro de ninguém (e o socket cabe no limite)."""
    casa = tempfile.mkdtemp(prefix="gh-", dir="/tmp")
    os.chmod(casa, 0o700)
    monkeypatch.setenv("GNUPGHOME", casa)
    yield casa
    if shutil.which("gpgconf"):
        subprocess.run(["gpgconf", "--homedir", casa, "--kill", "all"], capture_output=True)
    shutil.rmtree(casa, ignore_errors=True)


@precisa_gpg
def test_criptografado_so_deixa_o_gpg_na_pasta_e_abre_com_a_senha(banco, tmp_path, gnupg_isolado):
    nuvem = tmp_path / "nuvem"
    r = backup.fazer_criptografado(banco, nuvem, SENHA)
    assert r["arquivo"].name.endswith(".db.gpg") and backup.PADRAO_GPG.match(r["arquivo"].name)
    assert [p.name for p in nuvem.iterdir()] == [r["arquivo"].name]  # nenhuma cópia sem senha ficou lá
    assert stat.S_IMODE(os.stat(r["arquivo"]).st_mode) == 0o600
    assert r["tabelas"]["transactions"] == _linhas(banco)
    assert b"SQLite format" not in r["arquivo"].read_bytes()  # não é o banco em claro

    aberto = tmp_path / "aberto.db"
    backup.descriptografar(r["arquivo"], aberto, SENHA)
    assert _linhas(aberto) == _linhas(banco)


@precisa_gpg
def test_senha_errada_nao_abre_e_nao_deixa_lixo(banco, tmp_path, gnupg_isolado):
    r = backup.fazer_criptografado(banco, tmp_path / "nuvem", SENHA)
    saida = tmp_path / "x.db"
    with pytest.raises(backup.ErroBackup, match="Senha incorreta"):
        backup.descriptografar(r["arquivo"], saida, "outra-senha-qualquer")
    assert not saida.exists()


@precisa_gpg
def test_arquivo_adulterado_e_recusado(banco, tmp_path, gnupg_isolado):
    r = backup.fazer_criptografado(banco, tmp_path / "nuvem", SENHA)
    dados = bytearray(r["arquivo"].read_bytes())
    dados[len(dados) // 2] ^= 0xFF  # um bit trocado no meio
    r["arquivo"].write_bytes(bytes(dados))
    with pytest.raises(backup.ErroBackup, match="Senha incorreta, ou o arquivo está corrompido"):
        backup.descriptografar(r["arquivo"], tmp_path / "x.db", SENHA)


def test_senha_curta_e_recusada_antes_de_qualquer_coisa(banco, tmp_path):
    with pytest.raises(backup.ErroBackup, match="pelo menos"):
        backup.fazer_criptografado(banco, tmp_path / "nuvem", "curta")
    assert not (tmp_path / "nuvem").exists() or not list((tmp_path / "nuvem").iterdir())


@precisa_gpg
def test_retencao_do_criptografado_so_mexe_nos_gpg(banco, tmp_path, gnupg_isolado):
    nuvem = tmp_path / "nuvem"
    nuvem.mkdir()
    (nuvem / "foto.jpg").write_text("minha")
    base = datetime(2026, 1, 1)
    for i in range(4):
        backup.fazer_criptografado(banco, nuvem, SENHA, manter=2, agora=base + timedelta(days=i))
    gpgs = sorted(p.name for p in nuvem.iterdir() if backup.PADRAO_GPG.match(p.name))
    assert len(gpgs) == 2 and (nuvem / "foto.jpg").exists()


@precisa_gpg
def test_restaurar_do_criptografado_com_sim_guarda_o_atual(banco, tmp_path, gnupg_isolado):
    r = backup.fazer_criptografado(banco, tmp_path / "nuvem", SENHA)
    conn = db.connect(banco)
    conn.execute("DELETE FROM transactions")
    conn.commit()
    conn.close()
    with pytest.raises(backup.ErroBackup, match="--sim"):
        backup.restaurar_criptografado(r["arquivo"], banco, SENHA)
    out = backup.restaurar_criptografado(r["arquivo"], banco, SENHA, substituir=True)
    assert _linhas(banco) > 0 and out["copia_de_seguranca"].exists()


@precisa_gpg
def test_cli_criptografar_e_restaurar_com_senha_em_arquivo(banco, tmp_path, monkeypatch, capsys, gnupg_isolado):
    monkeypatch.setattr(db, "DEFAULT_PATH", banco)
    senha = tmp_path / "senha.txt"
    senha.write_text(SENHA + "\n")
    senha.chmod(0o644)  # legível por outros: tem que recusar
    monkeypatch.setenv("FINANCAS_BACKUP_SENHA_ARQUIVO", str(senha))
    assert cli.main(["backup", "--criptografar", "--dir", str(tmp_path / "n")]) == 1
    assert "legível por outras pessoas" in capsys.readouterr().out

    senha.chmod(0o600)
    assert cli.main(["backup", "--criptografar", "--dir", str(tmp_path / "n")]) == 0
    saida = capsys.readouterr().out
    assert "Backup criptografado:" in saida and "Guarde a senha" in saida and SENHA not in saida
    arquivo = next((tmp_path / "n").iterdir())
    assert cli.main(["restaurar", str(arquivo), "--sim"]) == 0


def test_cli_criptografar_sem_terminal_nem_arquivo_explica(banco, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(db, "DEFAULT_PATH", banco)
    monkeypatch.delenv("FINANCAS_BACKUP_SENHA_ARQUIVO", raising=False)
    monkeypatch.setattr("sys.stdin", open(os.devnull))  # não é terminal
    assert cli.main(["backup", "--criptografar", "--dir", str(tmp_path / "n")]) == 1
    assert "FINANCAS_BACKUP_SENHA_ARQUIVO" in capsys.readouterr().out
